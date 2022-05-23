import alfred3 as al
from alfred3 import admin

exp = al.Experiment()


class MySpectatorPage(admin.SpectatorPage):
    def on_exp_access(self):
        self += al.Text("My spectator page")


class MyOperatorPage(admin.OperatorPage):
    def on_exp_access(self):
        self += al.Text("My operator page")


class MyManagerPage(admin.ManagerPage):
    def on_exp_access(self):
        self += al.Text("My manager page")


exp.admin += MySpectatorPage(title="Spectator", name="spectator")
exp.admin += MyOperatorPage(title="Operator", name="operator")
exp.admin += MyManagerPage(title="Manager", name="manager")

exp += al.Page(title="normal", name="normal")

if __name__ == "__main__":
    exp.run(open_browser=False)
