"""Creates an alfred3 experiment template.

The template is downloaded from its GitHub repository (master branch),
which means that for the execution of this module, you need an active
internet connection.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

from pathlib import Path
import shutil

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
    "--release",
    default="master",
    help=(
        "You can specify a release tag here, if you"
        "want to use a specific version of the template."
    ),
)
@click.option(
    "-b/-s",
    "--big/--small",
    default=False,
    help=(
        "If this flag is set to 'b' / '--big', a 'big' template will be downloaded, which "
        "contains a more sophistaced default structure compared to the 'small' hello-world template."
    ),
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
def download_template(name: str, path: str, release: str, big: bool, runpy: bool):
    p = Path(path).resolve()  # parent directory, e.g. exps/

    filenames = ["LICENSE"]

    if release.startswith("v"):
        parsed_release = release[1:]
    else:
        parsed_release = release

    if big:
        dirname = f"alfred-template-{parsed_release}"
        url = f"https://github.com/jobrachem/alfred-template/archive/{release}.zip"

    else:
        dirname = f"alfred-hello_world-{parsed_release}"
        url = f"https://github.com/jobrachem/alfred-hello_world/archive/{release}.zip"
        filenames.append("alfred-hello_world.png")

    if not runpy:
        filenames.append("run.py")

    if p.joinpath(dirname).exists():
        raise FileExistsError("Directory already exists")

    if name is not None and p.joinpath(name).exists():
        raise FileExistsError("Directory already exists")

    dload.save_unzip(zip_url=url, extract_path=str(p), delete_after=True)

    repo_dir = p / dirname  # exp directory, e.g.: exps/alfred_hello-world-master
    if name:
        shutil.move(src=repo_dir, dst=p.joinpath(name))
    else:
        name = dirname

    target_dir = p / name

    remove_files(path=target_dir, files=filenames)

    if big:
        pkg_path = Path(__file__).resolve().parent
        pkg_secrets_file = pkg_path / "files" / "secrets.conf"
        pkg_secrets = pkg_secrets_file.read_text()

        secrets_file = target_dir / "secrets.conf"
        secrets_file.write_text("# place secret information here.")
        secrets_file.write_text("# NEVER share this file.")
        secrets_file.write_text(
            """# Place secret information here.
# NEVER share this file.
[mongo_saving_agent]
use = false
assure_initialization = true
level = 1
host = 
port = 
database = alfred
collection = 
user = 
password = 
auth_source = alfred
use_ssl = false
ca_file_path = 
        """
        )

    print(
        f"\nalfred3: Created an alfred3 experiment template in the directory '{str(target_dir)}'."
    )
    print(
        f"alfred3: You can start the experiment by changig to the directory and running 'python3 -m alfred.run' from a terminal."
    )


if __name__ == "__main__":
    download_template()  # pylint: disable=no-value-for-parameter
