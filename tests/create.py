"""
Convenience script for creating test experiments

Execute like this from the main alfred3 directory::

    $ python3 tests/create.py

Or like this, from within tests/::

    $ python3 -m create

"""

from pathlib import Path
from datetime import datetime
from subprocess import run
import click

@click.command()
@click.option("-name", prompt="Enter a name for the test experiment", help="Name for test experiment")
def testexp(name):
    timestamp = datetime.today().strftime("%Y-%m-%d-%H%M")
    dirname = timestamp + "-" + name
    
    path = Path.cwd() / "exp" / dirname
    path = path.resolve()

    path.mkdir(parents=True)

    run(["alfred3", "template", f"--path={str(path)}", ])


if __name__ == "__main__":
    testexp()