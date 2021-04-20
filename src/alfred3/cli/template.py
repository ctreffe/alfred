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
    "--path",
    default=None,
    help="The directory in which to place alfred3 template files.",
    show_default=True
)
def template(path: Path):
    _write(filename="script.py", path=path)
    _write(filename="alfred.conf", out_filename="config.conf", path=path)
    click.echo("Template created. Start experiment with 'alfred3 run'.")





