"""
Command line interface for alfred3.

Alfred3 offers some commands for the command line/terminal. You can see 
a list of all available commands by executing the following in a terminal::

    $ alfred3 --help

Then, you can get further help on the specific commands. For example,
to get help on the "run" command, execute::

    $ alfred3 run --help

These are the currently available commands::

    $ alfred3 --help

    Usage: alfred3 [OPTIONS] COMMAND [ARGS]...

    Options:
    --help  Show this message and exit.

    Commands:
    json-to-csv
    run
    template

"""


import click

from .template import template
from .run import run
from .extract import json_to_csv

@click.group()
def cli():
    pass

cli.add_command(template)
cli.add_command(run)
cli.add_command(json_to_csv)