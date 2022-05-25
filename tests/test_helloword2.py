import threading

import pytest
from dotenv import load_dotenv
from flask import Blueprint, request
from selenium import webdriver

from alfred3.testutil import get_app

load_dotenv()


testing = Blueprint("test", __name__)


@testing.route("/stop")
def stop():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Shutting down server..."


@pytest.fixture
def driver():
    chrome = webdriver.Chrome()
    yield chrome
    chrome.get("http://localhost:5000/stop")
    chrome.close()


@pytest.fixture
def running_app(tmp_path):
    script = "tests/res/script-hello_world.py"
    secrets = "tests/res/secrets-default.conf"

    app = get_app(tmp_path, script_path=script, secrets_path=secrets)
    app.register_blueprint(testing)
    t = threading.Thread(target=app.run, kwargs={"port": 5000, "use_reloader": False})
    t.start()
    yield app


# def test_one(running_app, driver, tmp_path):
#     driver.get("http://localhost:5000/start")
#     form = driver.find_element_by_id("form")
#     form.submit()
#     time.sleep(1)
#     assert tmp_path.joinpath("save") in list(tmp_path.iterdir())
