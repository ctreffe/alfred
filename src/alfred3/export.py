"""Provides functionality for exporting alfred data to .csv via the 
command line.

Easiest use case is to call it from within your experiment directory.
It will extract the necessary information about filepaths from your
config.conf and secrets.conf files.::

    python -m alfred3.export

Optionally, specify the source manually by giving the name of a 
config.conf or a secrets.conf section. The function will then export data
that was saved with the saving agent defined in that section::

    python -m alfred3.export --src="mongo_saving_agent"

You can also use it to convert .json files from the current working 
directory to .csv, saving the resulting file in the current working 
directory aswell::

    python -m alfred3.export -h

For more detailed usage information, see::

    python -m alfred3.export --help

.. moduleauthor:: Johannes Brachem <jbrachem@posteo.de> 
"""


from pprint import pprint

import csv
import json
import io
import os

from typing import Union
from pathlib import Path

import click

from .saving_agent import AutoMongoClient
from .data_manager import DataManager
from .data_manager import find_unique_name
from .data_manager import CodeBookExporter
from .data_manager import ExpDataExporter
from .config import ExperimentConfig, ExperimentSecrets


class MongoToCSV:
    """Downloads alfred3 data from a MongoDB collection as defined in
    a correspondig secrets.conf section.

    The class expects to be run from an experiment directory and to be
    able to infer the data_type from the provided *secrets_section*, though
    you can manually provide either upon initialization.

    The class grabs the *exp_id*, *version*, and *csv_directory* 
    from the config.conf and the MongoDB credentials from secrets.conf,
    both located in the experiment directory.

    Standard usage:
    
    1. Run the class from your experiment directory.
    2. Initialize it with the name of your secrets.conf section that
        contains the relevant MongoDB credentials.
    3. Call :meth:`MongoToCSV.activate()`
    4. Export data by calling :meth:`MongoToCSV.export()`
    
    Args:
        secrets_section: The name of a secrets.conf section, 
            that contains credentials for a MongoDB with alfred3 data.
        data_type: A string, indicating what kind of data should be 
            exported.
        expdir: Path to a directory containing an appropriate 
            config.conf and secrets.conf.
    
    Attributes:
        data_type: The type of data to be downloaded. Accepted values
            are "codebook", "unlinked", and "exp_data". On intialization,
            the data type is inferred from the section name. If the name 
            ends on "unlinked" or "codebook", that will be used as data 
            type. Else, "exp_data" will be used.
        expdir: The experiment directory.
    """

    def __init__(
        self, secrets_section: str, data_type: str = None, expdir: Union[str, Path] = None
    ):

        self.secrets_section = secrets_section

        if secrets_section.endswith("unlinked"):
            auto_data_type = "unlinked"
        elif secrets_section.endswith("codebook"):
            auto_data_type = "codebook"
        else:
            auto_data_type = "exp_data"

        self.data_type = data_type if data_type else auto_data_type
        self.expdir = Path(expdir) if expdir else Path.cwd()

    def activate(self):
        secrets = ExperimentSecrets(expdir=self.expdir)
        config = ExperimentConfig(expdir=self.expdir)

        sec = secrets.combine_sections("mongo_saving_agent", self.secrets_section)

        client = AutoMongoClient(sec)
        db_name = sec.get("database")
        col_name = sec.get("collection")

        self.collection = client[db_name][col_name]
        self.exp_id = config.get("metadata", "exp_id")
        self.exp_version = config.get("metadata", "version")
        self.out_dir = Path(config.get("general", "csv_directory"))
        self.out_dir.mkdir(exist_ok=True, parents=True)

    @property
    def out_dir(self):
        return self._out_dir

    @out_dir.setter
    def out_dir(self, out_dir):
        if not out_dir.is_absolute():
            self._out_dir = self.expdir / out_dir
        else:
            self._out_dir = out_dir

    @property
    def csv_name(self):
        return find_unique_name(self.out_dir, self.data_type + ".csv")

    def export(self, **kwargs):
        if self.data_type == DataManager.CODEBOOK_DATA:
            self.export_codebook(**kwargs)
        else:
            self.export_general(**kwargs)

    def export_codebook(self, **kwargs):
        ex = CodeBookExporter()

        if not self.exp_version:
            i = 1
            for doc in self.collection.find(
                {"exp_id": self.exp_id, "type": DataManager.CODEBOOK_DATA,}
            ):

                outfile = self.out_dir / self.csv_name
                ex.process(doc)
                ex.write_to_file(str(outfile), **kwargs)
                ex.reset()
                i += 1
        else:
            ex.write_mongo_data_to_file(
                collection=self.collection,
                exp_id=self.exp_id,
                exp_version=self.exp_version,
                out_dir=self.out_dir,
                csv_name=self.csv_name,
                **kwargs,
            )

    def export_general(self, **kwargs):
        ex = ExpDataExporter()
        ex.write_mongo_data_to_file(
            collection=self.collection,
            exp_id=self.exp_id,
            out_dir=self.out_dir,
            csv_name=self.csv_name,
            data_type=self.data_type,
            **kwargs,
        )


