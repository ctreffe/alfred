import logging

import pytest

import alfred3 as al
from alfred3.testutil import clear_db, get_exp_session


@pytest.fixture
def exp(tmp_path):
    script = "tests/res/script-basic_movement.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)
    yield exp
    clear_db()


@pytest.fixture
def blank_exp(tmp_path):
    script = "tests/res/script-blank.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)
    yield exp
    clear_db()


class Section(al.Section):
    def on_enter(self):
        self.log.info(f"{self.name}: on_enter executed")

    def on_resume(self):
        self.log.info(f"{self.name}: on_resume executed")

    def on_hand_over(self):
        self.log.info(f"{self.name}: on_hand_over executed")

    def on_leave(self):
        self.log.info(f"{self.name}: on_leave executed")

    def validate_on_leave(self):
        self.log.info(f"{self.name}: validate_on_leave executed")
        return super().validate_on_leave()

    def validate_on_forward(self):
        self.log.info(f"{self.name}: validate_on_forward executed")
        return super().validate_on_forward()

    def validate_on_backward(self):
        self.log.info(f"{self.name}: validate_on_backward executed")
        return super().validate_on_backward()

    def validate_on_jumpfrom(self):
        self.log.info(f"{self.name}: validate_on_jumpfrom executed")
        return super().validate_on_jumpfrom()

    def validate_on_jumpto(self):
        self.log.info(f"{self.name}: validate_on_jumpto executed")
        return super().validate_on_jumpto()

    def validate_on_move(self):
        self.log.info(f"{self.name}: validate_on_move executed")
        return super().validate_on_move()


class Page(al.Page):
    def on_first_show(self):
        self.log.info(f"{self.name}: on_first_show executed")
        return super().on_first_show()

    def on_each_show(self):
        self.log.info(f"{self.name}: on_each_show executed")
        return super().on_each_show()

    def on_first_hide(self):
        self.log.info(f"{self.name}: on_first_hide executed")
        return super().on_first_hide()

    def on_each_hide(self):
        self.log.info(f"{self.name}: on_each_hide executed")
        return super().on_each_hide()


