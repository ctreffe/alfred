"""
Convenience script for creating test experiments.

Execute from /tests/::

    $ python3 create.py

Or like this::

    $ python3 -m create

"""

from datetime import datetime
from pathlib import Path
from subprocess import run

import click


@click.command()
@click.option(
    "-name",
    prompt="Enter a name for the test experiment",
    help="Name for test experiment",
)
def testexp(name):
    timestamp = datetime.today().strftime("%Y%m%d%H%M")
    dirname = timestamp + "-" + name

    path = Path.cwd() / "exp" / dirname
    path = path.resolve()

    path.mkdir(parents=True)

    run(
        [
            "alfred3",
            "template",
            f"--path={str(path)}",
        ]
    )

    run(["code", path / "script.py"])


if __name__ == "__main__":
    testexp()