class LocalToCSV:
    """Collects alfred3 data from the file system and exports them
    as .csv files.

    The class expects to be run from an experiment directory and to be
    able to infer the data_type from the provided *config_section*, though
    you can also manually provide the *data_type* and the *expdir* upon 
    initialization.

    The class grabs the *csv_directory* (output directory) and the input
    directory from the config.conf located in the experiment directory 
    (*expdir*).

    Standard usage:
    
    1. Run the class from your experiment directory.
    2. Initialize it with the name of your config.conf section that
        defines the local saving agent whose data you want to export.
    3. Call :meth:`LocalToCSV.activate()`
    4. Export data by calling :meth:`LocalToCSV.export()`
    
    Args:
        config_section: The name of a config.conf section, 
            that defines the relevant LocalSavingAgent.
        data_type: A string, indicating what kind of data should be 
            exported.
        expdir: Path to a directory containing an appropriate 
            config.conf (usually an experiment directory).
    
    Attributes:
        data_type: The type of data to be downloaded. Accepted values
            are "codebook", "unlinked", and "exp_data". On intialization,
            the data type is inferred from the section name. If the name 
            ends on "unlinked" or "codebook", that will be used as data 
            type. Else, "exp_data" will be used.
        expdir: The experiment directory.
    """

    def __init__(
        self, config_section: str, data_type: str = None, expdir: Union[str, Path] = None
    ):
        self.config_section = config_section
        if config_section.endswith("unlinked"):
            auto_data_type = "unlinked"
        elif config_section.endswith("codebook"):
            auto_data_type = "codebook"
        else:
            auto_data_type = "exp_data"

        self.data_type = data_type if data_type else auto_data_type
        self.expdir = Path(expdir) if expdir else Path.cwd()

    @property
    def csv_name(self):
        return self.data_type + ".csv"

    @property
    def out_dir(self):
        return self._out_dir

    @out_dir.setter
    def out_dir(self, out_dir):
        if not out_dir.is_absolute():
            self._out_dir = self.expdir / out_dir
        else:
            self._out_dir = out_dir

    @property
    def in_dir(self):
        return self._in_dir

    @in_dir.setter
    def in_dir(self, in_dir):
        if not in_dir.is_absolute():
            self._in_dir = self.expdir / in_dir
        else:
            self._in_dir = in_dir

    def activate(self):
        config = ExperimentConfig(expdir=self.expdir)
        self.out_dir = Path(config.get("general", "csv_directory"))
        self.in_dir = Path(config.get(self.config_section, "path"))
        self.out_dir.mkdir(exist_ok=True, parents=True)

    def export(self, **kwargs):
        if self.data_type == DataManager.CODEBOOK_DATA:
            self.export_codebook(**kwargs)
        else:
            self.export_general(**kwargs)

    def export_codebook(self, **kwargs):
        ex = CodeBookExporter()

        # export all codebooks found in in_dir
        for filename in os.listdir(self.in_dir):
            in_file = Path(self.in_dir) / filename
            try:
                ex.write_local_data_to_file(in_file=in_file, out_dir=self.out_dir, **kwargs)
            except (KeyError, IsADirectoryError):
                pass
            finally:
                ex.reset()

    def export_general(self, **kwargs):
        ex = ExpDataExporter()
        ex.write_local_data_to_file(
            in_dir=self.in_dir,
            out_dir=self.out_dir,
            data_type=self.data_type,
            csv_name=self.csv_name,
            **kwargs,
        )


