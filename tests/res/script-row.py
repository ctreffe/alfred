import alfred3 as al

exp = al.Experiment()


class Text(al.Text):
    prepare_web_widget_executed = False
    callcount = 0

    def prepare_web_widget(self):
        self.prepare_web_widget_executed = True
        self.callcount += 1


@exp.member
class P1(al.Page):
    title = "Page 1"

    def on_exp_access(self):
        self += Text(name="p1_text_standalone")
        self += al.Row(Text(name="p1text_row"))


@exp.member
class P2(al.Page):
    title = "Page 2"

    def on_exp_access(self):
        self += Text(name="p2_text_standalone")
        self += al.Row(Text(name="p2_text_row"))
