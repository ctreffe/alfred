import mongomock
import pytest
from dotenv import load_dotenv

from alfred3.quota import SessionGroup, SessionQuota
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
    exp._save_data(sync=True)

    yield exp

    clear_db()


@pytest.fixture
def exp_factory(tmp_path, mongo_client):
    def expf(sid: str = None):
        script = "tests/res/script-hello_world.py"
        secrets = "tests/res/secrets-default.conf"
        exp = get_exp_session(
            tmp_path, script_path=script, secrets_path=secrets, sid=sid
        )
        exp.data_saver.main.agents["mongo"]._mc = mongo_client
        exp._save_data(sync=True)
        return exp

    yield expf

    clear_db()


class TestSessionGroup:
    def test_remove_aborted(self, exp_factory):
        exp1 = exp_factory("s1")
        exp2 = exp_factory("s2")

        exp1.start()
        exp2.start()

        session_group = SessionGroup(["s1", "s2"])

        assert session_group.pending(exp1)
        assert not session_group.aborted(exp1)

        exp1.abort(reason="test")
        exp1._save_data(sync=True)

        assert session_group.aborted(exp1)

        assert session_group.sessions == ["s2"]
        assert session_group.aborted_sessions == ["s1"]

    def test_remove_expired(self, exp_factory):
        exp1 = exp_factory("s1")
        exp2 = exp_factory("s2")

        exp1.start()
        exp2.start()

        session_group = SessionGroup(["s1", "s2"])

        assert session_group.pending(exp1)
        assert not session_group.expired(exp1)

        exp1.session_timeout = 0.1
        exp1._save_data(sync=True)
        assert exp1.session_expired

        assert session_group.expired(exp1)
        assert session_group.sessions == ["s2"]
        assert session_group.expired_sessions == ["s1"]


class TestQuota:
    def test_initialization(self, exp):
        quota = SessionQuota(3, exp)

        assert quota

        assert quota.nopen == 3
        assert quota.nfinished == 0
        assert quota.npending == 0

    def test_count_pending_count(self, exp):
        quota = SessionQuota(3, exp)

        quota.count()
        assert quota.nopen == 2
        assert quota.nfinished == 0
        assert quota.npending == 1

    def test_count_pending_abort(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()

        quota1 = SessionQuota(1, exp1)
        quota1.count()

        assert quota1.nopen == 0
        assert quota1.nfinished == 0
        assert quota1.npending == 1

        quota2 = SessionQuota(1, exp2)
        quota2.count()

        assert exp2.aborted

    def test_count_pending_inclusive(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()

        quota1 = SessionQuota(1, exp1, inclusive=True)
        quota1.count()

        assert quota1.nopen == 0
        assert quota1.nfinished == 0
        assert quota1.npending == 1

        quota2 = SessionQuota(1, exp2, inclusive=True)
        label = quota2.count()

        assert label == quota2.slot_label

    def test_count_finished(self, exp):
        quota = SessionQuota(3, exp)

        quota.count()

        exp._start()
        exp.finish()

        assert quota.nopen == 2
        assert quota.nfinished == 1
        assert quota.npending == 0

    def test_count_abort(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()

        quota1 = SessionQuota(1, exp1)
        quota1.count()

        exp1._start()
        exp1.finish()

        assert quota1.nopen == 0
        assert quota1.nfinished == 1
        assert quota1.npending == 0

        quota2 = SessionQuota(1, exp2)
        quota2.count()

        assert exp2.aborted

    def test_count_exp_version(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()
        exp2.config.read_dict({"metadata": {"version": 1}})

        quota1 = SessionQuota(1, exp1)
        quota1.count()

        exp1._start()
        exp1.finish()

        assert quota1.nopen == 0
        assert quota1.nfinished == 1
        assert quota1.npending == 0

        quota2 = SessionQuota(1, exp2)
        label = quota2.count()

        assert label == quota2.slot_label

    def test_remove_aborted(self, exp_factory):
        exp1 = exp_factory("s1")
        exp2 = exp_factory("s2")

        quota1 = SessionQuota(1, exp1)
        quota1.count()

        exp1.abort(reason="test")
        exp1._save_data(sync=True)

        quota2 = SessionQuota(1, exp2)
        quota2.count()
