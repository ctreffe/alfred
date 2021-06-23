import random
import json
import time
from dataclasses import dataclass, asdict, field
from typing import List, Iterator, Tuple
from pathlib import Path
from warnings import warn
from itertools import product
from collections import Counter

from pymongo.collection import ReturnDocument

from .exceptions import ConditionInconsistency, AllConditionsFull
from .data_manager import DataManager, saving_method
from .compatibility.condition import ListRandomizer as OldListRandomizer


@dataclass
class SessionGroup:

    sessions: List[str]

    def query(self, expid) -> dict:
        d = {}
        d["exp_id"] = expid
        d["exp_session_id"] = {"$in": self.sessions}
        d["type"] = DataManager.EXP_DATA

        return d

    def _load_local(self, exp) -> Iterator[dict]:
        dt = DataManager.EXP_DATA
        directory = exp.config.get("local_saving_agent", "path")
        directory = exp.subpath(directory)
        cursor = DataManager.iterate_local_data(dt, directory)
        for data in cursor:
            if data["exp_session_id"] in self.sessions:
                yield data
    
    def _get_fields(self, exp, fields: List[str]) -> list:
        method = saving_method(exp)
        if method == "mongo":
            data = self._get_fields_mongo(exp, fields)
        elif method == "local":
            data = self._get_fields_local(exp, fields)
        
        return data
    
    def _get_fields_mongo(self, exp, fields: List[str]) -> Iterator:
        q = self.query(exp.exp_id)
        projection_fields = {field: 1 for field in fields} 
        projection = {**projection_fields, **{"_id": 0}}
        cursor = exp.db_main.find(q, projection=projection)
        return cursor 
    
    def _get_fields_local(self, exp, fields: List[str]) -> Iterator:
        cursor = self._load_local(exp)
        for sessiondata in cursor:
            yield {key: value for key, value in sessiondata.items() if key in fields}

    def finished(self, exp, data: List[dict] = None) -> bool:
        if not data:
            data = self._get_fields(exp, ["exp_finished"])
        finished = [session["exp_finished"] for session in data]
        return all(finished)
    
    def aborted(self, exp, data: List[dict] = None) -> bool:
        if not data:
            data = self._get_fields(exp, ["exp_aborted"])
        aborted = [session["exp_aborted"] for session in data]
        return any(aborted)

    def expired(self, exp, data: List[dict] = None) -> bool:
        if not data:
            data = self._get_fields(exp, ["exp_start_time"])
        now = time.time()
        start_time = [session["exp_start_time"] for session in data]
        
        expired = []

        for t in start_time:
            if t is None:
                expired.append(False)
                continue
            
            passed_time = now - t
            expired.append(passed_time > exp.session_timeout)

        return any(expired)
        
    def started(self, exp, data: List[dict] = None) -> bool:
        if not data:
            data = self._get_fields(exp, ["exp_start_time"])
        start_time = [session["exp_start_time"] for session in data]
        return not any([t is None for t in start_time])
    
    def most_recent_save(self, exp, data: List[dict] = None) -> float:
        if not data:
            data = self._get_fields(exp, ["exp_save_time"])
        
        save_time = [session["exp_save_time"] for session in data]
        most_recent = max(save_time)
        return most_recent
        
    def active(self, exp) -> bool:
        fields = ["exp_start_time", "exp_finished", "exp_aborted", "exp_save_time"]
        data = list(self._get_fields(exp, fields))
        
        if not self.started(exp, data):
            # use tolerance of 1 min here to give experiments time to start
            if time.time() - self.most_recent_save(exp, data) > 60:
                return False
            else:
                return True

        finished = self.finished(exp, data)
        aborted = self.aborted(exp, data)
        expired = self.expired(exp, data)

        return not finished and not aborted and not expired


