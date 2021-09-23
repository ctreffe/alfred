import alfred3 as al
from alfred3 import admin

exp = al.Experiment()


class MyMonitoringPage(admin.MonitoringPage):

    def on_exp_access(self):
        self += al.Text("My monitoring page")


class MyModeratorPage(admin.ModeratorPage):

    def on_exp_access(self):
        self += al.Text("My moderator page")


class MyManagerPage(admin.ManagerPage):

    def on_exp_access(self):
        self += al.Text("My manager page")

exp.admin += MyMonitoringPage(title="Monitoring", name="monitoring")
exp.admin += MyModeratorPage(title="Moderator", name="moderator")
exp.admin += MyManagerPage(title="Manager", name="manager")

exp += al.Page(title="normal", name="normal")

if __name__ == "__main__":
    exp.run(open_browser=False)