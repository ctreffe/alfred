import alfred3 as al

exp = al.Experiment()

rivers = ["Themse", "Rhein", "Ems"]


@exp.member
class Main(al.Section):
    shuffle = True

    def on_exp_access(self):
        for item in range(3):
            self += Task(name=f"p{item + 1:02}", vargs={"i": item})


class Task(al.Page):
    def on_first_show(self):
        item = self.vargs.i
        position = self.position_in_section()
        stimulus = rivers[item]

        self.title = f"Task {position}"

        self += al.Text(
            "Please estimate the length of the following river:", align="center"
        )
        self += al.Text(f"**{stimulus}**", font_size="large", align="center")

        self += al.NumberEntry(
            placeholder="Enter a number", suffix="km", name=f"task_{position:02}"
        )
        self += al.Value(stimulus, name=f"item_{position:02}")
