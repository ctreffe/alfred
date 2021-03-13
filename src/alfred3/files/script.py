"""
This is a minimal, 'Hello, world!' alfred experiment.

You can run the experiment by executing the following command in a 
terminal from inside the experiment directory::

    $ alfred3 run

Refer to the alfred documentation for more guidance.
"""

import alfred3 as al
exp = al.Experiment()

exp += al.Page(title="Hello, world!", name="hello_world")


if __name__ == "__main__":
    exp.run()