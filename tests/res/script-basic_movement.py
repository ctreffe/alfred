import alfred3 as al

exp = al.Experiment()


class Section(al.Section):
    def on_leave(self):
        self.log.info(f"{self.name}: on_leve executed")

    def on_enter(self):
        self.log.info(f"{self.name}: on_enter executed")

    def on_resume(self):
        self.log.info(f"{self.name}: on_resume executed")

    def on_hand_over(self):
        self.log.info(f"{self.name}: on_hand_over executed")

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


exp += Section(name="basic_section")


@exp.member(of_section="basic_section")
class Page1(al.Page):
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


@exp.member(of_section="basic_section")
class Page2(Page1):
    name = "Page2"
    pass