@click.command()
@click.option(
    "--src",
    default="local_saving_agent",
    help="The name of the configuration section in 'config.conf' or 'secrets.conf' that defines the SavingAgent whose data you want to export.",
    show_default=True,
)
@click.option(
    "--directory",
    default=Path.cwd(),
    help="The path to the experiment whose data you want to export. [default: Current working directory]",
)
@click.option(
    "-h",
    "--here",
    default=False,
    is_flag=True,
    help="With this flag, you can indicate that you want to export .json files located in the current working directory.",
    show_default=True,
)
@click.option(
    "--data_type",
    default=None,
    help="The type of data that you want to export. Accepted values are 'exp_data', 'unlinked', and 'codebook'. If you specify a 'src', the function tries to infer the data type from the 'src's suffix. (Example: 'mongo_saving_agent_codebook' would lead to 'data_type' = 'codebook'. If you give a value for 'data_type', that always takes precedence. If no data_type is provide and no data_type can be inferred, 'exp_data' is used.",
    show_default=True,
)
@click.option(
    "--missings",
    default=None,
    help="Here, you can manually specify a value that you want to insert for missing values",
    show_default=True,
)
@click.option(
    "--remove_linebreaks",
    default=False,
    is_flag=True,
    help="Indicates, whether linebreak characters should be deleted from the file. If you don't use this flag (the default), linebreaks will be replaced with spaces.",
    show_default=True,
)
@click.option(
    "--delimiter",
    default=",",
    help="Here, you can manually specify a delimiter for your .csv file. You need to put the delimiter inside quotation marks, e.g. like this: --delimiter=';'.",
    show_default=True,
)
def export_cli(data_type, src, directory, here, missings, remove_linebreaks, delimiter):

    # try to guess data_type from suffix of src
    if not data_type and src is not None and src.endswith(DataManager.CODEBOOK_DATA):
        data_type = DataManager.CODEBOOK_DATA
    elif not data_type and src is not None and src.endswith(DataManager.UNLINKED_DATA):
        data_type = DataManager.UNLINKED_DATA
    elif not data_type and src is not None and src.endswith(DataManager.EXP_DATA):
        data_type = DataManager.EXP_DATA
    data_type = DataManager.EXP_DATA if data_type is None else data_type

    if here and data_type == DataManager.CODEBOOK_DATA:
        wd = Path.cwd()
        exporter = CodeBookExporter()
        for filename in os.listdir(wd):
            fp = wd / filename
            exporter.write_local_data_to_file(
                in_file=fp, out_dir=wd, delimiter=delimiter,
            )
            exporter.reset()
        print(f"Export completed. Files are located in '{wd}'.")

    elif here and data_type in [DataManager.EXP_DATA, DataManager.UNLINKED_DATA]:
        wd = Path.cwd()
        exporter = ExpDataExporter()

        exporter.write_local_data_to_file(
            in_dir=wd,
            out_dir=wd,
            data_type=data_type,
            missings=missings,
            remove_linebreaks=remove_linebreaks,
            delimiter=delimiter,
        )
        print(f"Export completed. Files are located in '{wd}'.")
    else:

        if "mongo" in src:
            exporter = MongoToCSV(secrets_section=src, data_type=data_type, expdir=directory)
        elif "local" in src:
            exporter = LocalToCSV(config_section=src, data_type=data_type, expdir=directory)

        exporter.activate()
        exporter.export(
            missings=missings, remove_linebreaks=remove_linebreaks, delimiter=delimiter
        )
        print(f"Export completed. Files are located in '{str(exporter.out_dir)}'.")


if __name__ == "__main__":
    export_cli()  # pylint: disable=no-value-for-parameter
