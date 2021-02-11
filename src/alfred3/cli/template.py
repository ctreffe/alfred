from importlib import resources as res
from pathlib import Path

import click

from alfred3 import files


def _write(filename: str, path: Path = None):
    fileobj = res.read_text(files, filename)
    
    if path is not None and path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
    
    if path is None:
        filepath = Path.cwd() / filename
    else:
        filepath = path / filename
    
    if filepath.exists() and filepath.is_file():
        click.echo(f"File '{filepath}' already exists. Skipping file.")
    else:
        filepath.write_text(fileobj)


@click.command()
@click.option(
    "--path",
    default=None,
    help="The directory in which to place alfred3 template files.",
    show_default=True
)
def template(path: Path):
    _write(filename="script.py", path=path)
    _write(filename="alfred.conf", path=path)
    click.echo("Template created. Start experiment with 'alfred3 run'.")





