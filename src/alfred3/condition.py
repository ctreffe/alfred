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
        now = time.time()
        return [s for s in self.sessions if (now - s.timestamp) < self.timeout]

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
            self.query = {"exp_id": self.exp.exp_id, "exp_version": self.version}
        
        elif self.exp.config.get("local_saving_agent", "use"):
            self.method = "local"
            self.path = self.exp.subpath(self.exp.config.get("exp_condition", "path")) / f"randomization{self.version}.json"
    
    def load(self) -> dict:
        if self.method == "mongo":
            return self.exp.db_misc.find_one(self.query)
        elif self.method == "local":
            with open(self.path, "r") as f:
                return json.load(f)
    
    def write(self, data: dict):
        if self.method == "mongo":
            self.exp.log.warning( "write called with: " + str(data))

            from pprint import pprint
            pprint(self.query)
            pprint(data)
            
            d = self.exp.db_misc.find_one()
            pprint(d)

            self.exp.db_misc.find_one_and_replace(self.query, data, upsert=True)

            d = self.exp.db_misc.find_one(self.query)
            if not d:
                self.exp.log.error("no data saved.")

        elif self.method == "local":
            with open(self.path, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)

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
            experiment, which might cause the randomizer to fail, causing
            :class:`.ConditionInconsistency` errors.
            Setting *respect_version* to True can fix such issues. 
            Defaults to False.
        
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
            be marked as open again. Defaults to 12 hours.
        
        random_seed: The random seed used for reproducible pseudo-random
            behavior. This seed will be used for shuffling the condition
            list. Defaults to the current system time.

    The ListRandomizer is used by initializing it (either directly
    or via the convenience method :meth:`.balanced`) and using the
    method :meth:`.get_condition` to receive a condition. By default,
    the ListRandomizer will automatically abort new sessions and display
    an information page for participants, if the experiment is full. This
    behavior can be customized (see :meth:`.get_condition`).
    
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

    """


    def __init__(
        self,
        *conditions: Tuple[str, int],
        exp,
        id: str = None,
        respect_version: bool = False,
        mode: str = "strict",
        timeout: int = 60 * 60 * 12,
        random_seed=time.time(),
    ):
        self.exp = exp
        self.id = id if id is not None else exp.session_id
        self.exp.finish_functions.append(self._mark_slot_finished)
        self.respect_version = respect_version
        self.mode = mode
        self.timeout = timeout
        self.random_seed = random_seed
        self.conditions = conditions
        
        self.io = _ConditionIO(self.exp, respect_version)

        try:
            data = self.io.load()
            self._check_consistency(data)
            self.slotlist = _SlotList(*data["slots"])
        except (FileNotFoundError, TypeError):
            self.exp.log.exception("error")
            self.slotlist = self._randomize()


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

    def get_condition(self, 
        full_page_title: str = "Experiment closed",
        full_page_text: str = "Sorry, the experiment currently does not accept any further participants.",
        customize_full_behavior: bool = False
    ) -> str:
        """
        Returns a condition.

        Args:
            full_page_title (str): Displayed title of the 'experiment full' 
                page, shown to new participants if all conditions are 
                full.
            full_page_text (str): Displayed text on the 'experiment full'
                page.
            customize_full_behavior (bool): If True, the function raises
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
            AllConditionsFull: If customize_full_behavior is True and
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
            It re-implements the default behavior, but showcases how
            you can customize behavior::

                import alfred3 as al
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    randomizer = al.ListRandomizer(("cond1", 10), ("cond2", 10), exp=exp)
                    try:
                        exp.condition = randomizer.get_condition()
                    except al.AllConditionsFull:
                        exp.abort(
                            reason="full",
                            title="Experiment closed.",
                            msg="Sorry, the experiment currently does not accept any further participants."
                            )
                
                
                @exp.member
                class DemoPage(al.Page):

                    def on_exp_access(self):

                        if self.exp.condition == "cond1":
                            lab = "label in condition 1"
                        
                        elif self.exp.condition == "cond2":
                            lab = "label in condition 2"
                
                        self += al.TextEntry(leftlab=lab, name="t1")

        """
        assigned_slot = self.slotlist.id_assigned_to(self.id)
        if assigned_slot is not None:
            return assigned_slot.condition

        slot = next(self.slotlist.open_slots(), None)

        if slot is None and self.mode == "inclusive":
            slot = next(self.slotlist.pending_slots(), None)

        if slot is None:
            if customize_full_behavior:
                raise AllConditionsFull
            else:
                self.exp.abort(reason="full", title=full_page_title, msg=full_page_text)
                return "__aborted__"
            
        slot.sessions.append(_Session(self.id))
        self.io.write(self._data)
        return slot.condition

    @property
    def _data(self):
        d = {}
        d["exp_id"] = self.exp.exp_id
        d["exp_version"] = self.exp.version if self.respect_version else ""
        d["type"] = "condition_data"
        d["mode"] = self.mode
        d["slots"] = asdict(self.slotlist)["slots"]
        d["random_seed"] = self.random_seed
        return d

    @classmethod
    def balanced(cls, *conditions, n_per_condition: int, **kwargs):
        """
        Alternative constructor for the ListRandomizer.

        Args:
            *conditions (str): A variable number of strings, giving the
                condition names.
            n_per_condition (int): The number of participants aimed at
                per condition.
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
                    randomizer = al.ListRandomizer.balanced("cond1", "cond2", n_per_condition=10, exp=exp)
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
        conditions = [(c, n_per_condition) for c in conditions]
        return cls(*conditions, **kwargs)

    def _mark_slot_finished(self, exp):
        slot = self.slotlist.id_assigned_to(self.id)
        slot.finished = True
        self.io.write(self._data)
