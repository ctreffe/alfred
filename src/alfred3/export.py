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
from typing import List, Iterator
from pathlib import Path
from itertools import chain

import click

from .saving_agent import AutoMongoClient
from .data_manager import DataManager
from .data_manager import decrypt_recursively
from .config import ExperimentConfig, ExperimentSecrets


class Exporter:
    """
    Handles data export from json to csv.

    The exporter obeys the follwoing rules for all export functions:

    1. Check if a file of the designated name exists in the designated
       directory.
    2. If yes, append the data from the current session to this file.
    3. If not, scan all available .json files and produce a new, 
       complete csv file.
    """

    def __init__(self, experiment):
        self.experiment = experiment
        self.exp = experiment
        self.csv_dir = self.exp.subpath(self.exp.config.get("data", "csv_directory"))
        self.delimiter = self.exp.config.get("data", "csv_delimiter")
        self.save_dir = self.exp.subpath(self.exp.config.get("local_saving_agent", "path"))

    def export(self, data_type: str):
        """
        Calls the appropriate specialized export function, depending
        on data type.

        Args:
            data_type (str): One of 'exp_data', 'unlinked', 'codebook',
                'move_history'.

        """
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        if data_type == DataManager.CODEBOOK_DATA:
            self.export_codebook()
        elif data_type == DataManager.HISTORY:
            self.export_move_history()
        elif data_type == DataManager.UNLINKED_DATA:
            self.export_unlinked()
        elif data_type == DataManager.EXP_DATA:
            self.export_exp_data()
    
    def _load(self, path: Union[str, Path]) -> list:
        """
        Returns a list of dictonaries with session data, read from an
        existing csv file.

        This version of 'load' uses the experiment-specific delimiter
        defined in config.conf.
        """
        return self.load(path, self.delimiter)

    @staticmethod
    def load(path: Union[str, Path], delimiter: str) -> list:
        """
        Returns a list of dictonaries with session data, read from an
        existing csv file.

        This version of 'load' is available as a public static method.
        """
        with open(path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            existing_data = [dict(row) for row in reader]
        return existing_data
    
    def _write(self, data: Iterator[dict], fieldnames: List[str], path: Path):
        """
        Writes a list of session data dictionaries to a csv file.

        This version of 'write' uses the experiment-specific delimiter
        defined in config.conf.
        """
        self.write(data, fieldnames, path, self.delimiter)

    @staticmethod
    def write(data: Iterator[dict], fieldnames: List[str], path: Path, delimiter: str):
        """
        Writes a list of session data dictionaries to a csv file.

        This version of 'write' is available as a public static method.
        """
        with open(path, "w", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
    
    def export_exp_data(self):
        csv_name = "exp_data.csv"
        path = self.csv_dir / csv_name

        if path.exists() and path.read_text():
            alldata = self._load(path)
            sessiondata = self.exp.data_manager.flat_session_data
            alldata.append(sessiondata)
            
            # get fieldnames from list of flat datasets
            metadata = list(self.exp.data_manager.metadata.keys())
            client_info = list(self.exp.data_manager.client_data.keys())
            element_names = []
            for row in alldata:
                for colname in row:
                    if not colname in metadata + client_info + ["additional_data"]:
                        if not colname in element_names:
                            element_names.append(colname)
            fieldnames = metadata + client_info + sorted(element_names) + ["additional_data"]
        else:
            data = list(DataManager.iterate_local_data(data_type=DataManager.EXP_DATA, directory=self.save_dir))
            fieldnames = DataManager.extract_ordered_fieldnames(data)
            alldata = [DataManager.flatten(d) for d in data]
        self._write(alldata, fieldnames, path)
        self.exp.log.info(f"Exported main experiment data to {path.parent.name}/{path.name}.")
    
    def export_move_history(self):
        csv_name = "move_history.csv"
        data = self.exp.data_manager.move_history
        fieldnames = DataManager.extract_fieldnames(data)
        path = self.csv_dir / csv_name

        if path.exists() and path.read_text():
            history = self._load(path)
            history += data
            fieldnames = DataManager.extract_fieldnames(history)
        else:
            existing_data = DataManager.iterate_local_data(data_type=DataManager.EXP_DATA, directory=self.save_dir)
            history = [d["exp_move_history"] for d in existing_data]
            fieldnames = DataManager.extract_fieldnames(chain(*history))
            history = chain(*history)
        
        self._write(history, fieldnames, path)
        self.exp.log.info(f"Exported movement history to {path.parent.name}/{path.name}.")

    def export_unlinked(self):
        csv_name = "unlinked.csv"
        agent = self.exp.data_saver.unlinked.agents["local_unlinked"]
        data = self.exp.data_manager.unlinked_data_with(agent)
        data = self.exp.data_manager.flatten(data)
        fieldnames = list(data.keys())
        data = [data]

        path = self.csv_dir / csv_name

        if path.exists() and path.read_text():
            ul_data = self._load(path)
            ul_data += data
            random.shuffle(ul_data)
            fieldnames = DataManager.extract_fieldnames(ul_data)
            data = ul_data
        else:
            unlinked_dir = self.exp.config.get("local_saving_agent_unlinked", "path")
            existing_data = list(DataManager.iterate_local_data(data_type=DataManager.UNLINKED_DATA, directory=unlinked_dir))
            data = [DataManager.flatten(d) for d in existing_data]
            fieldnames = DataManager.extract_fieldnames(data)
        
        if self.exp.config.getboolean("local_saving_agent_unlinked", "decrypt_csv_export"):
            if self.exp.secrets.get("encryption", "key"):
                key = self.exp.secrets.get("encryption", "key").encode()
                data = decrypt_recursively(data, key=key)

        self._write(data, fieldnames, path)
        self.exp.log.info(f"Exported unlinked data to {path.parent.name}/{path.name}.")

    def export_codebook(self):
        data = self.exp.data_manager.codebook_data

        version = self.exp.config.get("metadata", "version")
        csv_name = f"{DataManager.CODEBOOK_DATA}_{version}.csv"

        path = self.csv_dir / csv_name

        if path.exists() and path.read_text():
            with open(path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=self.delimiter)
                existing_codebook = {dict(row)["name"]: dict(row) for row in reader}
            
            existing_codebook.update(data)
            data = existing_codebook

        fieldnames = DataManager.extract_fieldnames(data.values())
        fieldnames = DataManager.sort_codebook_fieldnames(fieldnames)
        self._write(data.values(), fieldnames, path)
        self.exp.log.info(f"Exported codebook to {path.parent.name}/{path.name}.")

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
    path = Path(config.get("data", "csv_directory")).resolve()
    if not path.is_absolute():
        path = expdir.resolve() / path
    return path

def find_csv_name(expdir, data_type):
    directory = find_csv_dir(expdir)
    filename = data_type + ".csv"
    return find_unique_name(directory, filename)


class Extractor:
    """
    Turns uncurated alfred data from json format into csv format.

    Args:
        in_path (str): Path to directory containing json files. If None
            (default), the current working directory will be used.
        out_path (str): Path to directory in which the output csv file
            will be place. If None (default), the current working 
            directory will be used.
        delimiter (str): Delimiter to use in the resulting csv file. 
            Defaults to ";"
    
    Examples:
        The extractor is used by calling one of its four methods. The
        following python code can be used to turn all alfred json 
        datasets in the current working directory into a nice csv file.

        >>> from alfred3.export import Extractor
        >>> ex = Extractor()
        >>> ex.extract_exp_data()
        
    """

    def __init__(self, in_path: str = None, out_path: str = None, delimiter: str = ";"):
        self.in_path = Path(in_path) if in_path is not None else Path.cwd()
        self.out_path = Path(out_path) if out_path is not None else Path.cwd()
        self.delimiter = delimiter

    def extract_exp_data(self):
        """
        Extracts the main experiment data from json files in the 
        Extractors *in_path*.

        Examples:
            Turn all alfred json datasets in the current working 
            directory into a nice csv file.

            >>> from alfred3.export import Extractor
            >>> ex = Extractor()
            >>> ex.extract_exp_data()
        """
        data = list(DataManager.iterate_local_data(data_type=DataManager.EXP_DATA, directory=self.in_path))
        fieldnames = DataManager.extract_ordered_fieldnames(data)
        alldata = [DataManager.flatten(d) for d in data]
        csvname = find_unique_name(directory=self.out_path, filename="exp_data.csv")
        Exporter.write(data=alldata, fieldnames=fieldnames, path=csvname, delimiter=self.delimiter)

    def extract_unlinked_data(self):
        """
        Extracts unlinked data from json files in the Extractors 
        *in_path*.

        Examples:
            Turn all alfred json datasets in the current working 
            directory into a nice csv file.

            >>> from alfred3.export import Extractor
            >>> ex = Extractor()
            >>> ex.extract_unlinked_data()
        """
        existing_data = list(DataManager.iterate_local_data(data_type=DataManager.UNLINKED_DATA, directory=self.in_path))
        data = [DataManager.flatten(d) for d in existing_data]
        fieldnames = DataManager.extract_fieldnames(data)
        csvname = find_unique_name(directory=self.out_path, filename="unlinked.csv")
        Exporter.write(data=data, fieldnames=fieldnames, path=csvname, delimiter=self.delimiter)

    def extract_codebook(self, exp_version: str):
        """
        Extracts codebook data from json files in the Extractors 
        *in_path*.

        Args:
            exp_version (str): Experiment version. Codebook data must
                be exported for specific experiment versions.

        Examples:
            Get a nice csv codebook for the json data in the current
            working directory.

            >>> from alfred3.export import Extractor
            >>> ex = Extractor()
            >>> ex.extract_codebook("1.0")
        """
        cursor = DataManager.iterate_local_data(
            data_type=DataManager.EXP_DATA, 
            directory=self.in_path, 
            exp_version=exp_version
            )
        
        cursor_unlinked = DataManager.iterate_local_data(
            data_type=DataManager.UNLINKED_DATA,
            directory=self.in_path, 
            exp_version=exp_version
        )
        
        # extract individual codebooks for each experimen session
        cbdata_collection = []
        for entry in cursor:
            cb = DataManager.extract_codebook_data(entry)
            cbdata_collection.append(cb)
        for entry in cursor_unlinked:
            cb = DataManager.extract_codebook_data(entry)
            cbdata_collection.append(cb)
        
        # combine them to a single dictionary, overwriting old values 
        # with newer ones
        data = {}
        for entry in cbdata_collection:
            data.update(entry)

        fieldnames = DataManager.extract_fieldnames(data.values())
        fieldnames = DataManager.sort_codebook_fieldnames(fieldnames)
        csvname = find_unique_name(directory=self.out_path, filename=f"codebook_{exp_version}.csv")
        Exporter.write(data=data.values(), fieldnames=fieldnames, path=csvname, delimiter=self.delimiter)


    def extract_move_history(self):
        """
        Extracts movement data from json files in the Extractors 
        *in_path*.

        Examples:
            Get a nice csv of movement data for json data in the 
            current working directory.

            >>> from alfred3.export import Extractor
            >>> ex = Extractor()
            >>> ex.extract_move_history()
        """
        existing_data = DataManager.iterate_local_data(data_type=DataManager.EXP_DATA, directory=self.in_path)
        history = [d["exp_move_history"] for d in existing_data]
        fieldnames = DataManager.extract_fieldnames(chain(*history))
        history = chain(*history)
        csvname = find_unique_name(directory=self.out_path, filename="move_history.csv")
        Exporter.write(data=history, fieldnames=fieldnames, path=csvname, delimiter=self.delimiter)
