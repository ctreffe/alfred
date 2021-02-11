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