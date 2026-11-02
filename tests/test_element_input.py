import pytest
from bs4 import BeautifulSoup

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


class TestRangeInput:
    @pytest.mark.parametrize("default", [0, 0.0, 10, None])
    def test_default_rendering(self, exp, default):
        exp.testpage += al.RangeInput(name="slider", default=default)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        slider = exp.testpage.slider
        control = BeautifulSoup(slider.web_widget, "html.parser").select_one(
            'input[type="range"]'
        )

        assert slider.input == default
        if default is None:
            assert "value" not in control.attrs
        else:
            assert float(control["value"]) == default
            assert slider.data["slider"]["value"] == default

    @pytest.mark.parametrize("value", [0, 0.0, "0"])
    def test_zero_overrides_nonzero_default(self, exp, value):
        exp.testpage += al.RangeInput(name="slider", default=10, force_input=True)

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"slider": value})
        slider = exp.testpage.slider
        control = BeautifulSoup(slider.web_widget, "html.parser").select_one(
            'input[type="range"]'
        )

        assert slider.validate_data()
        assert float(control["value"]) == 0
        assert exp.values["slider"] == 0.0

    @pytest.mark.parametrize("value", [None, ""])
    def test_empty_input_stays_missing(self, value):
        slider = al.RangeInput(name="slider", default=10)
        slider.input = value

        assert slider.input is None


class TestMultipleChoiceHints:
    @pytest.mark.parametrize(
        "element", [al.MultipleChoice, al.MultipleChoiceButtons, al.MultipleChoiceBar]
    )
    @pytest.mark.parametrize("count", [1, 4])
    def test_default_hint_rejects_invalid_count(self, exp, element, count):
        exp.testpage += element(
            "One", "Two", "Three", "Four", name="multi", min=2, max=3
        )

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data(
            {f"multi_choice{i}": str(i) for i in range(1, count + 1)}
        )
        multi = exp.testpage.multi

        assert not multi.validate_data()
        hint = multi.select_hint
        assert "{min}" not in hint and "{max}" not in hint
        assert "2" in hint and "3" in hint
        assert hint in next(multi.corrective_hints).msg
        assert sum(exp.values["multi"].values()) == count

    @pytest.mark.parametrize("custom_config", [False, True])
    def test_custom_hint_precedence(self, exp, custom_config):
        exp.config.read_dict(
            {"hints": {"select_MultipleChoice": "Select {min} to {max} choices."}}
        )
        options = {} if custom_config else {"select_hint": "Choose two or three."}
        exp.testpage += al.MultipleChoice(
            "One", "Two", "Three", name="multi", min=2, max=3, **options
        )

        exp.start()
        exp.forward()
        exp.testpage.prepare_web_widget()
        exp.testpage._set_data({"multi_choice1": "1"})
        multi = exp.testpage.multi

        assert not multi.validate_data()
        expected = "Select 2 to 3 choices." if custom_config else "Choose two or three."
        assert multi.select_hint == expected
