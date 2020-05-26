"""Creates an alfred3 experiment template.

The template is downloaded from its GitHub repository (master branch),
which means that for the execution of this module, you need an active
internet connection.
"""

import urllib.request
import shutil
import zipfile
import os
import shutil
import sys
from pathlib import Path


def donwload_template(url: str, target_dir: str = None):
    """Downloads an experiment template from a url.

    If no `target_dir` is provided, the template directory will be
    placed in the current working directory.

    Args:
        url: URL to the zip-file of an experiment template git repo.
        target_dir: Target directory for the experiment template.
            Defaults to `None`.
    """

    file_name = "tmp.zip"

    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(url) as response, open(file_name, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

    if not target_dir:
        target_dir = os.getcwd()
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall(target_dir)
    else:
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall(target_dir)

            namelist = zip_ref.namelist()

        # move files to target dir and remove zip directory
        directory_name = namelist[0]
        subdir = os.path.join(target_dir, directory_name)

        for element in os.listdir(subdir):
            shutil.move(os.path.join(subdir, element), target_dir)

        os.rmdir(subdir)

    os.remove(file_name)


if __name__ == "__main__":

    hello_world = "https://github.com/jobrachem/alfred-hello_world/archive/master.zip"

    # process script
    if len(sys.argv) < 2:
        url = hello_world
        donwload_template(url)
        print("Created an alfred3 experiment template in the current working directory.")
    elif len(sys.argv) == 2:
        url = hello_world
        donwload_template(url, sys.argv[1])
        print(f"Created an alfred3 experiment template in the directory '{sys.argv[1]}'.")
    elif len(sys.argv) > 2:
        raise NotImplementedError("Currently, there are no arguments available for this module.")

    # print out success
    print("You can start the experiment via 'python3 run.py'.")
