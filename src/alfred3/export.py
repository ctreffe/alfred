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
import random

from typing import Union
from pathlib import Path

import click

from .saving_agent import AutoMongoClient
from .data_manager import DataManager
# from .data_manager import CodeBookExporter
# from .data_manager import ExpDataExporter
from .config import ExperimentConfig, ExperimentSecrets


class Exporter:

    def __init__(self, experiment):
        self.experiment = experiment
        self.exp = experiment
        self.csv_dir = self.exp.subpath(self.exp.config.get("general", "csv_directory"))
        self.delimiter = self.exp.config.get("general", "csv_delimiter")
    
    def export(self, data_type):
        
        if data_type == DataManager.CODEBOOK_DATA:
            self.export_codebook()
        elif data_type == DataManager.HISTORY:
            self.export_history()
        elif data_type == DataManager.UNLINKED_DATA:
            self.export_unlinked()
        else:
            self.export_exp_data()

    def export_exp_data(self):
        csv_name = "exp_data.csv"
        
        data = self.exp.data_manager.flat_session_data
        fieldnames = list(data.keys())

        path = self.csv_dir / csv_name
        
        with open(path, "a", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=self.delimiter)
            if not path.read_text():  
                writer.writeheader()
            writer.writerow(data)
    
    def export_history(self):
        csv_name = "move_history.csv"
        data = self.exp.data_manager.move_history
        fieldnames = DataManager.extract_fieldnames(data)
        path = self.csv_dir / csv_name
        
        with open(path, "a", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=self.delimiter)
            if not path.read_text():  
                writer.writeheader()
            writer.writerows(data)
    
    def export_unlinked(self):
        csv_name = "unlinked.csv"
        agent = self.exp.data_saver.unlinked.agents["local_unlinked"]
        data = self.exp.data_manager.unlinked_data_with(agent)
        data = self.exp.data_manager.flatten(data)
        fieldnames = list(data.keys())

        path = self.csv_dir / csv_name

        if path.exists() and path.read_text():
            with open(path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=self.delimiter)
                
                ul_data = []
                for row in reader:
                    ul_data.append(dict(row))
            
            ul_data.append(data)
            random.shuffle(ul_data)
            fieldnames = DataManager.extract_fieldnames(ul_data)
            data = ul_data
        
            with open(path, "w", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=self.delimiter)
                writer.writeheader()
                writer.writerows(data)
        else:
            with open(path, "w", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=self.delimiter)
                writer.writeheader()
                writer.writerow(data)

    def export_codebook(self):
        data = self.exp.data_manager.codebook_data
        fieldnames = DataManager.extract_fieldnames(data)

        version = self.exp.config.get("metadata", "version")
        csv_name = f"{DataManager.CODEBOOK_DATA}_{version}.csv"

        path = self.csv_dir / csv_name

        if path.exists() and path.read_text():
            with open(path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=self.delimiter)
                
                existing_codebook = []
                for row in reader:
                    existing_codebook.append(dict(row))
            
            existing_names = [entry["name"] for entry in existing_codebook]

            for element_info in data:
                if element_info["name"] not in existing_names:
                    existing_codebook.append(element_info)
            
            data = existing_codebook

        with open(path, "w", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(data)

def find_unique_name(directory, filename, exp_version=None, index: int = 1):
    filename = Path(filename)
    name = filename.stem
    ext = filename.suffix
    exp_version = "_" + exp_version if exp_version else ""

    normal_name = name + exp_version + ext
    idx_name = name + exp_version + f"_{index}" + ext

    if not normal_name in os.listdir(directory):
        return normal_name
    elif not idx_name in os.listdir(directory):
        return idx_name
    else:
        i = index + 1
        return find_unique_name(directory=directory, filename=filename, index=i)

def find_data_directory(expdir, saving_agent):
    config = ExperimentConfig(expdir=expdir)
    path = Path(config.get(saving_agent, "path")).resolve()
    if not path.is_absolute():
        path = expdir.resolve() / path
    return path

def find_csv_dir(expdir):
    config = ExperimentConfig(expdir=expdir)
    path = Path(config.get("general", "csv_directory")).resolve()
    if not path.is_absolute():
        path = expdir.resolve() / path
    return path

def find_csv_name(expdir, data_type):
    directory = find_csv_dir(expdir)
    filename = data_type + ".csv"
    return find_unique_name(directory, filename)

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
# @click.option(
#     "--remove_linebreaks",
#     default=False,
#     is_flag=True,
#     help="Indicates, whether linebreak characters should be deleted from the file. If you don't use this flag (the default), linebreaks will be replaced with spaces.",
#     show_default=True,
# )
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

    
    if src.startswith("local"):
        if here:
            datadir = Path.cwd()
        elif directory:
            datadir = find_data_directory(expdir=directory, saving_agent=src)
        
        data = DataManager.iterate_local_data(data_type=data_type, directory=datadir)
    
    elif src.startswith("mongo"):
        exp_id = ExperimentConfig(expdir=directory).get("general", "exp_id")
        secrets = ExperimentSecrets(expdir=directory)

        data = DataManager.iterate_mongo_data(exp_id=exp_id, data_type=data_type, secrets=secrets)

    data_list = [DataManager.flatten(dataset) for dataset in data]
    fieldnames = list(data_list.keys())

    csv_name = find_csv_name(expdir=directory, data_type=data_type)

    writer = csv.DictWriter(csv_name, fieldnames=fieldnames, delimiter=delimiter)
    writer.writeheader()
    writer.writerows(data_list)
        

    # if here and data_type == DataManager.CODEBOOK_DATA:
    #     wd = Path.cwd()
    #     exporter = CodeBookExporter()
    #     for filename in os.listdir(wd):
    #         fp = wd / filename
    #         exporter.write_local_data_to_file(
    #             in_file=fp, out_dir=wd, delimiter=delimiter,
    #         )
    #         exporter.reset()
    #     print(f"Export completed. Files are located in '{wd}'.")

    # elif here and data_type in [DataManager.EXP_DATA, DataManager.UNLINKED_DATA]:
    #     wd = Path.cwd()
    #     exporter = ExpDataExporter()

    #     exporter.write_local_data_to_file(
    #         in_dir=wd,
    #         out_dir=wd,
    #         data_type=data_type,
    #         missings=missings,
    #         remove_linebreaks=remove_linebreaks,
    #         delimiter=delimiter,
    #     )
    #     print(f"Export completed. Files are located in '{wd}'.")
    # else:

    #     if "mongo" in src:
    #         exporter = MongoToCSV(secrets_section=src, data_type=data_type, expdir=directory)
    #     elif "local" in src:
    #         exporter = LocalToCSV(config_section=src, data_type=data_type, expdir=directory)

    #     exporter.activate()
    #     exporter.export(
    #         missings=missings, remove_linebreaks=remove_linebreaks, delimiter=delimiter
    #     )
    #     print(f"Export completed. Files are located in '{str(exporter.out_dir)}'.")


if __name__ == "__main__":
    export_cli()  # pylint: disable=no-value-for-parameter
