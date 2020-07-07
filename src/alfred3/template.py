"""Creates an alfred3 experiment template.

The template is downloaded from its GitHub repository (master branch),
which means that for the execution of this module, you need an active
internet connection.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

from pathlib import Path

import click
import dload


def remove_files(path: str, files: list):
    p = Path(path)
    for filename in files:
        f = p / filename
        f.unlink()


@click.command()
@click.option("--name", default=None, help="Name of the new experiment directory.")
@click.option(
    "--path",
    default=Path.cwd(),
    help="Path to the target directory. The template directory will be placed in this directory.",
)
@click.option(
    "-b/-s",
    "--big/--small",
    default=False,
    help="If this flag is set to 'b' / '--big', a 'big' template will be downloaded, which contains more default structure compared to the 'small' hello-world template.",
    show_default=True,
)
@click.option(
    "-r",
    "--runpy",
    default=False,
    help="If this flag is set, the 'run.py' will be included in the download.",
    show_default=True,
    is_flag=True,
)
def download_template(name: str, path: str, big: bool, runpy: bool):
    p = Path(path).resolve()

    filenames = ["LICENSE"]

    if big:
        dirname = "alfred-template-master"
        url = "https://github.com/jobrachem/alfred-template/archive/master.zip"

    else:
        dirname = "alfred-hello_world-master"
        url = "https://github.com/jobrachem/alfred-hello_world/archive/master.zip"
        filenames.append("alfred-hello_world.png")

    if not runpy:
        filenames.append("run.py")

    if p.joinpath(dirname).exists() or p.joinpath(name).exists():
        raise FileExistsError("Directory already exists")

    dload.save_unzip(zip_url=url, extract_path=str(p), delete_after=True)

    repo_dir = p / dirname
    if name:
        target_dir = repo_dir.rename(name)
    else:
        name = dirname

    target_dir = p / name

    remove_files(path=target_dir, files=filenames)
    print(f"\nCreated an alfred3 experiment template in the directory '{str(target_dir)}'.")
    print(
        f"\nYou can start the experiment from within this directory via running 'python3 -m alfred.run --path={str(path)}' from a terminal."
    )


if __name__ == "__main__":
    download_template()  # pylint: disable=no-value-for-parameter
