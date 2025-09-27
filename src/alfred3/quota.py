"""
Module for quota functionality.
"""

import json
import random
import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from traceback import format_exception

from pymongo.collection import ReturnDocument

from .data_manager import DataManager, saving_method
from .exceptions import AllSlotsFull, SlotInconsistency


@dataclass
class SessionGroup:
    sessions: list[str]
    aborted_sessions: list[str] = field(default_factory=list)
    expired_sessions: list[str] = field(default_factory=list)

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

    def _get_fields(self, exp, fields: list[str]) -> list:
        method = saving_method(exp)
        if "exp_session_id" not in fields:
            fields.append("exp_session_id")
        if method == "mongo":
            data = self._get_fields_mongo(exp, fields)
        elif method == "local":
            data = self._get_fields_local(exp, fields)

        return data

    def _get_fields_mongo(self, exp, fields: list[str]) -> Iterator:
        q = self.query(exp.exp_id)
        projection_fields = {field: 1 for field in fields}
        projection = {**projection_fields, **{"_id": 0}}
        cursor = exp.db_main.find(q, projection=projection)
        return cursor

    def _get_fields_local(self, exp, fields: list[str]) -> Iterator:
        cursor = self._load_local(exp)
        for sessiondata in cursor:
            yield {key: value for key, value in sessiondata.items() if key in fields}

    def _remove_inactive_sessions(self, data: list[dict], move_to: list[str]) -> None:
        for session in data:
            sid = session["exp_session_id"]
            move_to.append(sid)
            try:
                self.sessions.remove(sid)
            except ValueError:
                pass

    def finished(self, exp, data: list[dict] = None) -> bool:
        if not data:
            data = self._get_fields(exp, ["exp_finished"])
        finished = [session["exp_finished"] for session in data]
        return bool(finished) and all(finished)

    def aborted(self, exp, data: list[dict] = None) -> bool:
        if self.aborted_sessions:
            return True

        if not data:
            data = self._get_fields(exp, ["exp_aborted"])

        aborted = []
        aborted_sessions = []
        for session in data:
            aborted.append(session["exp_aborted"])
            if session["exp_aborted"]:
                aborted_sessions.append(session)

        any_aborted = any(aborted)
        if any_aborted:
            self._remove_inactive_sessions(aborted_sessions, self.aborted_sessions)

        return any_aborted

    def expired(self, exp, data: list[dict] = None) -> bool:
        if self.expired_sessions:
            return True

        if not data:
            data = self._get_fields(
                exp, ["exp_start_time", "exp_session_timeout", "exp_save_time"]
            )

        data = list(data)
        now = time.time()

        expired_sessions = []
        for session in data:
            t = session["exp_start_time"]
            timeout = session["exp_session_timeout"]

            if t is None:
                t = session["exp_save_time"]

            passed_time = now - t
            is_expired = passed_time > timeout
            if is_expired:
                expired_sessions.append(session)

        if expired_sessions:
            self._remove_inactive_sessions(expired_sessions, self.expired_sessions)

        return bool(expired_sessions)

    def started(self, exp, data: list[dict] = None) -> bool:
        if not data:
            data = self._get_fields(exp, ["exp_start_time"])
        start_time = [session["exp_start_time"] for session in data]
        if not start_time:
            raise ValueError("Session not found.")
        return not any([t is None for t in start_time])

    def most_recent_save(self, exp, data: list[dict] = None) -> float:
        if not data:
            data = self._get_fields(exp, ["exp_save_time"])

        save_time = [session["exp_save_time"] for session in data]
        if not save_time:
            raise ValueError("Session not found.")
        most_recent = max(save_time)
        return most_recent

    def oldest_save(self, exp, data: list[dict] = None) -> float:
        if not data:
            data = self._get_fields(exp, ["exp_save_time"])

        save_time = [session["exp_save_time"] for session in data]
        if not save_time:
            raise ValueError("Session not found.")
        oldest = min(save_time)
        return oldest

    def pending(self, exp) -> bool:
        fields = [
            "exp_start_time",
            "exp_finished",
            "exp_aborted",
            "exp_save_time",
            "exp_session_timeout",
        ]
        data = list(self._get_fields(exp, fields))

        finished = self.finished(exp, data)
        aborted = self.aborted(exp, data)
        expired = self.expired(exp, data)

        # if not self.started(exp, data):
        #     # use tolerance of 1 min here to give experiments time to start
        #     if time.time() - self.most_recent_save(exp, data) > 60:
        #         return False
        #     else:
        #         return True

        return not finished and not aborted and not expired


