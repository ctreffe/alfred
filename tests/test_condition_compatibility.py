import random
import time

import mongomock
import pytest
from dotenv import load_dotenv

import alfred3.compatibility.condition as cond
from alfred3.compatibility.condition import ConditionInconsistency
from alfred3.testutil import clear_db, get_exp_session

load_dotenv()


@pytest.fixture
def mongo_client():
    yield mongomock.MongoClient()


@pytest.fixture
def exp(tmp_path, mongo_client):
    script = "tests/res/script-hello_world.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)
    exp.data_saver.main.agents["mongo"]._mc = mongo_client

    yield exp

    clear_db()


@pytest.fixture
def exp_factory(tmp_path, mongo_client):
    def expf():
        script = "tests/res/script-hello_world.py"
        secrets = "tests/res/secrets-default.conf"
        exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)
        exp.data_saver.main.agents["mongo"]._mc = mongo_client
        return exp

    yield expf

    clear_db()


@pytest.fixture
def lexp(tmp_path):
    script = "tests/res/script-hello_world.py"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=None)
    yield exp


@pytest.fixture
def strict_exp(exp):
    rd = cond.ListRandomizer(("a", 10), ("b", 10), exp=exp)
    exp.condition = rd.get_condition()
    yield exp


def test_clear(exp):
    """
    Just for clearing the database in case a test breaks down with an error.
    """
    print(exp)


class TestConditionValidation:
    def test_pass_validation(self, strict_exp):
        rd = cond.ListRandomizer(("a", 10), ("b", 10), exp=strict_exp)
        assert rd.get_condition()

    def test_change_mode(self, strict_exp):
        rd = cond.ListRandomizer(("a", 10), ("b", 10), exp=strict_exp, mode="inclusive")
        assert rd.get_condition()

    def test_change_of_n(self, strict_exp):
        rd = cond.ListRandomizer(("a", 10), ("b", 9), exp=strict_exp)
        with pytest.raises(ConditionInconsistency):
            rd.get_condition()

    def test_change_of_name(self, strict_exp):
        rd = cond.ListRandomizer(("a", 10), ("c", 10), exp=strict_exp)
        with pytest.raises(ConditionInconsistency):
            rd.get_condition()

    def test_add_condition(self, strict_exp):
        rd = cond.ListRandomizer(("a", 10), ("b", 10), ("c", 10), exp=strict_exp)
        with pytest.raises(ConditionInconsistency):
            rd.get_condition()

    def test_remove_condition(self, strict_exp):
        rd = cond.ListRandomizer(("a", 10), exp=strict_exp)
        with pytest.raises(ConditionInconsistency):
            rd.get_condition()

    def test_increase_version(self, strict_exp):
        strict_exp.config.read_dict({"metadata": {"version": "0.2"}})
        assert strict_exp.version == "0.2"

        rd = cond.ListRandomizer(("a", 10), exp=strict_exp)
        assert rd.get_condition()


def rd_slots(*conditions, exp, seed):
    rd = cond.ListRandomizer(*conditions, exp=exp, random_seed=seed)
    rd.get_condition()

    rd_slots = [slot.condition for slot in rd.slotlist.slots]
    return rd_slots


def slots(*conditions, seed):
    slots = []
    for c, n in conditions:
        slots += [c] * n
    random.seed(seed)
    random.shuffle(slots)
    return slots


class TestConditionShuffle:
    def test_shuffle_mongo(self, exp):
        conditions = [("a", 20), ("b", 20)]
        seed1 = 123
        s1 = rd_slots(*conditions, exp=exp, seed=seed1)

        exp.config.read_dict({"metadata": {"version": "0.2"}})
        seed2 = 12345
        s2 = rd_slots(*conditions, exp=exp, seed=seed2)

        assert s1 != s2

    def test_shuffle_seed_mongo(self, exp):
        conditions = [("a", 20), ("b", 20)]
        seed = 12345

        s1 = rd_slots(*conditions, exp=exp, seed=seed)
        s2 = slots(*conditions, seed=seed)

        assert s1 == s2

    def test_shuffle_local(self, lexp):
        conditions = [("a", 20), ("b", 20)]
        seed1 = 123
        s1 = rd_slots(*conditions, exp=lexp, seed=seed1)

        lexp.config.read_dict({"metadata": {"version": "0.2"}})
        seed2 = 12345
        s2 = rd_slots(*conditions, exp=lexp, seed=seed2)

        assert s1 != s2

    def test_shuffle_seed_local(self, lexp):
        conditions = [("a", 20), ("b", 20)]
        seed = 12345

        s1 = rd_slots(*conditions, exp=lexp, seed=seed)
        s2 = slots(*conditions, seed=seed)

        assert s1 == s2


