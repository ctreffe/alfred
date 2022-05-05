"""
Provides a command line command for running a local alfred3 experiment.

Run an alfred3 experiment from the terminal by changing to the experiment
directory and running::

    $ alfred3 run

You can access the help for this command directly in the terminal by
executing::

    $ alfred3 run --help

The current version offers the following options::

    Usage: alfred3 run [OPTIONS]

    Options:
    -a, --auto-open / -m, --manual-open
                                    If this flag is set to '-a', the experiment
                                    will open a browser window automatically.
                                    [default: '-a']

    --path TEXT                     Path to experiment directory. [default:
                                    current working directory]

    -debug, --debug / -production, --production
                                    If this flag is set to to '-debug', the
                                    alfred experiment will start in debug mode.
                                    [default: '-production']

    -test, --test / -production, --production
                                    If this flag is set to to '-test', the
                                    alfred experiment will start in test mode.
                                    [default: '-production']

    --help                          Show this message and exit.

"""
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
@click.option(
    "--path", 
    default=Path.cwd(),
    help="Path to experiment directory. [default: current working directory]")
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
