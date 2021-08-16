import pytest

import alfred3 as al
from alfred3.config import ExperimentSecrets, ExperimentConfig
from alfred3.exceptions import AlfredError
from alfred3.testutil import get_app, clear_db, forward

from dotenv import load_dotenv
load_dotenv()

@pytest.fixture
def client(tmp_path):
    script = "tests/res/script-admin.py"
    secrets = "tests/res/secrets-admin.conf"
    
    app = get_app(tmp_path, script_path=script, secrets_path=secrets)

    with app.test_client() as client:
        yield client
    
    clear_db()


def test_admin_exp(client):
    rv = client.get("/start?admin=true", follow_redirects=True)
    assert b"Admin" in rv.data

    rv = forward(client, data={"pw": "test"})
    assert b"Admin" in rv.data
    assert not b"Bitte geben Sie etwas ein." in rv.data

    rv = forward(client)
    assert b"Admin2" in rv.data


def test_admin(tmp_path):
    exp = al.Experiment()
    exp.admin += al.Page(name="admin_test")

    config = ExperimentConfig(tmp_path)
    secrets = ExperimentSecrets(tmp_path)
    secrets.read_dict({"general": {"admin_pw": "test"}})
    urlargs = {"admin": "true"}

    session = exp.create_session("sid1", config, secrets, **urlargs)
    assert session.admin_mode

def test_admin_without_password(tmp_path):
    exp = al.Experiment()
    exp.admin += al.Page(name="admin_test")

    config = ExperimentConfig(tmp_path)
    secrets = ExperimentSecrets(tmp_path)
    urlargs = {"admin": "true"}

    with pytest.raises(AlfredError):
        exp.create_session("sid1", config, secrets, **urlargs)
    