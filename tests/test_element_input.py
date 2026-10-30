import pytest

import alfred3 as al
import alfred3.element.input as inp
from alfred3.testutil import clear_db, get_exp_session


@pytest.fixture
def exp(tmp_path):
    script = "tests/res/script-hello_world.py"
    secrets = "tests/res/secrets-default.conf"
    exp = get_exp_session(tmp_path, script_path=script, secrets_path=secrets)

    exp += al.Page(title="Testpage", name="testpage")

    yield exp

    clear_db()


class TestPasswordEntry:
    def test_nomatch(self, exp):
        exp.testpage += inp.PasswordEntry("rightpass", name="pentry")
        exp.testpage._set_data({"pentry": "wrongpass"})

        assert not exp.testpage.pentry.validate_data()

    def test_match(self, exp):
        exp.testpage += inp.PasswordEntry("rightpass", name="pentry")
        exp.testpage._set_data({"pentry": "rightpass"})

        assert exp.testpage.pentry.validate_data()

    def test_list_of_passwords(self, exp):
        with pytest.raises(ValueError) as excinfo:
            inp.PasswordEntry(["rightpass1", "rightpass2"], name="pentry")

        assert "must be a string" in str(excinfo.value) and "pentry" in str(
            excinfo.value
        )


class TestMultiplePasswordEntry:
    def test_singlepass(self, exp):
        with pytest.raises(ValueError) as excinfo:
            inp.MultiplePasswordEntry("rightpass", name="pentry")
        exp.testpage._set_data({"pentry": "wrongpass"})

        assert "must be a list or a tuple" in str(excinfo.value) and "pentry" in str(
            excinfo.value
        )

    def test_match1(self, exp):
        exp.testpage += inp.MultiplePasswordEntry(
            ["rightpass1", "rightpass2"], name="pentry"
        )
        exp.testpage._set_data({"pentry": "rightpass1"})

        assert exp.testpage.pentry.validate_data()

    def test_match2(self, exp):
        exp.testpage += inp.MultiplePasswordEntry(
            ["rightpass1", "rightpass2"], name="pentry"
        )
        exp.testpage._set_data({"pentry": "rightpass2"})

        assert exp.testpage.pentry.validate_data()


class TestSingleChoiceElement:
    def test_data(self, exp):
        exp.testpage += al.SingleChoice("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test": 2})

        assert exp.values["test"] == 2
        assert exp.testpage.test.choice_labels[2 - 1] == "b"


class TestSingleChoiceButtons:
    def test_data(self, exp):
        exp.testpage += al.SingleChoiceButtons("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test": 2})

        assert exp.values["test"] == 2


class TestSubmittingButtons:
    def test_data(self, exp):
        exp.testpage += al.SubmittingButtons("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test": 2})

        assert exp.values["test"] == 2


class TestSingleChoiceBar:
    def test_data(self, exp):
        exp.testpage += al.SingleChoiceBar("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test": 2})

        assert exp.values["test"] == 2


class TestSingleChoiceList:
    def test_data(self, exp):
        exp.testpage += al.SingleChoiceList("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test": "a"})

        assert exp.values["test"] == "a"


class TestMultipleChoiceElement:
    def test_data(self, exp):
        exp.testpage += al.MultipleChoice("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test_choice1": "1"})

        assert exp.values["test"]["choice1"] is True

    def test_select_hint_default_message(self, exp):
        # Regression test for #308: with no custom select_hint, an
        # under/over-selection used to raise configparser.NoOptionError
        # because alfred.conf shipped the key under the name
        # "select_MultipleChoiceElement" while the code looked up
        # "select_MultipleChoice".
        exp.testpage += al.MultipleChoice(
            "a", "b", "c", "d", name="test", min=2, max=3, force_input=True
        )

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test_choice1": "1"})

        assert exp.testpage.test.validate_data() is False
        assert "2" in exp.testpage.test.select_hint
        assert "3" in exp.testpage.test.select_hint


class TestRangeInput:
    def test_default_zero_renders_as_zero(self, exp):
        # Regression test for #307: a falsy default (e.g. 0) used to be
        # dropped by the template's truthiness check ({% elif default %}),
        # so the rendered <input> had no value attribute and browsers
        # fell back to the slider's midpoint instead of 0.
        exp.testpage += inp.RangeInput(min=0, max=100, default=0, name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()

        html = exp.testpage.test.render_inner_html(exp.testpage.test.template_data)
        assert 'value="0"' in html

    def test_nonzero_default_still_renders(self, exp):
        exp.testpage += inp.RangeInput(min=0, max=100, default=10, name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()

        html = exp.testpage.test.render_inner_html(exp.testpage.test.template_data)
        assert 'value="10"' in html


class TestMultipleButtons:
    def test_data(self, exp):
        exp.testpage += al.MultipleChoiceButtons("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test_choice1": "1"})

        assert exp.values["test"]["choice1"] is True


class TestMultipleChoiceBar:
    def test_data(self, exp):
        exp.testpage += al.MultipleChoiceBar("a", "b", name="test")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"test_choice1": "1"})

        assert exp.values["test"]["choice1"] is True


