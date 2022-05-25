import pytest
from dotenv import load_dotenv

import alfred3 as al
from alfred3.config import ExperimentConfig, ExperimentSecrets
from alfred3.exceptions import AlfredError
from alfred3.testutil import clear_db, forward, get_app

load_dotenv()


@pytest.fixture
def client(tmp_path):
    script = "tests/res/script-admin.py"
    secrets = "tests/res/secrets-admin.conf"

    app = get_app(tmp_path, script_path=script, secrets_path=secrets)

    with app.test_client() as client:
        yield client

    clear_db()


class TestValidation:
    def test_admin_without_password(self, tmp_path):
        exp = al.Experiment()
        exp.admin += al.Page(name="admin_test")

        config = ExperimentConfig(tmp_path)
        secrets = ExperimentSecrets(tmp_path)
        urlargs = {"admin": "true"}

        with pytest.raises(AlfredError):
            exp.create_session("sid1", config, secrets, **urlargs)

    def test_admin_missing_password(self, tmp_path):
        exp = al.Experiment()
        exp.admin += al.Page(name="admin_test")

        config = ExperimentConfig(tmp_path)
        secrets = ExperimentSecrets(tmp_path)
        urlargs = {"admin": "true"}

        secrets.read_dict({"general": {"adminpass_lvl2": "test"}})

        with pytest.raises(AlfredError) as excinfo:
            exp.create_session("sid1", config, secrets, **urlargs)

        msg = str(excinfo.value)
        assert "lvl1" in msg and "lvl3" in msg and "lvl2" not in msg

    def test_admin_equal_passwords(self, tmp_path):
        exp = al.Experiment()
        exp.admin += al.Page(name="admin_test")

        config = ExperimentConfig(tmp_path)
        secrets = ExperimentSecrets(tmp_path)
        urlargs = {"admin": "true"}

        secrets.read_dict(
            {
                "general": {
                    "adminpass_lvl1": "test",
                    "adminpass_lvl2": "test",
                    "adminpass_lvl3": "test1",
                }
            }
        )

        with pytest.raises(AlfredError) as excinfo:
            exp.create_session("sid1", config, secrets, **urlargs)

        msg = str(excinfo.value)
        assert "Passwords must be unique to a level" in msg


class TestUsageRaw:
    def test_admin(self, tmp_path):
        exp = al.Experiment()
        exp.admin += al.Page(name="admin_test")

        config = ExperimentConfig(tmp_path)
        secrets = ExperimentSecrets(tmp_path)
        secrets.read_dict(
            {
                "general": {
                    "adminpass_lvl1": "test1",
                    "adminpass_lvl2": "test2",
                    "adminpass_lvl3": "test3",
                }
            }
        )
        urlargs = {"admin": "true"}

        session = exp.create_session("sid1", config, secrets, **urlargs)
        assert session.admin_mode


@pytest.mark.skip("Should be run manually")
class TestUsageOnSever:
    def test_admin_exp(self, client):
        rv = client.get("/start?admin=true", follow_redirects=True)
        assert b"Admin" in rv.data

    def test_spectator(self, client):
        rv = client.get("/start?admin=true", follow_redirects=True)
        rv = forward(client, data={"pw": "test1"})
        assert b"Spectator" in rv.data
        assert b"Bitte geben Sie etwas ein." not in rv.data
        assert b"Weiter" not in rv.data

        rv = forward(client)
        assert b"There's nothing here" in rv.data

    def test_operator(self, client):
        rv = client.get("/start?admin=true", follow_redirects=True)

        rv = forward(client, data={"pw": "test2"})
        assert b"Spectator" in rv.data
        assert b"Weiter" in rv.data

        rv = forward(client)
        assert b"Operator" in rv.data
        assert b"Weiter" not in rv.data

        rv = forward(client)
        assert b"There's nothing here" in rv.data

    def test_manager(self, client):
        rv = client.get("/start?admin=true", follow_redirects=True)

        rv = forward(client, data={"pw": "test3"})
        assert b"Spectator" in rv.data
        assert b"Weiter" in rv.data

        rv = forward(client)
        assert b"Operator" in rv.data
        assert b"Weiter" in rv.data

        rv = forward(client)
        assert b"Manager" in rv.data
        assert b"Weiter" not in rv.data

        rv = forward(client)
        assert b"There's nothing here" in rv.data
