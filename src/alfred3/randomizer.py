"""
Module for randomizing functionality.
"""

import random
import json
import time
from typing import List, Tuple
from itertools import product
from collections import Counter

from .quota import SessionQuota, QuotaData, QuotaIO
from .exceptions import ConditionInconsistency
from .data_manager import saving_method
from .compatibility.condition import ListRandomizer as OldListRandomizer


class ListRandomizer(SessionQuota):
    """
    Offers list randomization.

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
            :class:`.SlotInconsistency` errors.
            Setting *respect_version* to True can fix such issues.
            Defaults to True.

        inclusive (bool): If *False* (default), the randomizer will only 
            assign a condition slot, if there are no pending sessions for 
            that slot. It will not assign a condition slot, if a session 
            in that slot is finished, or if there is an ongoing session 
            in that slot that has not yet timed out. You will end up with 
            exactly as many participants in each condition as specified 
            in the target size.

            If *True*, the randomizer will assign a condition slot,
            if there is no finished session in that slot. That means,
            there might be two ongoing sessions for the same slot, and
            both might end up to finish.

            While inclusive=*False* may lead to participants being turned
            away before the experiment is really complete, inclusive=True
            may lead to more data being collected than necessary.

            Defaults to *False*.

        name (str): An identifier for the randomizer. If you
            set this to a custom value, you can use multiple randomizers
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
        
        mode (str): Deprecated in favor of *inclusive*. Please use
            the argument *inclusive* instead.

    The ListRandomizer is used by initializing it (either directly
    or via the convenience method :meth:`.balanced`) and using the
    method :meth:`.get_condition` to receive a condition. By default,
    the ListRandomizer will automatically abort sessions if the 
    experiment is full when *get_condition* is called and display
    an information page for participants. This
    behavior can be customized (see :meth:`.get_condition`).

    The ListRandomizer will not count experiment sessions that have
    expired due to being inactive for a long time. You can control
    this timeout via :attr:`.ExperimentSession.session_timeout`.


    .. warning:: Be mindful of the argument *respect_version*! With the
        default setting (True), randomization starts from scratch for
        every experiment version. If you set it to False, you will
        run into an error, if you change anything about the conditions.

    .. versionchanged:: 2.2.0
       - Deprecated the parameter *session_ids* without replacement. The 
         ListRandomizer is now aimed exclusively at allocating one session
         at a time.
       - Removed the method *abort_if_full*. Instead, you can check 
         the randomizer's status with the attributes :attr:`.full`,
         :attr:`.allfinished`, :attr:`.nopen`, :attr:`.npending`, and 
         :attr:`.nfinished` and call :meth:`.ExperimentSession.abort` 
         directly.
    
    .. versionchanged:: 2.1.7
       New parameters *session_ids* and *name*, new alternative
       constructor :meth:`.factors`. Deprecated the parameter *id*.

    Notes:

        **Why use list randomization?**

        In "naive" randomization, you might end up with a very unbalanced
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

    DATA_TYPE = "randomizer_data"

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
            directory = exp.config.get("data", "save_directory")
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
        inclusive: bool = False,
        random_seed=None,
        abort_page=None,
        name: str = "randomizer",
        mode: str = None,
        id: str = None,
    ):

        self.exp = exp
        self.respect_version = respect_version
        self.exp_version = self.exp.version if respect_version else ""
        self.inclusive = inclusive
        self.random_seed = random_seed if random_seed is not None else time.time()
        self.conditions = conditions
        self.abort_page = abort_page
        self.name = name
        self.session_ids = session_ids if session_ids is not None else [exp.session_id]
        if isinstance(self.session_ids, str):
            raise ValueError(
                "Argument 'session_ids' must be a list of strings, not a single string."
            )

        self.io = QuotaIO(self)
        self._initialize_slots()
        self._nslots = None
        
        if mode in ["strict", "inclusive"]:
            self.exp.log.warning(("Argument 'mode' is deprecated. Please use 'inclusive=True' or 'inclusive=False'  "f"instead. Using 'mode={mode}' for now for compatibility."))
            self.inclusive = mode == "inclusive"
        
        self.exp.append_plugin_data_query(self._plugin_data_query)

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

        In elaborated quota-balanced designs, you may end up with a lot
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
                
                import alfred3 as al

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

                import alfred3 as al

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
    def _plugin_data_query(self):
        f = {"exp_id": self.exp.exp_id, "type": self.DATA_TYPE, "name": self.name}

        q = {}
        q["title"] = "Randomizer Data"
        q["type"] = self.DATA_TYPE
        q["query"] = {"filter": f}
        q["encrypted"] = False

        return q
    
    @property
    def nslots(self) -> int:
        if not self._nslots:
            nslots = 0
            for _, n in self.conditions:
                nslots += n
            
            self._nslots = nslots
        
        return self._nslots

    @property
    def _insert(self) -> QuotaData:
        data = QuotaData(
            name=self.name,
            exp_id=self.exp.exp_id,
            exp_version=self.exp_version,
            inclusive=self.inclusive,
            type=self.DATA_TYPE,
            additional_info={"random_seed": self.random_seed}
        )

        return data

    def get_condition(self, raise_exception: bool = False) -> str:
        """
        Returns a condition.

        Args:
            raise_exception (bool): If True, the function raises
                the :class:`.AllSlotsFull` exception instead of
                automatically aborting the experiment if all slots
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
            AllSlotsFull: If raise_exception is True and
            all conditions are full.
            SlotInconsistency: If slot validation fails.

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
            you can customize behavior by catching the "AllSlotsFull"
            exception::

                import alfred3 as al
                from alfred3 import exceptions as alexcept
                exp = al.Experiment()

                @exp.setup
                def setup(exp):
                    randomizer = al.ListRandomizer(("cond1", 10), ("cond2", 10), exp=exp)
                    try:
                        exp.condition = randomizer.get_condition(raise_exception=True)
                    except alexcept.AllSlotsFull:
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
        return super().count(raise_exception=raise_exception)

    def _initialize_slots(self):
        self.io.load()

        with self.io as data:
            if not data.slots:
                data.slots = self._randomize_slots()
                self.io.save(data)

    def _generate_slots(self) -> List[dict]:
        slots = []
        for name, n in self.conditions:
            slots += [{"label": name}] * n
        return slots

    def _randomize_slots(self) -> List[dict]:
        slots = self._generate_slots()
        random.seed(self.random_seed)
        random.shuffle(slots)
        return slots

    def _validate(self, data: QuotaData):
        if self.respect_version:
            if not self.exp.version == data.exp_version:
                raise ConditionInconsistency(
                    "Experiment version and randomizer version do not match."
                )

        data_conditions = [slot["label"] for slot in data.slots]
        counted = Counter(data_conditions)

        instance = dict(self.conditions)

        msg = "Condition data is inconsistent with randomizer specification. "
        what_to_do = "You can set 'respect_version' to True and increase the experiment version."
        if not counted == instance:
            raise ConditionInconsistency(msg + what_to_do)


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