import pytest

import alfred3 as al
import alfred3.element.input as inp
from alfred3.exceptions import AlfredError
from alfred3.testutil import get_exp_session, clear_db

@pytest.fixture
def exp(tmp_path):
    script = "tests/res/script-hello_world.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)

    exp += al.Page(title="Testpage", name="testpage")

    yield exp

    clear_db()


class TestPasswordEntry:

    def test_nomatch(self, exp):
        exp.testpage += inp.PasswordEntry("rightpass", name="pentry")
        exp.testpage._set_data({"pentry": "wrongpass"})

        assert not exp.testpage.pentry.validate_data()
    
    def test_match(self, exp):
        exp.testpage += inp.PasswordEntry("rightpass", name="pentry")
        exp.testpage._set_data({"pentry": "rightpass"})

        assert exp.testpage.pentry.validate_data()

    def test_list_of_passwords(self, exp):
        with pytest.raises(AlfredError) as excinfo:
            inp.PasswordEntry(["rightpass1", "rightpass2"], name="pentry")

        assert "must be a string" in str(excinfo.value) and "pentry" in str(excinfo.value)


class TestMultiplePasswordEntry:

    def test_singlepass(self, exp):
        with pytest.raises(AlfredError) as excinfo:
            inp.MultiplePasswordEntry("rightpass", name="pentry")
        exp.testpage._set_data({"pentry": "wrongpass"})

        assert "must be a list or a tuple" in str(excinfo.value) and "pentry" in str(excinfo.value)
    
    def test_match1(self, exp):
        exp.testpage += inp.MultiplePasswordEntry(["rightpass1", "rightpass2"], name="pentry")
        exp.testpage._set_data({"pentry": "rightpass1"})

        assert exp.testpage.pentry.validate_data()
    
    def test_match2(self, exp):
        exp.testpage += inp.MultiplePasswordEntry(["rightpass1", "rightpass2"], name="pentry")
        exp.testpage._set_data({"pentry": "rightpass2"})

        assert exp.testpage.pentry.validate_data()

