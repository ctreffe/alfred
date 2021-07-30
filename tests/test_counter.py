import pytest
from alfred3.randomizer import SessionCounter
from alfred3.testutil import get_exp_session, clear_db
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def exp(tmp_path):
    script = "tests/res/script-hello_world.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)

    yield exp

    clear_db()


@pytest.fixture
def exp_factory(tmp_path):
    def expf():
        script = "tests/res/script-hello_world.py"
        secrets = "tests/res/secrets-default.conf"
        exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)
        return exp

    yield expf

    clear_db()


class TestCounter:

    def test_initialization(self, exp):
        counter = SessionCounter(3, exp)

        assert counter

        assert counter.nopen == 3
        assert counter.nfinished == 0
        assert counter.npending == 0
    

    def test_count_pending_count(self, exp):
        counter = SessionCounter(3, exp)

        counter.count()
        assert counter.nopen == 2
        assert counter.nfinished == 0
        assert counter.npending == 1
    
    def test_count_pending_abort(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()
        
        counter1 = SessionCounter(1, exp1)
        counter1.count()

        assert counter1.nopen == 0
        assert counter1.nfinished == 0
        assert counter1.npending == 1

        counter2 = SessionCounter(1, exp2)
        counter2.count()

        assert exp2.aborted

    def test_count_pending_inclusive(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()
        
        counter1 = SessionCounter(1, exp1, inclusive=True)
        counter1.count()

        assert counter1.nopen == 0
        assert counter1.nfinished == 0
        assert counter1.npending == 1

        counter2 = SessionCounter(1, exp2, inclusive=True)
        label = counter2.count()

        assert label == counter2.slot_label

    
    def test_count_finished(self, exp):
        counter = SessionCounter(3, exp)

        counter.count()

        exp._start()
        exp.finish()

        assert counter.nopen == 2
        assert counter.nfinished == 1
        assert counter.npending == 0
    
    def test_count_abort(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()
        
        counter1 = SessionCounter(1, exp1)
        counter1.count()

        exp1._start()
        exp1.finish()

        assert counter1.nopen == 0
        assert counter1.nfinished == 1
        assert counter1.npending == 0

        counter2 = SessionCounter(1, exp2)
        counter2.count()

        assert exp2.aborted
    
    def test_count_exp_version(self, exp_factory):
        exp1 = exp_factory()
        exp2 = exp_factory()
        exp2.config.read_dict({"metadata": {"version": 1}})

        counter1 = SessionCounter(1, exp1)
        counter1.count()

        exp1._start()
        exp1.finish()

        assert counter1.nopen == 0
        assert counter1.nfinished == 1
        assert counter1.npending == 0

        counter2 = SessionCounter(1, exp2)
        label = counter2.count()

        assert label == counter2.slot_label