class TestBasicMovement:
    def test_forward(self, exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page2"
        assert "validate_on_forward" in caplog.text

        exp.movement_manager.move("forward")
        assert exp.finished
        assert exp.current_page is exp.final_page

    def test_backward(self, exp):
        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page2"

        exp.movement_manager.move("backward")
        assert exp.current_page.name == "Page1"

    def test_jump(self, exp):
        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("jump>Page2")
        assert exp.current_page.name == "Page2"

    def test_jump_to_nonexistent_page(self): ...

    def test_page_should_not_be_shown(self, exp, caplog):
        # page with should_be_shown = False should be skipped
        # none of its hooks should run
        exp.Page2.should_be_shown = False

        exp.start()
        assert exp.current_page.name == "Page1"

        exp.forward()
        assert exp.finished
        assert "Page2: on_first_show executed" not in caplog.text
        assert "Page2: on_each_show executed" not in caplog.text
        assert "Page2: on_first_hide executed" not in caplog.text
        assert "Page2: on_each_show executed" not in caplog.text

    def test_skip_on_hiding(self, blank_exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp = blank_exp

        class TestPage(al.Page):
            def on_first_hide(self):
                self.log.info(f"{self.name}: on_first_hide executed")
                self.exp.my_target_test_page.should_be_shown = False

        exp += TestPage(name="test_page")
        exp += al.Page(name="my_target_test_page")

        exp.start()
        assert exp.current_page.name == "test_page"

        exp.forward()
        assert exp.finished
        assert "my_target_test_page: on_first_show executed" not in caplog.text
        assert "my_target_test_page: on_each_show executed" not in caplog.text
        assert "my_target_test_page: on_first_hide executed" not in caplog.text
        assert "my_target_test_page: on_each_show executed" not in caplog.text

    def test_skip_two_pages(self, blank_exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp = blank_exp

        class TestPage(Page):
            def on_exp_access(self):
                self.should_be_shown = False

        exp += Page(name="base_page")
        exp += TestPage(name="test1")
        exp += TestPage(name="test2")

        exp.start()
        assert exp.current_page.name == "base_page"

        exp.forward()
        assert exp.finished

        assert "test1: on_first_show executed" not in caplog.text
        assert "test1: on_each_show executed" not in caplog.text
        assert "test1: on_first_hide executed" not in caplog.text
        assert "test1: on_each_show executed" not in caplog.text

        assert "test2: on_first_show executed" not in caplog.text
        assert "test2: on_each_show executed" not in caplog.text
        assert "test2: on_first_hide executed" not in caplog.text
        assert "test2: on_each_show executed" not in caplog.text


class TestCustomMove:
    def test_custom_move_backward(self, exp):
        class MovePage(al.Page):
            custom_move_has_run = False

            def custom_move(self):
                self.custom_move_has_run = True
                self.exp.backward()

        exp += MovePage(name="custom_move_page")

        exp.start()
        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page2"

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "custom_move_page"

        exp.movement_manager.move("forward")
        assert exp.custom_move_page.custom_move_has_run
        assert exp.current_page.name == "Page2"

    def test_custom_move_jump(self, exp):
        class MovePage(al.Page):
            custom_move_has_run = False

            def custom_move(self):
                self.custom_move_has_run = True
                self.exp.jump("Page1")

        exp += MovePage(name="custom_move_page")

        exp.start()
        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page2"

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "custom_move_page"

        exp.movement_manager.move("forward")
        assert exp.custom_move_page.custom_move_has_run
        assert exp.current_page.name == "Page1"

    def test_custom_move_return(self, exp):
        class MovePage(al.Page):
            custom_move_has_run = False

            def custom_move(self):
                self.custom_move_has_run = True
                return True

        exp += MovePage(name="custom_move_page")

        exp.start()
        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page2"

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "custom_move_page"

        exp.movement_manager.move("forward")
        assert exp.custom_move_page.custom_move_has_run
        assert exp.finished


class TestPermissions:
    def test_allow_foward(self, exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp.basic_section.allow_forward = False

        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page1"
        assert exp.current_page.name in caplog.text
        assert "does not allow movement in direction 'forward'" in caplog.text

    def test_allow_backward(self, exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp.basic_section.allow_backward = False

        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page2"

        exp.movement_manager.move("backward")
        assert exp.current_page.name == "Page2"
        assert exp.current_page.name in caplog.text
        assert "does not allow movement in direction 'backward'" in caplog.text

    def test_allow_backward_to(self, exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp.basic_section.allow_backward = False

        inner = al.Section(name="inner")
        outer = al.Section(name="outer")

        outer += inner
        inner += al.Page(name="inner_page")
        outer += al.Page(name="outer_page")

        exp += outer

        inner.allow_backward = False

        exp.start()
        exp.jump("inner_page")

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "outer_page"

        exp.movement_manager.move("backward")
        assert exp.current_page.name == "outer_page"

        assert "inner_page" in caplog.text
        assert "does not allow movement in direction 'backward'" in caplog.text

    def test_allow_jumpto(self, exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp.basic_section.allow_jumpto = False

        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("jump>Page2")
        assert exp.current_page.name == "Page1"
        assert "Page2" in caplog.text
        assert "cannot be jumped to" in caplog.text

    def test_allow_jumpfrom(self, exp, caplog):
        caplog.set_level(logging.DEBUG)
        exp.basic_section.allow_jumpfrom = False

        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("jump>Page2")
        assert exp.current_page.name == "Page1"
        assert "Page1" in caplog.text
        assert "cannot be jumped from" in caplog.text


class TestOrder:
    def test_permissions(self, exp, caplog):
        # if move is not permitted:
        # validation should not run
        # hooks should not run
        # no move should be recorded
        caplog.set_level(logging.DEBUG)
        exp.basic_section.allow_forward = False

        exp.start()
        assert exp.current_page.name == "Page1"

        nmoves = len(exp.move_history)

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "Page1"
        assert exp.current_page.name in caplog.text
        assert "does not allow movement in direction 'forward'" in caplog.text
        assert "validate" not in caplog.text
        assert "on_each_hide" not in caplog.text
        assert "on_first_hide" not in caplog.text
        assert nmoves == len(exp.move_history)

    def test_validation(self, exp, caplog):
        # if validation fails:
        # hooks should not run
        # no move should be recorded
        caplog.set_level(logging.DEBUG)

        class Page(al.Page):
            def validate(self):
                self.log.info(f"{self.name}: validate executed")
                return False

            def on_first_hide(self):
                self.log.info(f"{self.name}: on_first_hide executed")
                return super().on_first_hide()

            def on_each_hide(self):
                self.log.info(f"{self.name}: on_each_hide executed")
                return super().on_each_hide()

        exp += Page(name="testpage")
        exp.start()

        exp.jump("testpage")
        assert exp.current_page.name == "testpage"
        nmoves = len(exp.move_history)

        exp.movement_manager.move("forward")
        assert exp.current_page.name == "testpage"
        assert "testpage: validate executed" in caplog.text

        assert "testpage: on_each_hide" not in caplog.text
        assert "testpage: on_first_hide" not in caplog.text
        assert nmoves == len(exp.move_history)

    def test_on_hiding(self, blank_exp, caplog):
        # on_hiding...
        # ... should run before leaving, handing over, resuming, entering sections
        # ... should run before on_showing of the next page
        caplog.set_level(logging.DEBUG)

        exp = blank_exp

        order = []

        class TestSection(al.Section):
            name = "test_section"

            def on_leave(self):
                order.append(self.name)

        class TestPage(al.Page):
            name = "test_page"

            def on_first_hide(self):
                order.append(self.name)

        sec = TestSection()
        sec += TestPage()
        exp += sec

        exp.start()
        exp.forward()

        assert order == ["test_page", "test_section"]


class TestAddingPages:
    def test_add_page_on_hiding_to_current_section(self, exp, caplog):
        # inserting a page directly after the current one in a forward
        # move should lead to a move to the added page
        caplog.set_level(logging.DEBUG)

        class Page(al.Page):
            def on_first_hide(self):
                self.log.info(f"{self.name}: on_first_hide executed")
                self.section += al.Page(name="added_page")
                return super().on_first_hide()

        exp += Page(name="testpage")
        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("jump>testpage")
        assert exp.current_page.name == "testpage"

        exp.movement_manager.move("forward")

        assert "testpage: on_first_hide" in caplog.text
        assert exp.current_page.name == "added_page"

    def test_add_page_on_hiding_to_exp(self, exp, caplog):
        # inserting a page directly after the current one in a forward
        # move should lead to a move to the added page
        caplog.set_level(logging.DEBUG)

        class Page(al.Page):
            def on_first_hide(self):
                self.log.info(f"{self.name}: on_first_hide executed")
                self.exp += al.Page(name="added_page")
                return super().on_first_hide()

        exp += Page(name="testpage")
        exp.start()
        assert exp.current_page.name == "Page1"

        exp.movement_manager.move("jump>testpage")
        assert exp.current_page.name == "testpage"

        exp.movement_manager.move("forward")

        assert "testpage: on_first_hide" in caplog.text
        assert exp.current_page.name == "added_page"

    # def test_add_page_to_exp_on_leave(self, blank_exp, caplog):
    #     caplog.set_level(logging.DEBUG)
    #     exp = blank_exp

    #     class TestSection(Section):
    #         name = "test_section"

    #         def on_exp_access(self):
    #             self += al.Page(name="base_page")

    #         def on_leave(self):
    #             super().on_leave()
    #             self.exp += al.Page(name="test_page")

    #     exp += TestSection()

    #     exp.start()
    #     assert exp.current_page.name == "base_page"

    #     exp.forward()
    #     assert exp.finished
    #     assert exp.current_page is exp.final_page

    # def test_add_page_on_enter_to_empty_section(self, blank_exp, caplog):
    #     caplog.set_level(logging.DEBUG)
    #     exp = blank_exp

    #     class TestSection(Section):
    #         name = "test_section"

    #         def on_enter(self):
    #             self += al.Page(name="test_page")

    #     exp += al.Page(name="base_page")
    #     exp += TestSection()

    #     exp.start()
    #     assert exp.current_page.name == "base_page"

    #     exp.forward()
    #     assert exp.current_page.name == "test_page"


class TestBasicSectionMovement:
    def test_enter(self, blank_exp, caplog):
        exp = blank_exp
        caplog.set_level(logging.DEBUG)

        exp += Section(name="s1")
        exp += Section(name="s2")
        exp.s1 += Page(name="p1")
        exp.s2 += Page(name="p2")

        exp.start()
        assert exp.current_page.name == "p1"
        assert "s1: on_enter" in caplog.text
        assert "s2: on_enter" not in caplog.text

        exp.forward()
        assert exp.current_page.name == "p2"
        assert "s2: on_enter" in caplog.text

    def test_leave(self, blank_exp, caplog):
        exp = blank_exp
        caplog.set_level(logging.DEBUG)

        exp += Section(name="s1")
        exp += Section(name="s2")
        exp.s1 += Page(name="p1")
        exp.s2 += Page(name="p2")

        exp.start()
        assert exp.current_page.name == "p1"

        exp.forward()
        assert exp.current_page.name == "p2"
        assert "s1: on_leave" in caplog.text
        assert "s1: validate_on_leave" in caplog.text
        assert "s2: on_leave" not in caplog.text
        assert "s2: validate_on_leave" not in caplog.text

        exp.forward()
        assert exp.finished
        assert "s2: on_leave" in caplog.text


class TestNestedMovement:
    def test_hand_over1(self, blank_exp, caplog):
        exp = blank_exp
        caplog.set_level(logging.DEBUG)

        parent = Section(name="parent_section")
        parent += Page(name="parent_page")

        child = Section(name="child_section")
        child += Page(name="child_page")

        parent += child
        exp += parent

        exp.start()

        assert "parent_section: on_enter" in caplog.text
        assert "parent_section: on_hand_over" not in caplog.text
        assert "parent_section: on_leave" not in caplog.text
        assert "child_section: on_enter" not in caplog.text

        exp.forward()
        assert exp.current_page.name == "child_page"
        assert "parent_section: on_hand_over" in caplog.text
        assert "child_section: on_enter" in caplog.text
        assert "parent_section: on_leave" not in caplog.text
        assert "parent_section: validate_on_leave" not in caplog.text

        exp.forward()
        assert "parent_section: on_resume" not in caplog.text
        assert "child_section: on_leave" in caplog.text
        assert "parent_section: on_leave" in caplog.text

    def test_hand_over2(self, blank_exp, caplog):
        exp = blank_exp
        caplog.set_level(logging.DEBUG)

        parent = Section(name="parent_section")

        child = Section(name="child_section")
        child += Page(name="child_page")

        parent += child
        parent += Page(name="parent_page")
        exp += parent

        exp.start()
        assert exp.current_page.name == "child_page"
        assert "parent_section: on_enter" in caplog.text
        assert "parent_section: on_hand_over" in caplog.text
        assert "child_section: on_enter" in caplog.text
        assert "parent_section: on_leave" not in caplog.text

        exp.forward()
        assert "parent_section: on_resume" in caplog.text
        assert "child_section: on_leave" in caplog.text
        assert "parent_section: on_leave" not in caplog.text

        exp.forward()
        assert "parent_section: on_leave" in caplog.text
