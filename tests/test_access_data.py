import pytest

from alfred3.testutil import clear_db, get_exp_session


@pytest.fixture
def exp(tmp_path):
    script = "tests/res/script-hello_world.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)

    yield exp

    clear_db()


def test_access_data(exp):
    exp.start()
    exp._save_data(sync=True)
    assert exp.all_exp_data
