"""Runs an alfred3 experiment residing in a `script.py` in the working
directory.
"""

from alfred3.run import run_experiment
from alfred3.alfredlog import init_logging

if __name__ == "__main__":
    init_logging("alfred3")
    run_experiment()
