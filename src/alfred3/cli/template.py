from importlib import resources as res
from pathlib import Path

import click

from alfred3 import files


def _write(filename: str, out_filename: str = None, path: Path = None):
    fileobj = res.read_text(files, filename)
    
    if path is not None and path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
    
    out_filename = out_filename if out_filename is not None else filename

    if path is None:
        filepath = Path.cwd() / out_filename
    else:
        filepath = path / out_filename
    
    if filepath.exists() and filepath.is_file():
        click.echo(f"File '{filepath}' already exists. Skipping file.")
    else:
        filepath.write_text(fileobj, encoding='utf-8')


@click.command()
@click.option(
    "-b", "big",
    default=False,
    is_flag=True,
    help="If '-b' is given, a more extensive template will be loaded, \
        including, for instance, a secrets.conf and a .gitignore file."
)
@click.option(
    "--path",
    default=None,
    type=click.Path(),
    help="The directory in which to place alfred3 template files.",
    show_default=True
)
def template(big, path):
    path = Path(path) if path is not None else None

    _write(filename="alfred.conf", out_filename="config.conf", path=path)
    if big:
        _write(filename="secrets.conf", path=path)
        _write(filename=".gitignore")
        _write(filename="script_big.py", out_filename="script.py", path=path)
    else:
        _write(filename="script.py", path=path)
    click.echo("Template created. Start experiment with 'alfred3 run'.")





