import click
from pathlib import Path
from alfred3.run import ExperimentRunner

@click.command()
@click.option(
    "-a/-m",
    "--auto-open/--manual-open",
    default=True,
    help="If this flag is set to '-a', the experiment will open a browser window automatically. [default: '-a']",
)
@click.option("--path", default=Path.cwd())
@click.option(
    "-debug/-production",
    "--debug/--production",
    default=False,
    help="If this flag is set to to '-debug', the alfred experiment will start in flask's debug mode. [default: '-production']",
)
def run(path, auto_open, debug):
    runner = ExperimentRunner(path)
    runner.auto_run(open_browser=auto_open, debug=debug)