@dataclass
class Slot:
    label: str
    session_groups: list[SessionGroup] = field(default_factory=list)
    finished_sessions: list[str] = field(default_factory=list)
    aborted_sessions: list[str] = field(default_factory=list)
    expired_sessions: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.session_groups = [SessionGroup(**sdata) for sdata in self.session_groups]

    def most_recent_save(self, exp) -> float:
        oldest_saves = [s.oldest_save(exp) for s in self.session_groups]
        return max(oldest_saves)

    def npending(self, exp) -> int:
        pending = [s.pending(exp) for s in self.session_groups]
        return len(pending)

    def finished(self, exp) -> bool:
        if self.finished_sessions:
            return True

        session_groups = []
        for s in self.session_groups:
            if s.finished(exp):
                self.finished_sessions.append(s)
            else:
                session_groups.append(s)

        self.session_groups = session_groups

        return bool(self.finished_sessions)

    def pending(self, exp) -> bool:
        pending = []
        for s in self.session_groups:
            if s.finished(exp):
                if s not in self.finished_sessions:
                    self.finished_sessions.append(s)
            elif s.aborted(exp):
                if s not in self.aborted_sessions:
                    self.aborted_sessions.append(s)
            elif s.expired(exp):
                if s not in self.expired_sessions:
                    self.expired_sessions.append(s)
            else:
                pending.append(s)

        self.session_groups = pending
        return bool(pending)

    def conduct_maintenance(self, exp):
        self.pending(exp)

    def open(self, exp) -> bool:
        return not self.finished(exp) and not self.pending(exp)

    def __contains__(self, session_ids: list[str]) -> bool:
        group_contains_session = (
            session_ids == group.sessions for group in self.session_groups
        )
        return any(group_contains_session)


@dataclass
class SlotManager:
    slots: list[dict]

    def __post_init__(self):
        self.slots = [Slot(**slot_data) for slot_data in self.slots]

    def open_slots(self, exp) -> Iterator[Slot]:
        return (slot for slot in self.slots if slot.open(exp))

    def pending_slots(self, exp) -> Iterator[Slot]:
        return (slot for slot in self.slots if slot.pending(exp))

    def find_slot(self, session_ids: list[str]) -> Slot:
        for slot in self.slots:
            if session_ids in slot:
                return slot

    def conduct_maintenance(self, exp):
        [slot.conduct_maintenance(exp) for slot in self.slots]

    def next_pending(self, exp) -> Slot:
        slots = list(self.pending_slots(exp))

        if len(slots) == 1:
            return slots[0]

        slots = self._sparsest_slots(slots, exp)

        if len(slots) == 1:
            return slots[0]

        return self._oldest_slot(slots, exp)

    def _sparsest_slots(self, slots, exp) -> list[Slot]:
        npending = [slot.npending(exp) for slot in slots]
        n = min(npending)
        minimal_pending = [slot for slot in slots if slot.npending(exp) == n]
        return minimal_pending

    def _oldest_slot(self, slots, exp) -> Slot:
        most_recent_save = [slot.most_recent_save(exp) for slot in slots]
        oldest = min(most_recent_save)
        i = most_recent_save.index(oldest)
        return slots[i]


@dataclass
class QuotaData:
    name: str
    exp_id: str
    exp_version: str
    inclusive: bool
    type: str
    slots: list[dict] = field(default_factory=list)
    busy: str = "false"
    additional_info: dict = field(default_factory=dict)


