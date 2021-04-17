"""
Provides functionality for assigning participants to experiment conditions.
"""

from dataclasses import dataclass, asdict
from typing import Tuple, List, Iterator
from pathlib import Path
from uuid import uuid4
import time
import random
import json


class AllConditionsFull(Exception):
    pass


class ConditionInconsistency(AssertionError):
    pass


@dataclass
class _Session:
    id: str
    timestamp: float = time.time()


@dataclass
class _Slot:

    condition: str
    timeout: int
    sessions: list
    finished: bool = False

    def __init__(self, *sessions, condition: str, timeout: int, finished: bool = False):
        self.condition = condition
        self.timeout = timeout
        self.sessions = [_Session(**s) for s in sessions]
        self.finished = finished

    @property
    def status(self):

        if not self.finished and not self.active_sessions:
            return "free"

        elif not self.finished:
            return "pending"

        else:
            return "finished"

    @property
    def active_sessions(self):
        if self.timeout:
            now = time.time()
            return [s for s in self.sessions if (now - s.timestamp) < self.timeout]
        else:
            return self.sessions

    @property
    def ids(self):
        return [session.id for session in self.sessions]

    def session(self, id) -> _Session:
        return [s for s in self.sessions if s.id == id]


@dataclass
class _SlotList:
    slots: list

    def __init__(self, *slots):
        self.slots = [_Slot(*s.pop("sessions", []), **s) for s in slots]

    def open_slots(self) -> Iterator[_Slot]:
        return (slot for slot in self.slots if slot.status == "free")
    
    def pending_slots(self) -> Iterator[_Slot]:
        return (slot for slot in self.slots if slot.status == "pending")

    def id_assigned_to(self, id) -> _Slot:
        for slot in self.slots:
            if id in slot.ids:
                return slot
        return None


class _ConditionIO:
    """
    Handles data in- and output for condition administration.
    """
    def __init__(self, exp, respect_version: bool):
        self.exp = exp
        self.version = self.exp.version if respect_version else ""
        self.path = None
        self.query = None
        self.method = None

        if self.exp.secrets.getboolean("mongo_saving_agent", "use"):
            self.method = "mongo"
            self.query = {"exp_id": self.exp.exp_id, "exp_version": self.version, "type": "condition_data"}
        
        elif self.exp.config.get("local_saving_agent", "use"):
            self.method = "local"
            self.path = self.exp.subpath(self.exp.config.get("exp_condition", "path")) / f"randomization{self.version}.json"
            self.path.parent.mkdir(exist_ok=True, parents=True)
    
    def load(self, atomic: bool = True) -> dict:
        if self.method == "mongo":
            if atomic:
                # this will try a couple of times until if receives a version of the data that
                # can be safely worked on (with no other assignment ongoing)
                data = None
                i = 0
                while not data:
                    query = {**self.query, **{"assignment_ongoing": False}}
                    data = self.exp.db_misc.find_one_and_update(query, {"$set": {"assignment_ongoing": True}})
                    time.sleep(1)
                    i += 1
                    if i > 10:
                        self.exp.log.error("Could not find a free condition dataset in 10 trys.")
                        break
                return data
            else:
                
                # if there is no data, this returns None and places an assignment_ongoing note in the DB
                # if there is data, this returns the data and places an assignment_ongoing note in the DB
                data = self.exp.db_misc.find_one_and_update(
                    self.query, 
                    {"$set": {"assignment_ongoing": True}}, 
                    upsert=True
                    )
                return data
        
        elif self.method == "local":
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except FileNotFoundError:
                return None
    
    def write(self, data: dict, update: bool = False):
        if self.method == "mongo":
            if update:
                # this will update the slots, without touching the assignment status
                query = self.query
                data = {"slots": data["slots"]}
                self.exp.db_misc.find_one_and_update(query, {"$set": data})
            else:
                # this will replace the document, usually leading to releasing the assignment status
                query = {**self.query, **{"assignment_ongoing": True}}
                self.exp.db_misc.find_one_and_replace(query, data, upsert=True)
        
        elif self.method == "local":
            with open(self.path, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)
    
    def abort(self):
        if self.method == "mongo":
            query = {**self.query, **{"assignment_ongoing": True}}
            self.exp.db_misc.find_one_and_update(query, {"$set": {"assignment_ongoing": False}})
        

