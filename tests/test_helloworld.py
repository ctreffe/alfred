"""
High-level unit tests that ensure that starting, moving, finishing and
data saving work.
"""

import pytest
from dotenv import load_dotenv

from alfred3.testutil import clear_db, forward, get_alfred_docs, get_app, get_json

load_dotenv()


@pytest.fixture
def client(tmp_path):
    script = "tests/res/script-hello_world.py"
    secrets = "tests/res/secrets-default.conf"

    app = get_app(tmp_path, script_path=script, secrets_path=secrets)

    with app.test_client() as client:
        yield client

    clear_db()


@pytest.mark.skip
class TestHelloWorld:
    def test_start(self, client):
        rv = client.get("/start", follow_redirects=True)
        assert b"Page 1" in rv.data

    def test_finish(self, client):
        client.get("/start", follow_redirects=True)
        rv = forward(client)
        assert b"Experiment beendet" in rv.data

    def test_local_saving(self, client, tmp_path):
        client.get("/start", follow_redirects=True)
        forward(client)

        contents = [p.name for p in tmp_path.iterdir()]

        assert "save" in contents

        data = next(get_json(tmp_path / "save" / "exp"))
        assert data is not None
        assert "exp_id" in data

    def test_local_data_export(self, client, tmp_path):
        client.get("/start", follow_redirects=True)
        forward(client)

        contents = [p.name for p in tmp_path.iterdir()]
        assert "data" in contents

        data_contents = [p.name for p in tmp_path.joinpath("data").iterdir()]

        assert "exp_data.csv" in data_contents
        assert "codebook_0.1.csv" in data_contents
        assert "move_history.csv" in data_contents

    def test_mongo_saving(self, client):
        client.get("/start", follow_redirects=True)
        forward(client)

        data = next(get_alfred_docs())
        assert data is not None
        assert "exp_id" in data