class TestConditionAllocation:
    def test_aborted_session(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp1, random_seed=seed)
        exp1.condition = rd1.get_condition()

        slots = rd1.slotlist.slots
        assert exp1.condition == slots[0].condition
        assert slots[0].condition != slots[1].condition

        exp1._start()
        exp1.abort("test")
        exp1._save_data(sync=True)

        exp1_session = rd1.slotlist.slots[0].sessions[0]
        assert not exp1_session.active(exp1)

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp2, random_seed=seed)
        exp2.condition = rd2.get_condition()
        assert exp2.condition == exp1.condition

    def test_active_session(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp1, random_seed=seed)
        exp1.condition = rd1.get_condition()

        exp1._start()
        exp1._save_data(sync=True)

        exp1_session = rd1.slotlist.slots[0].sessions[0]
        assert exp1_session.active(exp1)

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp2, random_seed=seed)
        exp2.condition = rd2.get_condition()

        assert exp2.condition != exp1.condition

    def test_finished_session(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp1, random_seed=seed)
        exp1.condition = rd1.get_condition()

        exp1._start()
        exp1.finish()

        slot1 = rd1.slotlist.slots[0]
        exp1_session = slot1.sessions[0]

        assert slot1.finished
        assert not exp1_session.active(exp1)

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp2, random_seed=seed)
        exp2.condition = rd2.get_condition()

        assert exp2.condition != exp1.condition

    def test_expired_session(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp1, random_seed=seed)
        exp1.condition = rd1.get_condition()

        exp1._start()
        exp1._start_time = exp1._start_time - exp1.session_timeout - 1

        assert exp1.session_expired
        exp1._save_data(sync=True)

        slot1 = rd1.slotlist.slots[0]
        exp1_session = slot1.sessions[0]

        assert not slot1.finished
        assert not exp1_session.active(exp1)

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp2, random_seed=seed)
        exp2.condition = rd2.get_condition()

        assert exp2.condition == exp1.condition

    def test_slots_full_strict(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp1, random_seed=seed)
        exp1.condition = rd1.get_condition()
        exp1._start()
        exp1._save_data(sync=True)

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp2, random_seed=seed)
        exp2.condition = rd2.get_condition()
        exp2._start()
        exp2._save_data(sync=True)

        exp3 = exp_factory()
        rd3 = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp3, random_seed=seed)
        exp3.condition = rd3.get_condition()

        assert exp3.aborted

    def test_slots_inclusive(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced(
            "a", "b", n=1, exp=exp1, random_seed=seed, mode="inclusive"
        )
        exp1.condition = rd1.get_condition()
        exp1._start()
        exp1.finish()

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer.balanced(
            "a", "b", n=1, exp=exp2, random_seed=seed, mode="inclusive"
        )
        exp2.condition = rd2.get_condition()
        exp2._start()

        assert exp1.condition != exp2.condition

        exp3 = exp_factory()
        rd3 = cond.ListRandomizer.balanced(
            "a", "b", n=1, exp=exp3, random_seed=seed, mode="inclusive"
        )
        exp3.condition = rd3.get_condition()

        assert exp2.condition == exp3.condition

    def test_slots_full_inclusive(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced(
            "a", "b", n=1, exp=exp1, random_seed=seed, mode="inclusive"
        )
        exp1.condition = rd1.get_condition()
        exp1._start()
        exp1.finish()

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer.balanced(
            "a", "b", n=1, exp=exp2, random_seed=seed, mode="inclusive"
        )
        exp2.condition = rd2.get_condition()
        exp2._start()
        exp2.finish()

        assert exp1.condition != exp2.condition

        exp3 = exp_factory()
        rd3 = cond.ListRandomizer.balanced(
            "a", "b", n=1, exp=exp3, random_seed=seed, mode="inclusive"
        )
        exp3.condition = rd3.get_condition()

        assert exp3.aborted

    def test_balanced_constructor(self, exp_factory):
        exp1 = exp_factory()
        seed = 12348
        rd1 = cond.ListRandomizer.balanced("a", "b", n=10, exp=exp1, random_seed=seed)
        exp1.condition = rd1.get_condition()

        exp2 = exp_factory()
        rd2 = cond.ListRandomizer(("a", 10), ("b", 10), exp=exp2, random_seed=seed)
        exp2.condition = rd2.get_condition()

        slots1 = [s.condition for s in rd1.slotlist.slots]
        slots2 = [s.condition for s in rd2.slotlist.slots]
        assert slots1 == slots2

    def test_session_expired(self, exp_factory):
        exp1 = exp_factory()
        exp1.session_timeout = 1
        rand = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp1)

        exp1.condition = rand.get_condition()
        exp1._start()
        time.sleep(1)

        assert exp1.session_expired

        slot = rand.slotlist.id_assigned_to(exp1.session_id)
        slot.active_sessions(exp1)

        exp2 = exp_factory()

        assert exp1.exp_id == exp2.exp_id

        rand2 = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp2)
        exp2.condition = rand2.get_condition()

        assert exp1.condition == exp2.condition

    def test_shifted_finish(self, exp_factory):
        exp1 = exp_factory()
        rand = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp1)

        exp1.condition = rand.get_condition()
        exp1._start()
        exp1._save_data(sync=True)

        exp2 = exp_factory()
        rand2 = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp2)
        exp2.condition = rand2.get_condition()
        exp2._start()
        exp2._save_data(sync=True)

        assert exp1.condition != exp2.condition

        exp1.finish()

        rdata = exp1.db_misc.find_one({"type": "condition_data"})
        slotlist = cond._SlotList(*rdata["slots"])

        assert slotlist.slots[0].finished
        assert not slotlist.slots[1].finished

        exp2.finish()

        rdata = exp1.db_misc.find_one({"type": "condition_data"})
        slotlist = cond._SlotList(*rdata["slots"])

        assert slotlist.slots[0].finished
        assert slotlist.slots[1].finished


class TestSession:
    def test_init(self):
        s1 = cond._Session(id="abc")
        s2 = cond._Session(id="abc")
        assert s2.timestamp
        assert s1.timestamp

    def test_active(self, exp):
        s1 = cond._Session(id=exp.session_id)
        assert not s1.active(exp)

    def test_mark_finished(self, exp):
        rand = cond.ListRandomizer.balanced("a", "b", n=1, exp=exp)
        exp.condition = rand.get_condition()
        rand._mark_slot_finished(exp)

        slot = rand.slotlist.id_assigned_to(exp.session_id)
        assert slot.finished