class QuotaIO:
    def __init__(self, quota):
        self.quota = quota
        self.exp = quota.exp
        self.db = self.exp.db_misc

        if saving_method(self.exp) == "local":
            self.path.parent.mkdir(exist_ok=True)

    @property
    def query(self) -> dict:
        d = {}
        d["exp_id"] = self.exp.exp_id
        d["exp_version"] = self.quota.exp_version
        d["type"] = self.quota.DATA_TYPE
        d["name"] = self.quota.name
        return d

    @property
    def path(self) -> Path:
        name = f"{self.quota.DATA_TYPE}_{self.quota.name}{self.quota.exp_version}.json"
        directory = self.exp.config.get("data", "save_directory")
        directory = self.exp.subpath(directory)
        return directory / name

    def load(self) -> QuotaData:
        method = saving_method(self.exp)
        if method == "mongo":
            return self.load_mongo(self.quota._insert)
        elif method == "local":
            return self.load_local(self.quota._insert)

    def load_mongo(self, insert: QuotaData) -> QuotaData:
        q = self.query
        data = self.db.find_one_and_update(
            filter=q,
            update={"$setOnInsert": asdict(insert)},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        data.pop("_id", None)
        return QuotaData(**data)

    def load_local(self, insert: QuotaData) -> QuotaData:
        if not self.path.exists():
            self.save_local(asdict(insert))

        else:
            with open(self.path, encoding="utf-8") as fp:
                data = json.load(fp)

            return QuotaData(**data)

    def load_markbusy(self) -> QuotaData:
        method = saving_method(self.exp)
        if method == "mongo":
            return self.load_markbusy_mongo()
        elif method == "local":
            return self.load_markbusy_local()

    def load_markbusy_mongo(self) -> QuotaData:
        q = self.query
        q["busy"] = "false"

        update = {"$set": {"busy": self.exp.session_id}}
        rd = ReturnDocument.AFTER

        data = self.db.find_one_and_update(filter=q, update=update, return_document=rd)

        if data is None:
            return None

        data.pop("_id", None)

        return QuotaData(**data)

    def load_markbusy_local(self) -> QuotaData:
        if not self.path.exists():
            data = asdict(self.rand.data)

        with open(self.path, encoding="utf-8") as fp:
            data = json.load(fp)

        if not data["busy"] == "false":
            return None

        data["busy"] = self.exp.session_id
        self.save_local(data)
        return QuotaData(**data)

    def save(self, data: QuotaData):
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
        q["busy"] = self.exp.session_id
        self.db.find_one_and_update(filter=q, update={"$set": data})

    def release(self):
        method = saving_method(self.exp)
        if method == "mongo":
            self.release_mongo()
        elif method == "local":
            self.release_local()

    def release_mongo(self):
        q = self.query
        q["busy"] = self.exp.session_id
        u = {"$set": {"busy": "false"}}
        self.db.find_one_and_update(filter=q, update=u)

    def release_local(self):
        with open(self.path, encoding="utf-8") as fp:
            data = json.load(fp)
        if not data["busy"] == self.exp.session_id:
            return

        data["busy"] = "false"
        self.save_local(data)

    def __enter__(self):
        data = self.load_markbusy()
        start = time.time()
        wait = 30
        min_tries = 5
        n_tries = 0
        while not data:
            self.exp.log.debug(
                "Could not load non-busy randomizer data. Trying again after waiting"
                " for a short time."
            )
            time.sleep(random.random())
            data = self.load_markbusy()
            n_tries += 1

            if (n_tries > min_tries) and (time.time() - start > wait):
                raise RuntimeError(
                    f"Tried to load randomizer data for {wait} seconds and tried"
                    f" {n_tries} times. Could not load data, since the randomizer was"
                    " always busy."
                )
        return data

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type and exc_type != AllSlotsFull:
            self.release()
            self.exp.abort(reason="quota_error")
            tb = "".join(format_exception(exc_type, exc_value, traceback))
            self.exp.log.error(
                "There was an error in a locked operation."
                "I aborted the experiment and released the lock."
                f"{tb}"
            )

        else:
            self.release()


class SessionQuota:
    """
    A quota for experiment sessions.

    The quota allows you to enforce an upper limit on the number of
    participants in your experiment.

    Args:
        nslots (int): Maximum number of slots.
        exp (alfred3.ExperimentSession): Experiment session.
        respect_version (bool):
        inclusive (bool):
            If *False* (default), the quota will only assign a
            slot, if there are no pending sessions for that slot. It will
            not assign a slot, if a session in that slot
            is finished, or if there is an ongoing session in that slot
            that has not yet timed out. You will end up with exactly
            as many participants, as specified in *nslots*.

            If *True*, the quota will assign a slot,
            if there is no finished session in that slot. That means,
            there may be two ongoing sessions for the same slot, and
            both might end up to finish.

            While inclusive=*False* may lead to participants being turned
            away before the experiment is really complete, inclusive=True
            may lead to more data being collected than necessary.

            Defaults to *False*.
        name (str):
            An identifier for the quota. If you
            give this a custom value, you can use multiple quotas
            in the same experiment. Defaults to 'quota'.
        abort_page (alfred3.Page): You can reference a custom
                page to be displayed to new participants, if the
                quota is full.

    .. versionadded:: 2.2.0

    Examples:
        A simple example on how to use the quota::

            import alfred3 as al

            exp = al.Experiment()


            @exp.setup
            def setup(exp):
                quota = al.SessionQuota(10, exp)
                quota.count()


            exp += al.Page(title="Hello, World!", name="hello_world")

    """

    DATA_TYPE = "quota_data"

    def __init__(
        self,
        nslots: int,
        exp,
        respect_version: bool = True,
        inclusive: bool = False,
        name: str = "quota",
        abort_page=None,
    ):
        self.nslots = nslots
        self.slot_label = "slot"
        self.exp = exp
        self.respect_version = respect_version
        self.exp_version = self.exp.version if respect_version else ""
        self.inclusive = inclusive
        self.name = name
        self.session_ids = [exp.session_id]
        self.io = QuotaIO(self)
        self.abort_page = abort_page

        self._initialize_slots()

    @property
    def _insert(self) -> QuotaData:
        data = QuotaData(
            name=self.name,
            exp_id=self.exp.exp_id,
            exp_version=self.exp_version,
            inclusive=self.inclusive,
            type=self.DATA_TYPE,
        )

        return data

    def _initialize_slots(self):
        self.io.load()

        with self.io as data:
            if not data.slots:
                data.slots = self._generate_slots()
                self.io.save(data)

    def _generate_slots(self) -> list[dict]:
        slots = [{"label": self.slot_label}] * self.nslots
        return slots

    @property
    def nopen(self) -> int:
        """
        int: Number of open slots.
        """
        with self.io as data:
            return self._nopen(data)

    def _nopen(self, data) -> int:
        slot_manager = self._slot_manager(data)
        open_slots = list(slot_manager.open_slots(self.exp))
        return len(open_slots)

    @property
    def npending(self) -> int:
        """
        int: Number of slots in which a session is still ongoing.
        """
        with self.io as data:
            return self._npending(data)

    def _npending(self, data) -> int:
        slot_manager = self._slot_manager(data)
        pending_slots = list(slot_manager.pending_slots(self.exp))
        return len(pending_slots)

    @property
    def full(self) -> bool:
        """
        bool: *True*, if the randomizer has allocated all available slots.
        """
        if self.inclusive:
            return (self.nopen + self.npending) == 0
        else:
            return self.nopen == 0

    @property
    def nfinished(self) -> int:
        """
        int: Number of finished slots.
        """
        with self.io as data:
            nopen = self._nopen(data)
            npending = self._npending(data)
            return self.nslots - (nopen + npending)

    @property
    def allfinished(self) -> bool:
        """
        bool: Indicates, whether all slots in the quota are finished.
        """
        return self.nfinished == self.nslots

    def _accepts_sessions(self, data) -> bool:
        """
        bool: *True*, if all slots are full. In 'strict' mode,
        unfinished but pending experiment sessions ('pending' sessions)
        are counted. In 'inclusive' mode, only sessions that are fully
        finished are counted.
        """
        if self.inclusive:
            nopen = self._nopen(data)
            npending = self._npending(data)
            n_unfinished = nopen + npending
            return not n_unfinished == 0

        else:
            return self._nopen(data) > 0

    def count(self, raise_exception: bool = False) -> str:
        """
        Counts the experiment session associated with the quota.

        Args:
            raise_exception (bool): If True, the function raises
                the :class:`.AllSlotsFull` exception instead of
                automatically aborting the experiment if all slots
                are full. This allows you to catch the exception and
                customize the experiment's behavior in this case.

        Returns:
            str: The slot label.

        Raises:
            AllSlotsFull: If raise_exception is True and
            all slots are full.
            SlotInconsistency: If slot validation fails.

        Examples:
            A simple example on how to use the quota::

                import alfred3 as al

                exp = al.Experiment()


                @exp.setup
                def setup(exp):
                    quota = al.SessionQuota(10, exp)
                    quota.count()


                exp += al.Page(title="Hello, World!", name="hello_world")
        """
        with self.io as data:
            self.exp.log.debug("Loaded quota data. Starting to count.")
            self._validate(data)

            slot_manager = self._slot_manager(data)
            slot = self._own_slot(data)

            if slot:
                self.exp.log.debug(
                    "This session was already assigned to a slot. Returning its slot"
                    " label."
                )
                return slot.label

            full = not self._accepts_sessions(data)
            if full and raise_exception:
                self.exp.log.info(
                    "The quota is full. Aborting count with an exception."
                )
                raise AllSlotsFull
            elif full:
                self.exp.log.info(
                    "The quota is full. Aborting count by aborting the experiment."
                )
                self._abort_exp()
                return "__ABORTED__"

            slot = next(slot_manager.open_slots(self.exp), None)

            if slot is None and self.inclusive:
                self.exp.log.info(
                    "Found no open slot. Searching for a pending slot next, since the"
                    " quota is inclusive."
                )
                slot = slot_manager.next_pending(self.exp)

            if slot is None:
                msg = "No slot found, even though the quota does not appear to be full."
                raise SlotInconsistency(msg)

            self.exp.log.info(
                "The quota found a slot for the current session. Starting to update the"
                " database representations."
            )
            self._update_slot(slot)

            try:  # for compatibility with alfred3-interact
                slot_manager.conduct_maintenance(self.exp)
            except AttributeError:
                pass
            data.slots = asdict(slot_manager)["slots"]
            self.io.save(data)
            self.exp.log.debug(
                "The quota has finished to update the database representations."
                " Returning the slot label now."
            )
            return slot.label

    def _update_slot(self, slot):
        group = SessionGroup(self.session_ids)
        slot.session_groups.append(group)

    def _slot_manager(self, data: QuotaData) -> SlotManager:
        return SlotManager(data.slots)

    def next(self) -> Slot:
        """
        Returns the next open slot.
        """
        with self.io as data:
            open_slots = self._slot_manager(data).open_slots(self.exp)

        return next(open_slots)

    def _own_slot(self, data: QuotaData) -> Slot:
        slot_manager = self._slot_manager(data)
        slot = slot_manager.find_slot(self.session_ids)
        return slot

    def _validate(self, data: QuotaData):
        if self.respect_version:
            if not self.exp.version == data.exp_version:
                raise SlotInconsistency(
                    "Experiment version and randomizer version do not match."
                )

    def _abort_exp(self):
        self.exp.log.info("The quota starts to abort the experiment.")
        full_page_title = "Experiment closed"
        full_page_text = (
            "Sorry, the experiment currently does not accept any further participants."
        )
        self.exp.abort(
            reason="full",
            title=full_page_title,
            msg=full_page_text,
            icon="user-check",
            page=self.abort_page,
        )