@dataclass
class Slot:

    condition: str
    session_groups: List[SessionGroup] = field(default_factory=list)

    def __post_init__(self):
        self.session_groups = [
            SessionGroup(**session_data) for session_data in self.session_groups
        ]

    def finished(self, exp) -> bool:
        finished = [s.finished(exp) for s in self.session_groups]
        return any(finished)

    def pending(self, exp) -> bool:
        active = [s.active(exp) for s in self.session_groups]
        return any(active)

    def open(self, exp) -> bool:
        return not self.finished(exp) and not self.pending(exp)

    def __contains__(self, session_ids: List[str]) -> bool:
        group_contains_session = (session_ids == group.sessions for group in self.session_groups)
        return any(group_contains_session)


@dataclass
class SlotManager:
    slots: List[dict]

    def __post_init__(self):
        self.slots = [Slot(**slot_data) for slot_data in self.slots]

    def open_slots(self, exp) -> Iterator[Slot]:
        return (slot for slot in self.slots if slot.open(exp))

    def pending_slots(self, exp) -> Iterator[Slot]:
        return (slot for slot in self.slots if slot.pending(exp))
    
    def find_slot(self, session_ids: List[str]) -> Slot:
        for slot in self.slots:
            if session_ids in slot:
                return slot


@dataclass
class RandomizerData:
    randomizer_id: str
    exp_id: str
    exp_version: str
    random_seed: float 
    mode: str
    slots: List[dict] = field(default_factory=list)
    busy: bool = False
    type: str = "condition_data"


