"""
General tests that have not yet been refactored into specific test
modules.
"""

import pytest
from dotenv import load_dotenv

from alfred3.testutil import clear_db, get_exp_session

load_dotenv()


@pytest.fixture
def expfin(tmp_path):
    script = "tests/res/script-finish.py"
    secrets = "tests/res/secrets-default.conf"

    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)
    exp._start()

    yield exp

    clear_db()


def test_early_finish(expfin):
    expfin.forward()
    assert expfin.finished
    assert expfin.First.is_closed
    assert not expfin.Second.is_closed


def test_normal_finish(expfin):
    expfin.forward()
    expfin.forward()
    assert expfin.finished
    assert expfin.Second.is_closed
