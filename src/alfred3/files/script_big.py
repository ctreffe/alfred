"""
You can run the experiment by executing the following command in a 
terminal from inside the experiment directory::

    $ alfred3 run

Refer to the alfred documentation for more guidance.
"""

import alfred3 as al
exp = al.Experiment()


@exp.setup
def setup(exp):
    randomizer = al.ListRandomizer.balanced("a", "b", n=10, exp=exp)
    exp.condition = randomizer.get_condition()

    exp.session_timeout = 60 * 60 * 2 # 2 hours timeout


@exp.member
class HelloWorld(al.Page):
    title = "Hello, world!"
    
    def on_exp_access(self):
        self += al.Text("Welcome to alfred3!", align="center")


if __name__ == "__main__":
    exp.run(open_browser=True)