class ListRandomizer:
    """
    Offers efficient list randomization.

    Args:
        *conditions: A variable number of tuples, defining the experiment
            conditions. The tuples have the form ``("str", int)``, where
            *str* is a string giving the condition's name, and *int* is
            the target number of observations for this condition.
        
        exp (alfred3.ExperimentSession): The alfred3 experiment session.
        
        id (str): A unique identifier for the condition slot assigned
            by this instance of *ListRandomizer*. If *None*, the current
            :attr:`.ExperimentSession.session_id` will be used. 
            This argument enables you to assign, for example, a group
            id that connects several sessions, to the randomizer.
            Defaults to None.
        
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
        
        timeout (int): Timeout in seconds. After timeout expiration,
            sessions are regarded as expired. Their condition slots will
            be marked as open again. If None (default), the Randomizer 
            will use the :attr:`.ExperimentSession.session_timeout`, which
            is highly recommended. Using a shorter timeout than the 
            session timeout might result in a situation where a session
            that the Randomizer regarded as expired ends up still finishing
            the experiment.
        
        random_seed: The random seed used for reproducible pseudo-random
            behavior. This seed will be used for shuffling the condition
            list. Defaults to the current system time. Valid seeds are
            all values that are accepted by :func:`random.seed`
        
        abort_page (alfred3.page.Page): You can reference a custom
                page to be displayed to new participants, if the 
                experiment is full.

    The ListRandomizer is used by initializing it (either directly
    or via the convenience method :meth:`.balanced`) and using the
    method :meth:`.get_condition` to receive a condition. By default,
    the ListRandomizer will automatically abort new sessions and display
    an information page for participants, if the experiment is full. This
    behavior can be customized (see :meth:`.get_condition`).

    .. warning:: Be mindful of the argument *respect_version*! With the
        default setting (True), randomization starts from scratch for
        every experiment version. If you set it to False, you will
        run into an error, if you change anything about the conditions.
    
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


    def __init__(
        self,
        *conditions: Tuple[str, int],
        exp,
        id: str = None,
        respect_version: bool = True,
        mode: str = "strict",
        timeout: int = None,
        random_seed=None,
        abort_page=None,
    ):
        self.exp = exp
        self.id = id if id is not None else exp.session_id
        self.exp.finish_functions.append(self._mark_slot_finished)
        self.respect_version = respect_version
        self.mode = mode
        self.timeout = timeout if timeout is not None else self.exp.session_timeout
        self.random_seed = random_seed if random_seed is not None else time.time()
        self.conditions = conditions
        self.abort_page = abort_page
        
        self.io = _ConditionIO(self.exp, respect_version)
        self.slotlist = None
    
    @property
    def full(self) -> bool:
        """
        bool: Boolean, indicating whether there are any open slots left.
        """
        slot = next(self.slotlist.open_slots(), None)

        if slot is None and self.mode == "inclusive":
            slot = next(self.slotlist.pending_slots(), None)
        
        if slot is not None:
            return False
        else:
            return True

    @classmethod
    def balanced(cls, *conditions, n: int, **kwargs):
        """
        Alternative constructor for the ListRandomizer.

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
        conditions = [(c, n) for c in conditions]
        return cls(*conditions, **kwargs)

    def abort(self):
        self.io.abort()
        full_page_title = "Experiment closed"
        full_page_text = "Sorry, the experiment currently does not accept any further participants."
        self.exp.abort(reason="full", title=full_page_title, msg=full_page_text, icon="user-check", page=self.abort_page)
        return "__aborted__"

    def get_condition(self, 
        raise_exception: bool = False
    ) -> str:
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
        self._load_or_insert_data()

        # TODO atomisieren
        assigned_slot = self.slotlist.id_assigned_to(self.id)
        if assigned_slot is not None:
            self.io.write(self._data)
            return assigned_slot.condition

        slot = next(self.slotlist.open_slots(), None)

        if slot is None and self.mode == "inclusive":
            slot = next(self.slotlist.pending_slots(), None)

        if slot is None:
            if raise_exception:
                raise AllConditionsFull
            else:
                return self.abort()
            
        slot.sessions.append(_Session(self.id))
        self.io.write(self._data) # releases the assignment, placing the "no assignment ongoing" note
        return slot.condition
    
    def _check_consistency(self, data):
        if self.respect_version:
            assert self.exp.version == data["exp_version"]

        data_conditions = [slot["condition"] for slot in data["slots"]]
        self_conditions = [c for c, _ in self.conditions]

        what_to_do = "You might try to set 'respect_version' to True and increase the experiment version."
        msg = "Condition data is inconsistent with randomizer specification. " + what_to_do

        # all condition that appear in the data are represented in self
        if not all([condition in self_conditions for condition in data_conditions]):
            raise ConditionInconsistency(msg)

        # all conditions in self are represented in the data
        if not all([condition in data_conditions for condition in self_conditions]):
            raise ConditionInconsistency(msg)

        # number of slots is consistent
        if not len(self._generate_slots()) == len(data["slots"]):
            raise ConditionInconsistency(msg)

    def _load_or_insert_data(self):

        # check if there is any data at all, independent of assignment_ongoing status
        data = self.io.load(atomic=False) 
        
        if not data: # if not, create a dataset and mark it as assignment_ongoing
            self.slotlist = self._randomize()
            data = self._data
            data["assignment_ongoing"] = True
            self.io.write(data)
        elif data and data["assignment_ongoing"]:
            data = self.io.load() # load data again, this time respecting assignment_ongoing
        
        self._check_consistency(data)
        self.slotlist = _SlotList(*data["slots"])

        if self.full:
            self.abort()

    def _generate_slots(self) -> List[_Slot]:
        slots = []
        for c in self.conditions:
            slots += [{"condition": c[0], "timeout": self.timeout}] * c[1]
        return slots

    def _randomize(self) -> _SlotList:
        slots = self._generate_slots()
        random.seed(self.random_seed)
        random.shuffle(slots)
        return _SlotList(*slots)

    @property
    def _data(self):
        d = {}
        d["exp_id"] = self.exp.exp_id
        d["exp_version"] = self.exp.version if self.respect_version else ""
        d["type"] = "condition_data"
        d["mode"] = self.mode
        d["slots"] = asdict(self.slotlist)["slots"]
        d["random_seed"] = self.random_seed
        d["assignment_ongoing"] = False
        return d

    def _mark_slot_finished(self, exp):
        slot = self.slotlist.id_assigned_to(self.id)
        slot.finished = True
        self.io.write(self._data, update=True)
    

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