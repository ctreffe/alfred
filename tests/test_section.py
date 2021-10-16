import pytest
import random
import alfred3 as al
from alfred3.testutil import get_exp_session, clear_db

@pytest.fixture
def exp_shuffle(tmp_path):
    script = "tests/res/script-shuffle.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)

    yield exp

    clear_db()


class TestSection:

    def test_shuffle1(self, exp_shuffle):
        exp = exp_shuffle

        assert exp.movement_manager.first_page.name == "p01"
        random.seed(1)
        exp.start()
        
        pages = [p.name for p in exp.Main.members.values()]
        assert pages == ["p02", "p03", "p01"]
    

    def test_shuffle2(self, exp_shuffle):
        exp = exp_shuffle

        assert exp.movement_manager.first_page.name == "p01"
        random.seed(123123)
        exp.start()
        
        pages = [p.name for p in exp.Main.members.values()]
        assert pages == ["p03", "p02", "p01"]