class TestEmailEntry:
    def test_correct_email(self, exp):
        exp.testpage += al.EmailEntry(name="email")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"email": "abc@test.de"})

        assert exp.testpage.email.validate_data()

    def test_incorrect_email(self, exp):
        exp.testpage += al.EmailEntry(name="email")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"email": "abctest.de"})

        assert not exp.testpage.email.validate_data()


class TestMatchEntry:
    def test_match(self, exp):
        exp.testpage += al.MatchEntry(pattern="this", name="match")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"match": "this"})

        assert exp.testpage.match.validate_data()

    def test_no_match(self, exp):
        exp.testpage += al.MatchEntry(pattern="this", name="match")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"match": "not this"})

        assert not exp.testpage.match.validate_data()


class TestNumberEntry:
    def test_integer(self, exp):
        exp.testpage += al.NumberEntry(name="number")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1"})

        assert exp.testpage.number.validate_data()
        assert exp.testpage.number.input == 1
        assert exp.values.get("number") == 1

    def test_decimal_point(self, exp):
        exp.testpage += al.NumberEntry(name="number", ndecimals=1)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1.1"})

        assert exp.testpage.number.validate_data()
        assert exp.testpage.number.input == 1.1
        assert exp.values.get("number") == 1.1

    def test_decimal_comma(self, exp):
        exp.testpage += al.NumberEntry(name="number", ndecimals=1)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1,1"})

        assert exp.testpage.number.validate_data()
        assert exp.testpage.number.input == 1.1
        assert exp.values.get("number") == 1.1

    def test_string(self, exp):
        exp.testpage += al.NumberEntry(name="number", ndecimals=1)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "test"})

        assert not exp.testpage.number.validate_data()

    def test_min(self, exp):
        exp.testpage += al.NumberEntry(name="number", min=2)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1"})

        assert not exp.testpage.number.validate_data()

    def test_max(self, exp):
        exp.testpage += al.NumberEntry(name="number", max=2)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "3"})

        assert not exp.testpage.number.validate_data()

    def test_ndecimals(self, exp):
        exp.testpage += al.NumberEntry(name="number", ndecimals=2)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1,12"})

        assert exp.testpage.number.validate_data()
        assert exp.testpage.number.input == 1.12
        assert exp.values.get("number") == 1.12

    def test_ndecimals_fail(self, exp):
        exp.testpage += al.NumberEntry(name="number", ndecimals=2)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1,123"})

        assert not exp.testpage.number.validate_data()

    def test_decimal_sign_fail(self, exp):
        exp.testpage += al.NumberEntry(name="number", decimal_signs=";")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1,12"})

        assert not exp.testpage.number.validate_data()

    def test_decimal_sign_semicolon_fail(self, exp):
        # validation fails, because ndecimals=0 default
        exp.testpage += al.NumberEntry(name="number", decimal_signs=";")

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1;12"})

        assert not exp.testpage.number.validate_data()

    def test_decimal_sign_semicolon(self, exp):
        # validation fails, because ndecimals=0 default
        exp.testpage += al.NumberEntry(name="number", decimal_signs=";", ndecimals=1)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"number": "1;1"})

        assert exp.testpage.number.validate_data()
        assert exp.testpage.number.input == 1.1
        assert exp.values.get("number") == 1.1


# class TestMultipleChoiceList:
#     def test_data_select_one(self, exp):
#         exp.testpage += al.MultipleChoiceList("a", "b", name="test")

#         exp.start()
#         exp.forward()
#         exp.testpage.prepare_web_widget()
#         exp.testpage._set_data({f"test": ["1"]})

#         assert exp.values["test"]["choice1"] == True

#     def test_data_select_multiple(self, exp):
#         exp.testpage += al.MultipleChoiceList("a", "b", name="test")

#         exp.start()
#         exp.forward()
#         exp.testpage.prepare_web_widget()
#         exp.testpage._set_data({f"test": ["1", "2"]})

#         assert exp.values["test"]["choice1"] == True
#         assert exp.values["test"]["choice2"] == True
