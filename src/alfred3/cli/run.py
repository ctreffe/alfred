import click
from pathlib import Path
from alfred3.run import ExperimentRunner

@click.command()
@click.option(
    "-a/-m",
    "--auto-open/--manual-open",
    default=None,
    help="If this flag is set to '-a', the experiment will open a browser window automatically. [default: '-a']",
)
@click.option("--path", default=Path.cwd())
@click.option(
    "-debug/-production",
    "--debug/--production",
    default=False,
    help="If this flag is set to to '-debug', the alfred experiment will start in debug mode. [default: '-production']",
)
@click.option(
    "-test/-production",
    "--test/--production",
    default=False,
    help="If this flag is set to to '-test', the alfred experiment will start in test mode. [default: '-production']",
)
def run(path, auto_open, debug, test):
    runner = ExperimentRunner(path)
    runner.auto_run(open_browser=auto_open, debug=debug, test=test)