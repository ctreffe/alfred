"""Creates an alfred3 experiment template.

The template is downloaded from its GitHub repository (master branch),
which means that for the execution of this module, you need an active
internet connection.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

from pathlib import Path
from uuid import uuid4
import shutil
import os

import click
import dload


class TemplateDownloader:
    def __init__(self):
        self._root_dir = Path.cwd()
        self._expdir = None
        self.here = False

        self.files_to_remove = ["LICENSE"]
        self.allowed_names = [".git", ".idea"]
        self.release = None
        self.url_base = None
        self.repo = None
        self._tmp_dir = None

        self.include_secrets = False
        self.secrets = None

        self.conflict_counter = 0

    @property
    def root_dir(self):
        return self._root_dir

    @root_dir.setter
    def root_dir(self, name):
        d = Path(name)
        self._root_dir = d

    @property
    def expdir(self):
        if not self.here and self._expdir is not None:
            return self.root_dir / self._expdir
        else:
            return self.root_dir

    @expdir.setter
    def expdir(self, directory):
        if directory is None:
            self._expdir = directory
        else:
            d = Path(directory)
            if d.is_absolute():
                self._expdir = str(d.stem)
                self.root_dir = d.parent
            else:
                self._expdir = str(d)

    @property
    def downloaded_dir(self):
        if self.release.startswith("v"):
            parsed_release = self.release[1:]
        else:
            parsed_release = self.release
        return f"{self.repo}-{parsed_release}"

    @property
    def tmp_dir(self):
        if not self._tmp_dir:
            raise FileNotFoundError("No tmp_dir found.")
        return self.root_dir / self._tmp_dir

    @property
    def tmp_dir_downloaded(self):
        return self.tmp_dir / self.downloaded_dir

    @property
    def url(self):
        return f"{self.url_base}/{self.repo}/archive/{self.release}.zip"

    def _create_directory(self):
        if not self.here:
            try:
                self.expdir.mkdir()
            except FileExistsError:
                self.conflict_counter += 1
                self._expdir = self._expdir + f"_conflict{self.conflict_counter}"
                print(f"Target directory already existed. Created new directory {self.expdir}")
                self._create_directory()

    def download_template(self):
        self._create_directory()

        dir_content = os.listdir(self.expdir)

        for f in self.allowed_names:
            try:
                dir_content.remove(f)
            except ValueError:
                pass
        if dir_content:

            raise FileExistsError("Target directory must be empty.")
        self._tmp_dir = uuid4().hex
        self.tmp_dir.mkdir()
        dload.save_unzip(zip_url=self.url, extract_path=str(self.tmp_dir), delete_after=True)
        self._remove_files()
        self._move_files()
        if self.include_secrets:
            self._add_secrets_conf()

    def _remove_files(self):
        for filename in self.files_to_remove:
            f = self.tmp_dir_downloaded / filename
            f.unlink()

    def _move_files(self):
        for f in os.listdir(self.tmp_dir_downloaded):
            shutil.move(src=str(self.tmp_dir_downloaded / f), dst=str(self.expdir))
        shutil.rmtree(str(self.tmp_dir))

    def _add_secrets_conf(self):
        # pkg_path = Path(__file__).resolve().parent
        # pkg_secrets_file = pkg_path / "files" / "secrets.conf"
        # pkg_secrets = pkg_secrets_file.read_text()

        secrets_file = self.expdir / "secrets.conf"
        secrets_file.write_text(self.secrets)


@click.command()
@click.option(
    "--name",
    default="alfred3_experiment",
    help="Name of the new experiment directory.",
    show_default=True,
)
@click.option(
    "--path",
    default=Path.cwd(),
    help="Path to the target directory. [default: Current working directory]",
)
@click.option(
    "--release",
    default="v1.0.0",
    help=(
        "You can specify a release tag here, if you "
        "want to use a specific version of the template."
    ),
)
@click.option(
    "--variant",
    default="m",
    help=(
        "Which type of template do you want to download? "
        "The available options are: 's' (minimalistic), 'm' (includes 'run.py' and 'secrets.conf') "
        "and 'l' (includes subdirectory with imported classes and instructions.)"
    ),
    show_default=True,
)
@click.option(
    "-h",
    "--here",
    default=False,
    help="If this flag is set to '-h', the template files will be placed directly into the directory specified in '--path', ignoring the paramter '--name'.",
    show_default=True,
    is_flag=True,
)
def download_template(name, path, release, variant, here):
    loader = TemplateDownloader()
    loader.root_dir = path
    loader.expdir = name
    loader.here = here
    loader.release = release
    loader.url_base = "https://github.com/jobrachem"
    msg = "Download successful."

    if variant not in ["s", "m", "l"]:
        raise NotImplementedError

    if variant == "s":
        loader.repo = "alfred-hello_world"
        loader.files_to_remove.append("alfred-hello_world.png")
        loader.files_to_remove.append("run.py")
        start_msg = "Start your experiment via 'python -m alfred3.run'."

    if variant == "m":
        loader.repo = "alfred-hello_world"
        loader.files_to_remove.append("alfred-hello_world.png")

    if variant == "m" or variant == "l":
        start_msg = "Start your experiment via 'python -m alfred3.run' or by executing 'run.py'."
        loader.include_secrets = True
        loader.secrets = """# Place secret information here.
# NEVER share this file.

# [encryption]
# encryption_key =
# public_key = true


[mongo_saving_agent]
use = false
name = mongo
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

# The following section can take the same field as 'mongo_saving_agent'.
# Field that are not provided will be filled with the input from 'mongo_saving_agent'
[mongo_saving_agent_unlinked]
use = false
name = mongo_unlinked

# The following section can take the same field as 'mongo_saving_agent'.
# Field that are not provided will be filled with the input from 'mongo_saving_agent'
[mongo_saving_agent_codebook]
use = false
name = mongo_codebook
        """

    if variant == "l":
        loader.repo = "alfred-template"

    loader.download_template()
    print(msg + " " + start_msg)


if __name__ == "__main__":
    download_template()  # pylint: disable=no-value-for-parameter
