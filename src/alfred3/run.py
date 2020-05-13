# -*- coding: utf-8 -*-
"""Run an alfred experiment.

You can either use the command line interface via ``python3 -m alfred3.run`` from within your experiment directory, or import the `run_experiment` function into your own `run.py` and run it from there.

Example for importing and running the `run_experiment` function:

.. code-block:: python

    from alfred3.run import run_experiment

    if __name__ == "__main__":
        run_experiment()

"""

import importlib
import sys
import webbrowser
import os

from pathlib import Path

from alfred3.helpmates import socket_checker, ChromeKiosk, localserver
from alfred3 import alfredlog
from alfred3 import settings

def load(name: str, location: str):
    """Import a Python module from a specific location.

    Arguments:
        name: Full filename of the module (including file extension)
        location: Full filepath to the module (including file)
    """

    spec = importlib.util.spec_from_file_location(name, location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def run_experiment(path: str=None):
    """Run an alfred3 experiment.

    Note that, when using this function with the ``python -m alfred3.run`` command line command, the current working directory **must** be the experiment directory containing the `script.py` you want to run. Otherwise, alfred3 cannot properly parse your custom `config.conf`.

    Arguments:
        path: Path to the experiment directory in which to look for a script.py. If none is provided, the parent directory of the running file will be used by default.
    """

    alfredlog.init_logging('alfred3')
    logger = alfredlog.getLogger("alfred3")

    # check for correct experiment type
    if not settings.experiment.type == "web":
        raise RuntimeError("Experiment type must be 'web'.")

    # set paths to script.py and config.conf and check their existence
    executing_dir = Path(sys.argv[0]).parent
    expdir = Path(path) if path else executing_dir
    script_path = expdir.joinpath("script.py")
    config_path = expdir.joinpath("config.conf")

    if not script_path.is_file():
        raise FileNotFoundError("No script.py found at {}".format(script_path))

    if not config_path.is_file():
        logger.warning("No config.conf found at {}. Running on default config only.".format(config_path))
    
    # import script from path
    script = load("script.py", script_path)

    # set generate_experiment function
    localserver.script.set_generator(script.generate_experiment)

    # set port
    port = 5000
    while not socket_checker(port):
            port += 1
    
    # generate url
    expurl = 'http://127.0.0.1:{port}/start'.format(port=port)

    # open correct browser
    if settings.experiment.fullscreen:
        ChromeKiosk.open(expurl)
    else:
        webbrowser.open(expurl)

    # run app
    sys.stderr.writelines([" * Start local experiment using {}\n".format(expurl)])
    localserver.app.run(port=port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    """This part of the module is run only if it is called directly via ``python -m alfred3.run``.
    """

    # parse command line path option
    if len(sys.argv) < 2:
        expdir = Path.cwd()
    elif len(sys.argv) == 2:
        """This section would allow us to simply give a path as an argument to the command line call. For this to work, settings need to be able to read a specific config.conf.
        # TODO: Finish implementation of this feature.
        """

        expdir = Path(sys.argv[1]).resolve()
        raise NotImplementedError("Giving parameters to the call to alfred3.run is currently not implemented.")
    
    run_experiment(path=expdir)
