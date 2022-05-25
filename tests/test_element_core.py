import pytest
from dotenv import load_dotenv

import alfred3 as al
from alfred3.testutil import clear_db, get_app, get_exp_session

load_dotenv()


@pytest.fixture
def rowexp(tmp_path):
    script = "tests/res/script-row.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)

    exp += al.Page(title="Testpage", name="testpage")

    yield exp

    clear_db()


@pytest.fixture
def client(tmp_path):
    script = "tests/res/script-row.py"
    secrets = "tests/res/secrets-default.conf"

    app = get_app(tmp_path, script_path=script, secrets_path=secrets)

    with app.test_client() as client:
        yield client

    clear_db()


class TestRow:
    def test_prepare_web_widgets(self, rowexp):
        exp = rowexp

        exp.start()
        exp.ui.render("token")

        assert exp.current_page is exp.P1
        assert exp.P1.p1_text_standalone.prepare_web_widget_executed
        assert exp.P1.p1_text_standalone.callcount == 1

        exp.forward()
        exp.ui.render("token")

        assert exp.current_page is exp.P2
        assert exp.P2.p2_text_standalone.prepare_web_widget_executed
        assert exp.P2.p2_text_standalone.callcount == 1
