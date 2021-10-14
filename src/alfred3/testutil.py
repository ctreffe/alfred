"""
Provides utility functionality for testing.
"""

import os
import json
from pathlib import Path
from uuid import uuid4

from alfred3.run import ExperimentRunner
from alfred3.config import ExperimentConfig, ExperimentSecrets

from bs4 import BeautifulSoup
from pymongo import MongoClient
from thesmuggler import smuggle


def prepare_script(tmp_path, script_path: str):
    """
    Reads a script.py and writes it into the directory *tmp_path*.
    This is intended for use with the tmp_path fixture.
    """
    script = Path(script_path).read_text(encoding="utf-8")
    tmp_script = Path(tmp_path) / "script.py"
    tmp_script.write_text(script)


def prepare_config(tmp_path, config_path: str) -> str:
    """
    Reads a config.conf and writes it into the directory *tmp_path*.
    This is intended for use with the tmp_path fixture.

    Does nothing if config_path is an empty string.
    """
    if not config_path:
        return ExperimentConfig(expdir=tmp_path)
    config = Path(config_path).read_text(encoding="utf-8")
    tmp_config = Path(tmp_path) / "config.conf"
    tmp_config.write_text(config)

    return ExperimentConfig(expir=tmp_path, config_objects=[config])


def prepare_secrets(tmp_path, secrets_path: str) -> str:
    """
    Writes a secrets.conf for a mongo saving agent into the *tmp_path*.
    This is intended for use with the tmp_path fixture.
    """
    if not secrets_path:
        return
    
    SECRETS = Path(secrets_path).read_text(encoding="utf-8")
    secrets = SECRETS.format(
        host=os.getenv("MONGODB_HOST"),
        port=os.getenv("MONGODB_PORT"),
        db=os.getenv("MONGODB_DATABASE"),
        usr=os.getenv("MONGODB_USERNAME"),
        pw=os.getenv("MONGODB_PASSWORD"),
        col=os.getenv("MONGODB_COLLECTION"),
        misc_collection=os.getenv("MONGODB_MISC_COLLECTION"),
    )

    tmp_secrets = Path(tmp_path) / "secrets.conf"
    tmp_secrets.write_text(secrets)

    return ExperimentSecrets(expdir=tmp_path, config_objects=[secrets])

def get_db():
    """
    Returns the mongoDB database specified via credentials in .env.
    """
    mc = MongoClient(
        host=os.getenv("MONGODB_HOST"),
        port=int(os.getenv("MONGODB_PORT")),
        username=os.getenv("MONGODB_USERNAME"),
        password=os.getenv("MONGODB_PASSWORD"),
        )
    db = os.getenv("MONGODB_DATABASE")
    return mc[db]

def get_alfred_collection():
    """
    Returns the alfred mongoDB collection.
    """
    db = get_db()
    col = os.getenv("MONGODB_COLLECTION")
    return db[col]

def get_misc_collection():
    """
    Returns the misc mongoDB collection
    """
    db = get_db()
    col = os.getenv("MONGODB_MISC_COLLECTION")
    return db[col]

def clear_db():
    """
    Deletes all documents in the testing collection of the mongoDB
    accessed through environment variables.

    Intended for cleanup after testing.
    """
    col = get_alfred_collection()
    misc_col = get_misc_collection()
    delete_count_col = col.delete_many({}).deleted_count
    delete_count_misc = misc_col.delete_many({}).deleted_count
    print(
        f"Deleted {delete_count_col} documents in collection '{col}'"
        f"and {delete_count_misc} in collection '{misc_col}' during"
        "cleanup."
    )


def get_exp_session(
    tmp_path,
    script_path: str,
    config_path: str = "",
    secrets_path: str = "tests/res/secrets-default.conf",
    sid: str = None,
    **urlargs
):
    """
    Returns an alfred3.experiment.ExperimentSession object based on the
    given script.py.
    """
    prepare_script(tmp_path, script_path)
    config = prepare_config(tmp_path, config_path)
    secrets = prepare_secrets(tmp_path, secrets_path)

    script = smuggle(tmp_path / "script.py")
    exp = script.exp
    sid = uuid4().hex if sid is None else sid
    
    session = exp.create_session(session_id=sid, config=config, secrets=secrets, **urlargs)
    return session


def get_app(
    tmp_path,
    script_path: str,
    config_path: str = "",
    secrets_path: str = "tests/res/secrets-default.conf",
):
    """
    Returns an alfred3 experiment flask app with a running mongo saving 
    agent, based on the given script. The app is returned in testing mode.
    """
    prepare_script(tmp_path, script_path)
    prepare_config(tmp_path, config_path)
    prepare_secrets(tmp_path, secrets_path)

    runner = ExperimentRunner(path=tmp_path)
    runner.generate_session_id()
    runner.configure_logging()

    app = runner.create_experiment_app()
    app.config["TESTING"] = True
    return app


def move(client, direction: str, data: dict, **kwargs):
    """
    Conducts a movement on a alfred3 test experiment in the specified 
    direction, i.e. simulates a click on a forward, backward, finish, 
    or jump button.

    Args:
        client: Flask test client app (as returned by *get_app*)
        direction: Movement direction, can be 'forward', 'backward',
            or 'jump>page_name' (replace *page_name* with the name of
            the page that should be jumped to).
        **kwargs: Keyword arguments passed on to the client.post method.
    
    By default, the method follows redirects.

    Returns:
        A return value as returned by the flask test client's methods
        *get* and *post*
    """
    rv = client.get("/experiment")
    bs = BeautifulSoup(rv.data.decode(), "html.parser")
    token = bs.find("input", {"name": "page_token"})
    
    data = data if data is not None else {}

    d = {}
    d["move"] = direction
    d["page_token"] = token.get("value")
    d.update(data)

    if not "follow_redirects" in kwargs:
        kwargs["follow_redirects"] = True

    return client.post("/experiment", data=d, **kwargs)

def forward(client, data: dict = None, **kwargs):
    """Shortcut for a forward move"""
    return move(client, direction="forward", data=data, **kwargs)

def backward(client, data: dict = None, **kwargs):
    """Shortcut for a backward move"""
    return move(client, direction="backward", data=data, **kwargs)

def jump(client, to: str, data: dict = None, **kwargs):
    """Shortcut for a jump"""
    return move(client, direction=f"jump>{to}", data=data, **kwargs)

def first_subpath(path: str) -> Path:
    """
    Returns the first child of the given path.
    """
    return next(path.iterdir(), None)

def get_json(path: str):
    """
    Iterates over all json files in the directory.
    """
    for p in path.iterdir():
        if p.suffix == ".json":
            with open(p, "r", encoding="utf-8") as f:
                yield json.load(f)

def get_alfred_docs():
    """
    Iterates over all documents in the MongoDB alfred collection.
    """
    col = get_alfred_collection()
    return col.find()

def get_misc_docs():
    """
    Iterates over all documents in the MongoDB misc collection.
    """
    col = get_misc_collection()
    return col.find()