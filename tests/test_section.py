import random

import pytest

import alfred3 as al
from alfred3.testutil import clear_db, get_exp_session


@pytest.fixture
def exp_shuffle(tmp_path):
    script = "tests/res/script-shuffle.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)

    yield exp

    clear_db()


@pytest.fixture
def exp(tmp_path):
    script = "tests/res/script-hello_world.py"
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

        page_names = [p.name for p in exp.Main.members.values()]
        assert page_names == ["p02", "p03", "p01"]

        exp.forward()
        exp.forward()

        pages = list(exp.Main.members.values())
        assert pages[0].input_elements["task_01"]
        assert pages[1].input_elements["task_02"]
        assert pages[2].input_elements["task_03"]

    def test_shuffle2(self, exp_shuffle):
        exp = exp_shuffle

        assert exp.movement_manager.first_page.name == "p01"
        random.seed(123123)
        exp.start()

        page_names = [p.name for p in exp.Main.members.values()]
        assert page_names == ["p03", "p02", "p01"]

        exp.forward()
        exp.forward()

        pages = list(exp.Main.members.values())
        assert pages[0].input_elements["task_01"]
        assert pages[1].input_elements["task_02"]
        assert pages[2].input_elements["task_03"]

    def test_first_page(self):
        main = al.Section(name="main")

        main += al.Page(name="p1")
        main += al.Page(name="p2")

        assert main.p1 is main.first_page
        assert main.p2 is not main.first_page

    def test_last_page(self):
        main = al.Section(name="main")

        main += al.Page(name="p1")
        main += al.Page(name="p2")

        assert main.p1 is not main.last_page
        assert main.p2 is main.last_page


class TestHideOnForwardSection:
    def test_jump_backwards(self, exp):
        main = al.Section(name="main")
        smart = al.HideOnForwardSection(name="smart")

        main += al.Page(name="first")
        smart += al.Page(name="second")
        smart += al.Page(name="third")

        exp += main
        exp += smart

        exp.start()
        exp.forward()
        assert exp.current_page.name == "first"
        exp.forward()
        assert exp.current_page.name == "second"
        exp.backward()
        assert exp.current_page.name == "first"
        exp.forward()
        exp.forward()
        assert exp.current_page.name == "third"
        exp.backward()
        assert exp.current_page.name == "first"
        exp.forward()
        assert exp.current_page.name == "third"

        assert exp.second.is_closed