class RandomizerIO:
    def __init__(self, randomizer):
        self.rand = randomizer
        self.exp = randomizer.exp
        self.db = self.exp.db_misc

        if saving_method(self.exp) == "local":
            self.path.parent.mkdir(exist_ok=True)

    @property
    def query(self) -> dict:
        d = {}
        d["exp_id"] = self.exp.exp_id
        d["exp_version"] = self.rand.exp_version
        d["type"] = "condition_data"
        d["randomizer_id"] = self.rand.randomizer_id
        return d
    
    @property
    def path(self) -> Path:
        name = f"randomization_{self.rand.randomizer_id}{self.rand.exp_version}.json"
        directory = self.exp.config.get("exp_condition", "path")
        directory = self.exp.subpath(directory)
        return  directory / name
    
    def load(self) -> RandomizerData:
        insert = RandomizerData(
            randomizer_id=self.rand.randomizer_id,
            exp_id=self.exp.exp_id,
            exp_version=self.rand.exp_version,
            random_seed=self.rand.random_seed,
            mode=self.rand.mode
        )

        method = saving_method(self.exp)
        if method == "mongo":
            return self.load_mongo(insert)
        elif method == "local":
            return self.load_local(insert)
    
    def load_mongo(self, insert: RandomizerData) -> RandomizerData:
        q = self.query
        data = self.db.find_one_and_update(
            filter=q, 
            update={"$setOnInsert": asdict(insert)}, 
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        data.pop("_id", None)
        return RandomizerData(**data)
    
    def load_local(self, insert: RandomizerData) -> RandomizerData:
        if not self.path.exists():
            self.save_local(asdict(insert))
        
        else:
            with open(self.path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            
            return RandomizerData(**data)

    def load_markbusy(self) -> RandomizerData:
        method = saving_method(self.exp)
        if method == "mongo":
            return self.load_markbusy_mongo()
        elif method == "local":
            return self.load_markbusy_local()

    def load_markbusy_mongo(self) -> RandomizerData:
        q = self.query
        q["busy"] = False
        
        update = {"$set": {"busy": True}}
        rd = ReturnDocument.AFTER

        data = self.db.find_one_and_update(filter=q, update=update, return_document=rd)
        
        if data is None:
            return None

        data.pop("_id", None)

        return RandomizerData(**data)
    
    def load_markbusy_local(self) -> RandomizerData:
        if not self.path.exists():
            data = asdict(self.rand.data)


        with open(self.path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        
        if data["busy"]:
            return None
        
        data["busy"] = True
        self.save_local(data)
        return RandomizerData(**data)
        
    def save(self, data: RandomizerData):
        data = asdict(data)

        method = saving_method(self.exp)
        if method == "mongo":
            self.save_mongo(data)
        elif method == "local":
            self.save_local(data)
    
    def save_local(self, data: dict):
        with open(self.path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=4)

    def save_mongo(self, data: dict):
        q = self.query
        q["busy"] = True
        self.db.find_one_and_update(filter=q, update={"$set": data})

    def release(self):
        method = saving_method(self.exp)
        if method == "mongo":
            self.release_mongo()
        elif method == "local":
            self.release_local()
    
    def release_mongo(self):
        q = self.query
        q["busy"] = True
        u = {"$set": {"busy": False}}
        self.db.find_one_and_update(filter=q, update=u)
    
    def release_local(self):
        with open(self.path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        
        data["busy"] = False
        self.save_local(data)

    def __enter__(self):
        data = self.load_markbusy()
        start = time.time()
        while not data:
            time.sleep(1)
            data = self.load_markbusy()
            if time.time() - start > 10:
                raise IOError("Could not load randomizer data.")
        return data

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type:
            self.release()
            self.exp.abort(reason="randomizer_error")
            self.exp.log.error(
                (
                    f"There was an error in a locked Randomizer operation: '{exc_value}' "
                    "I aborted the experiment and released the lock."
                )
            )
        
        else:
            self.release()


class ListRandomizer:
    """
    Offers efficient list randomization.

    Args:
        *conditions: A variable number of tuples, defining the experiment
            conditions. The tuples have the form ``("str", int)``, where
            *str* is a string giving the condition's name, and *int* is
            the target number of observations for this condition.
        
        exp (alfred3.ExperimentSession): The alfred3 experiment session.

        session_ids (list): A list of experiment session ids that should
            be treated as a group, i.e. share a single condition slot.
            That means, they will be allocated to the same condition and,
            as a group, take up only one space in the count of sessions
            that the randomizer keeps. Most useful for group experiments.
            Defaults to ``[exp.session_id]``, i.e. a list of length 1 with
            the session id of the current experiment instance as its only
            element.
        
        respect_version (bool): If True, randomization will start anew
            for each experiment version. This is especially important,
            if you make changes to the condition setup of an ongoing
            experiment. This might cause the randomizer to fail, causing
            :class:`.ConditionInconsistency` errors.
            Setting *respect_version* to True can fix such issues. 
            Defaults to True.
        
        mode (str): Can be one of 'strict' or 'inclusive'. 
        
            If 'strict', the randomizer will only assign a condition 
            slot, if there are no active sessions for that slot. It will
            not assign a condition slot, if a session in that slot
            is finished, or if there is an ongoing session in that slot
            that has not yet timed out. You will end up with exactly
            as many participants in each condition, as specified in the
            target size. 
            
            If 'inclusive', the randomizer will assign a condition slot,
            if there is no finished session in that slot. That means,
            there might be two ongoing sessions for the same slot, and
            both might end up to finish.

            While 'strict' mode might lead to participants being turned
            away before the experiment is really complete, 'inclusive'
            mode might lead to more data being collected than necessary.

            Defaults to 'strict'.
        
        randomizer_id (str): An identifier for the randomizer. If you
            give this a custom value, you can use multiple randomizers
            in the same experiment. Defaults to 'randomizer'.
        
        random_seed: The random seed used for reproducible pseudo-random
            behavior. This seed will be used for shuffling the condition
            list. Defaults to the current system time. Valid seeds are
            all values that are accepted by :func:`random.seed`
        
        abort_page (alfred3.page.Page): You can reference a custom
                page to be displayed to new participants, if the 
                experiment is full.
        
        id (str): A unique identifier for the condition slot assigned
            by this instance of *ListRandomizer*. If *None*, the current
            :attr:`.ExperimentSession.session_id` will be used. 
            This argument enables you to assign, for example, a group
            id that connects several sessions, to the randomizer.
            Defaults to None. *Deprecated* in version 2.1.7: Please use
            parameter *session_ids* instead. If you use the 'id' 
            parameter, the ListRandomizer will start in compatibility
            mode.

    The ListRandomizer is used by initializing it (either directly
    or via the convenience method :meth:`.balanced`) and using the
    method :meth:`.get_condition` to receive a condition. By default,
    the ListRandomizer will automatically abort sessions when 
    *get_condition* is called and display
    an information page for participants, if the experiment is full. This
    behavior can be customized (see :meth:`.get_condition`).

    .. warning:: Be mindful of the argument *respect_version*! With the
        default setting (True), randomization starts from scratch for
        every experiment version. If you set it to False, you will
        run into an error, if you change anything about the conditions.
    
    .. versionchanged:: 2.1.7
       New parameters *session_ids* and *randomizer_id*, new alternative 
       constructor :meth:`.factors`. Deprecated the parameter *id*.
    
    Notes: 

        **List Randomization**

        In naive randomization, you might end up with a very unbalanced
        design. For example, if you recruit 300 participants and randomize
        them into two conditions, you might end up with 100 participants in
        the first and 200 in the second condition. If you aim for a balanced
        design with 150 participants in either condition, you might have 
        to recruit more than 300 participants and throw away lots of observations
        in the condition that turned out to be larger. 

        List randomization solves this problem, which is why it is commonly
        used in offline studies. Let's take an easy example. We might have
        two conditions, a and b, each of which should be completed by three participants.
        The order in which participants are assigned to a condition should be
        random. To achieve this, we create a list that contains a condition 
        slot for each participant::

            ["a", "a", "a", "b", "b", "b"]

        We then shuffle this list, which might lead to something like the
        following::

            ["b", "a", "a", "b", "a", "b"]
        
        Then, the conditions are assigned to participants based on the
        shuffled list in the order that they start the experiment.

        **Using the ListRandomizer offline**

        You can use the ListRandomizer offline, i.e. without using a
        mongoDB for data saving. In this case, you must keep in mind,
        that the shuffled list will only be shared on one machine. 
        Offline, randomization cannot be synchronized across multiple
        machines.
    
    Examples:

        A minimal experiment with two conditions. If the experiment
        is full, the experiment will immediately abort new sessions
        and display an abort page to new participants::

            import alfred3 as al
            exp = al.Experiment()

            @exp.setup
            def setup(exp):
                randomizer = al.ListRandomizer(("cond1", 10), ("cond2", 10), exp=exp)
                exp.condition = randomizer.get_condition()
            
            @exp.member
            class DemoPage(al.Page):

                def on_exp_access(self):

                    if self.exp.condition == "cond1":
                        lab = "label in condition 1"
                    
                    elif self.exp.condition == "cond2":
                        lab = "label in condition 2"
            
                    self += al.TextEntry(leftlab=lab, name="t1")
        
        You can use the alternative constructor :meth:`.balanced` for
        simplified initialization, if you use the same sample size for 
        all experiment conditions::

            import alfred3 as al
            exp = al.Experiment()

            @exp.setup
            def setup(exp):
                randomizer = al.ListRandomizer.balanced("cond1", "cond2", n=10, exp=exp)
                exp.condition = randomizer.get_condition()
            
            @exp.member
            class DemoPage(al.Page):

                def on_exp_access(self):

                    if self.exp.condition == "cond1":
                        lab = "label in condition 1"
                    
                    elif self.exp.condition == "cond2":
                        lab = "label in condition 2"
            
                    self += al.TextEntry(leftlab=lab, name="t1")

    """

    @staticmethod
    def _use_comptability(**kwargs) -> bool:
        """
        Checks whether there is existing randomizer data. In this case,
        the randomizer will operate in compatibility mode.
        """
        exp = kwargs["exp"]
        respect_version = kwargs.get("respect_version", True)
        
        method = saving_method(exp)
        version = exp.version if respect_version else ""
        
        if method == "mongo":
            query = {"exp_id": exp.exp_id, "exp_version": version, "type": "condition_data"}
            data = exp.db_misc.find_one(query)
        elif method == "local":
            directory = exp.config.get("exp_condition", "path")
            path = exp.subpath(directory) / f"randomization{version}.json"
            
            if not path.exists():
                return False
            
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        
        if data:
            old = data["slots"][0].get("sessions", False)
            return old is not False
        else:
            return False


    def __new__(cls, *args, **kwargs):
        if kwargs.get("id", False) or cls._use_comptability(**kwargs):
            return OldListRandomizer(*args, **kwargs)
        else:
            return super().__new__(cls)

    def __init__(
        self,
        *conditions: Tuple[str, int],
        exp,
        session_ids: List[str] = None,
        respect_version: bool = True,
        mode: str = "strict",
        random_seed=None,
        abort_page=None,
        randomizer_id: str = "randomizer",
        id: str = None,
    ):

        self.exp = exp
        self.respect_version = respect_version
        self.exp_version = self.exp.version if respect_version else ""
        self.mode = mode
        self.random_seed = random_seed if random_seed is not None else time.time()
        self.conditions = conditions
        self.abort_page = abort_page
        self.randomizer_id = randomizer_id
        self.session_ids = session_ids if session_ids is not None else [exp.session_id]
        if isinstance(self.session_ids, str):
            raise ValueError("Argument 'session_ids' must be a list of strings, not a single string.")
        
        self.io = RandomizerIO(self)
        self._initialize_slots()
        
    @classmethod
    def balanced(cls, *conditions, n: int, **kwargs):
        """
        Alternative constructor, creates a ListRandomizer where all 
        conditions have the same size.

        Args:
            *conditions (str): A variable number of strings, giving the
                condition names.
            n (int): The number of participants **per condition**.
            **kwargs: Keyword arguments, passed on the normal intialization
                of :class:`.ListRandomizer`.
        
        Notes:
            This alternative constructor offers a more concise syntax
            for simple balanced setups. All conditions receive the same
            sample size.
        
        Examples:
            ::

                import alfred3 as al
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    randomizer = al.ListRandomizer.balanced("cond1", "cond2", n=10, exp=exp)
                    exp.condition = randomizer.get_condition()
                
                @exp.member
                class DemoPage(al.Page):

                    def on_exp_access(self):

                        if self.exp.condition == "cond1":
                            lab = "label in condition 1"
                        
                        elif self.exp.condition == "cond2":
                            lab = "label in condition 2"
                
                        self += al.TextEntry(leftlab=lab, name="t1")

        """
        if kwargs.get("id", False) or cls._use_comptability(**kwargs):
            return OldListRandomizer.balanced(*conditions, n=n, **kwargs)

        conditions = [(c, n) for c in conditions]
        return cls(*conditions, **kwargs)
    
    @classmethod
    def factors(cls, *factors, n, **kwargs):
        """
        Alternative constructor, creates a *balanced* ListRandomizer
        where the conditions are combinations of several factors.

        Args:
            *factors: A variable number of *iterables*, giving the 
                factors to be used in forming the conditions.

            n (int): The number of participants **per condition**.

            **kwargs: Keyword arguments, passed on the normal intialization
                of :class:`.ListRandomizer`.

        In elaborated counter-balanced designs, you may end up with a lot
        of different conditions when combining all different possible
        values of your factos. Typing them by hand is tedious. To make
        your life easier, you can now simply input the factors themselves,
        and alfred3 will construct the combinations for you. The values
        of the individual factors will be separated by dots.

        .. note:: Note that, in Python, strings are iterables. That means,
            that a call like ``ListRandomizer.factors("ab", "cd", ...)``
            will combine the *individual characters* within the strings.
            The resulting conditions in this case will be 
            ``["a.c", "a.d", "b.c", "b.d"]``. If you want to include a
            single string on its own, put in in a list:
            ``ListRandomizer.factors("ab", ["cd"], ...)`` will create
            two conditions: ``["a.cd", "b.cd"]``.
        
        .. versionadded:: 2.1.7
        
        Examples:

            Use the :meth:`.factors` constructor to create conditions::
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    randomizer = l.ListRandomizer.factors(
                        ["a1", "a2"], ["b1", "b2"], 
                        n=20, 
                        exp=exp
                    )

                    exp.condition = randomizer.get_condition()

                    print(randomizer.conditions)
                    # (('a1.b1', 20), ('a1.b2', 20), ('a2.b1', 20), ('a2.b2', 20))
            
            Use the :meth:`.factors` constructor to create conditions,
            then do something for all sessions that contain a specific
            factor value::
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    randomizer = al.ListRandomizer.factors(
                        ["a1", "a2"], ["b1", "b2"], 
                        n=20, 
                        exp=exp
                    )

                    exp.condition = randomizer.get_condition()

                    if "a1" in exp.condition:
                        # do something only for conditions with a1
                        pass

        """
        conditions = product(*factors)
        conditions = [".".join(c) for c in conditions]
        conditions = [(c, n) for c in conditions]

        return cls(*conditions, **kwargs)

    @property
    def full(self) -> bool:
        """
        bool: *True*, if all condition slots are full. In 'strict' mode,
        unfinished but active experiment sessions are counted. In
        'inclusive' mode, only sessions that are fully finished are 
        counted.
        """
        with self.io as data:
            return self._is_full(data)

    def abort_if_full(self, raise_exception: bool = False, data: RandomizerData = None):
        """
        Aborts the experiment, if all slots of the randomizer are filled.

        Args:
            raise_exception (bool): If True, the function raises
                the :class:`.AllConditionsFull` exception instead of 
                automatically aborting the experiment if all conditions 
                are full. This allows you to catch the exception and 
                customize the experiment's behavior in this case.
        
        .. versionadded:: 2.1.7
        """
        if data is None:
            full = self.full
        else:
            full = self._is_full(data)
        
        if not full:
            return

        if raise_exception:
            raise AllConditionsFull
        else:
            self._abort()

    def get_condition(self, raise_exception: bool = False) -> str:
        """
        Returns a condition.

        Args:
            raise_exception (bool): If True, the function raises
                the :class:`.AllConditionsFull` exception instead of 
                automatically aborting the experiment if all conditions 
                are full. This allows you to catch the exception and 
                customize the experiment's behavior in this case.
        
        If all conditions are full, the experiment will be aborted. New
        participants will be redirected to an abort page. The text
        displayed on this page can be customized with the arguments
        'full_page_title' and 'full_page_text'.

        Returns:
            str: A condition name, taken from the randomized conditions
            list.
        
        Raises:
            AllConditionsFull: If raise_exception is True and
            all conditions are full.
        
        Examples:

            An example using the default behavior::

                import alfred3 as al
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    randomizer = al.ListRandomizer(("cond1", 10), ("cond2", 10), exp=exp)
                    exp.condition = randomizer.get_condition()
                
                @exp.member
                class DemoPage(al.Page):

                    def on_exp_access(self):

                        if self.exp.condition == "cond1":
                            lab = "label in condition 1"
                        
                        elif self.exp.condition == "cond2":
                            lab = "label in condition 2"
                
                        self += al.TextEntry(leftlab=lab, name="t1")

            This is an example of customizing the 'full' behavior. 
            It basically re-implements the default behavior, but showcases how
            you can customize behavior by catching the "AllConditionsFull"
            exception::

                import alfred3 as al
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    randomizer = al.ListRandomizer(("cond1", 10), ("cond2", 10), exp=exp)
                    try:
                        exp.condition = randomizer.get_condition(raise_exception=True)
                    except al.AllConditionsFull:
                        full_page = al.Page(title="Experiment closed.", name="fullpage")
                        full_page += al.Text("Sorry, the experiment currently does not accept any further participants")
                        exp.abort(reason="full", page=full_page)
                
                
                @exp.member
                class DemoPage(al.Page):

                    def on_exp_access(self):

                        if self.exp.condition == "cond1":
                            lab = "label in condition 1"
                        
                        elif self.exp.condition == "cond2":
                            lab = "label in condition 2"
                
                        self += al.TextEntry(leftlab=lab, name="t1")
            
            The following is an example of a custom page displayed when
            the experiment is full. Note that it, basically implements
            the same behavior as the previous example, it is just a little
            more convenient::

                import alfred3 as al
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    full_page = al.Page(title="Experiment closed.", name="fullpage")
                    full_page += al.Text("Sorry, the experiment currently does not accept any further participants.")
                    
                    randomizer = al.ListRandomizer(("cond1", 10), ("cond2", 10), exp=exp, abort_page=full_page)
                
                    exp.condition = randomizer.get_condition()
                
                
                @exp.member
                class DemoPage(al.Page):

                    def on_exp_access(self):

                        if self.exp.condition == "cond1":
                            lab = "label in condition 1"
                        
                        elif self.exp.condition == "cond2":
                            lab = "label in condition 2"
                
                        self += al.TextEntry(leftlab=lab, name="t1")


        """
        with self.io as data:
            
            self._validate(data)
            slot_manager = SlotManager(data.slots)
            slot = slot_manager.find_slot(self.session_ids)
            if slot:
                return slot.condition
            
            if self._is_full(data):
                self.abort_if_full(raise_exception=raise_exception, data=data)
                return "__ABORTED__"
            
            slot = next(slot_manager.open_slots(self.exp), None)

            if slot is None and self.mode == "inclusive":
                slot = next(slot_manager.pending_slots(self.exp), None)
            
            if slot is None:
                msg = "No slot found, even though the randomizer does not appear to be full."
                raise ConditionInconsistency(msg)
            
            group = SessionGroup(self.session_ids)
            slot.session_groups.append(group)
            
            data.slots = asdict(slot_manager)["slots"]
            self.io.save(data)
            return slot.condition
    
    def find_slot(self, session_ids: List[str]) -> Slot:
        data = self.io.load()
        slot_manager = SlotManager(data.slots)
        slot = slot_manager.find_slot(session_ids)
        return slot

    
    def _initialize_slots(self):
        self.io.load()

        with self.io as data:
            if not data.slots:
                data.slots = self._randomize_slots()
                self.io.save(data)
    
    def _generate_slots(self) -> List[dict]:
        slots = []
        for c in self.conditions:
            slots += [{"condition": c[0]}] * c[1]
        return slots

    def _randomize_slots(self) -> List[dict]:
        slots = self._generate_slots()
        random.seed(self.random_seed)
        random.shuffle(slots)
        return slots
    
    def _abort(self):
        full_page_title = "Experiment closed"
        full_page_text = "Sorry, the experiment currently does not accept any further participants."
        self.exp.abort(reason="full", title=full_page_title, msg=full_page_text, icon="user-check", page=self.abort_page)

    def _validate(self, data: RandomizerData):
        if self.respect_version:
            if not self.exp.version == data.exp_version:
                raise ConditionInconsistency("Experiment version and randomizer version do not match.")

        data_conditions = [slot["condition"] for slot in data.slots]
        counted = Counter(data_conditions)

        instance = dict(self.conditions)

        msg = "Condition data is inconsistent with randomizer specification. "
        what_to_do = "You can set 'respect_version' to True and increase the experiment version."
        if not counted == instance:
            raise ConditionInconsistency(msg + what_to_do)
    
    def _is_full(self, data: RandomizerData) -> bool:
        slot_manager = SlotManager(data.slots)
        open_slots = slot_manager.open_slots(self.exp)
        pending_slots = slot_manager.pending_slots(self.exp)
        
        if self.mode == "strict":
            full = not any(open_slots) 
        elif self.mode == "inclusive":
            full = not any(open_slots) and not any(pending_slots)
        
        return full


def random_condition(*conditions) -> str:
    """
    Returns a random condition based on the supplied arguments with 
    equal probability of all conditions.

    Args:
        *conditions: A variable number of condition identifiers
    
    Returns:
        str: One of the input arguments, chosen at random.
    
    See Also:
        This is a naive way of randomizing, suitable mostly for
        quick prototypes with equal probability of all conditions. 
        A more powerful approach is offered by :class:`.ListRandomizer`.
    
    Examples:
        
            >>> import alfred3 as al
            >>> al.random_condition("A", "B")
            A

        The example returns either "A" or "B".
    """
    return str(random.choice(conditions))