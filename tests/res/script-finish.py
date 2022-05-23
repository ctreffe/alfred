import alfred3 as al

exp = al.Experiment()


@exp.member
class First(al.Page):
    def on_exp_access(self):
        self += al.TextEntry(name="el1")

    def on_first_hide(self):
        self.exp.finish()


@exp.member
class Second(al.Page):
    def on_exp_access(self):
        self += al.TextEntry(name="el2")
