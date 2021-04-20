# -*- coding: utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>, Johannes Brachem <jbrachem@posteo.de>
"""
from __future__ import absolute_import

import time
import os
import csv
import io
import json
import random
import copy

from pathlib import Path
from builtins import object
from typing import Union
from typing import List
from typing import Dict
from typing import Iterator

from dataclasses import asdict

from cryptography.fernet import Fernet, InvalidToken

from . import page
from .exceptions import AlfredError
from .config import ExperimentSecrets
from .saving_agent import AutoMongoClient
from .alfredlog import QueuedLoggingInterface
from .util import flatten_dict
from .util import prefix_keys_safely


class DataManager(object):
    EXP_DATA = "exp_data"
    UNLINKED_DATA = "unlinked"
    CODEBOOK_DATA = "codebook"
    HISTORY = "move_history"

    instance_log = False
    

    # the empty fields are initialized here below to enable name-
    # checking for all experiment members on these names and ordering
    # of fieldnames for csv export independent of an ExperimentSession
    # instance
    client_data = {}
    client_data["client_resolution_screen"] = None
    client_data["client_resolution_inner"] = None
    client_data["client_referrer"] = None
    client_data["client_javascript_active"] = None
    client_data["client_device_type"] = None
    client_data["client_device_manufacturer"] = None
    client_data["client_device_family"] = None
    client_data["client_browser"] = None
    client_data["client_os_family"] = None
    client_data["client_os_name"] = None
    client_data["client_os_version"] = None

    _metadata = {}
    _metadata["exp_author"] = None
    _metadata["exp_title"] = None
    _metadata["exp_version"] = None
    _metadata["exp_start_time"] = None
    _metadata["exp_start_timestamp"] = None
    _metadata["exp_save_time"] = None
    _metadata["exp_finished"] = None
    _metadata["exp_aborted"] = None
    _metadata["exp_aborted_because"] = None
    _metadata["exp_session"] = None
    _metadata["exp_condition"] = None
    _metadata["exp_id"] = None
    _metadata["exp_session_id"] = None
    _metadata["exp_plugin_queries"] = None
    _metadata["session_status"] = None
    _metadata["alfred_version"] = None
    _metadata["type"] = None

    def __init__(self, experiment):
        self._experiment = experiment
        self.exp = experiment
        self.additional_data = {}
        self.log = QueuedLoggingInterface(base_logger=__name__)
        self.log.add_queue_logger(self, __name__)
        
        

    @property
    def experiment(self):
        return self._experiment

    @property
    def metadata(self):
        data = self._metadata
        
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_version"] = self._experiment.version
        data["exp_start_time"] = self._experiment.start_time
        data["exp_start_timestamp"] = self._experiment.start_timestamp
        data["exp_save_time"] = time.time()
        data["exp_finished"] = self._experiment.finished
        data["exp_aborted"] = self._experiment.aborted
        data["exp_aborted_because"] = self._experiment._aborted_because
        data["exp_session"] = self._experiment.session
        data["exp_condition"] = self._experiment.condition
        data["exp_id"] = self._experiment.exp_id
        data["exp_session_id"] = self._experiment.session_id
        data["exp_plugin_queries"] = self._experiment._plugin_data_queries
        data["session_status"] = self._experiment.session_status
        data["alfred_version"] = self._experiment.alfred_version
        data["type"] = self.EXP_DATA
        
        return data
    
    @property
    def move_history(self):
        return [asdict(move) for move in self.exp.movement_manager.history]
    
    @property
    def values(self):
        return {el["name"]: el["value"] for el in self.exp.root_section.data.values()}
    
    @property
    def element_data(self):
        eldata = self.experiment.root_section.data
        return {**eldata}
    
    @property
    def session_data(self):
        d = {**self.metadata, **self.client_data}
        d["exp_data"] = self.element_data
        d["exp_move_history"] = self.move_history
        d["additional_data"] = self.additional_data
        return d
    
    @property
    def codebook_data(self) -> Dict[str, dict]:
        """dict: Returns codebook data for the current session."""
        exp = self.extract_codebook_data(self.session_data)
        unlinked = self.extract_codebook_data(self.unlinked_data)

        return {**exp, **unlinked}
    
    @staticmethod
    def extract_codebook_data(exp_data: dict) -> Dict[str, dict]:
        """ 
        Extracts codebook data from a full experiment data dictionary.

        Args:
            exp_data: Full experiment data dictionary, like the one
                returned by :attr:`.session_data`

        Returns:
            dict: A dictionary of dictionaries, containing detailed 
                information about the used elements.
        """
        meta = {}
        meta["alfred_version"] = exp_data["alfred_version"]
        meta["exp_author"] = exp_data["exp_author"]
        meta["exp_title"] = exp_data["exp_title"]
        meta["exp_version"] = exp_data["exp_version"]

        codebook = exp_data.pop("exp_data")
        for entry in codebook.values():
            entry.pop("value", None)
            entry.update(meta)
        
        return codebook
    
    @staticmethod
    def extract_fieldnames(data: Iterator) -> list:
        """
        Finds correct fieldnames for exporting multiple unlinked or
        codebook datasets to a single csv file.

        Args:
            data: A list or other iterator, providing the individual
                datasets
        
        Returns:
            list: List of fieldnames
        
        Note:
            The first scanned document determines the initial order of
            the fieldnames. Subsequently found additional fieldnames
            are simply appended.
        """
        fieldnames = {}
        for element in data:
            el = copy.copy(element)
            el.pop("_id", None) # remove mongoDB doc ID, if there is one
            fieldnames.update(el) 
        
        return list(fieldnames)
    
    @classmethod
    def extract_ordered_fieldnames(cls, data: Iterator) -> list:
        """ 
        Finds correct (and correctly ordered) fieldnames for exporting 
        multiple experiment datasets to a single csv file.

        Args:
            data: A list or other iterator providing the individual
                datasets. These need to be the full experiment datasets.

        Returns:
            list: List of fieldnames

        Notes:
            The fieldnames are ordered as follows:

            1. Experiment metadata
            2. Client info data
            3. Element data (ordered alphabetically by element name)
            4. Additional data

        """
        metadata = []
        client_info = []
        adata = []
        elements = {}

        for dataset in data:
            d = cls.flatten(copy.copy(dataset))

            for entry in list(d.keys()):
                if entry in cls.client_data:
                    d.pop(entry)
                    client_info.append(entry)
                elif entry in cls._metadata:
                    d.pop(entry)
                    metadata.append(entry)
                elif entry.startswith("additional_data"):
                    d.pop(entry)
                    adata.append(entry)
            elements.update(d)
        
        metadata = [name for name in metadata if not name.startswith("additional_data")]
        
        element_names = sorted(list(elements))
        metadata = sorted(list(set(metadata)))
        client_info = sorted(list(set(client_info)))
        adata = sorted(list(set(adata)))

        fieldnames = metadata + client_info + element_names + adata
        return fieldnames
    
    @staticmethod
    def sort_fieldnames(fieldnames: List[str], template: List[str]) -> List[str]:
        """
        Sorts the list fieldnames according to template.

        If fieldnames contains more fields than template, the returned
        list consists of a sorted part (the elements present in 
        *template*) and an appended part (the other elements, appended
        in their order of appearance in *fieldnames*).

        Args:
            fieldnames: List to sort
            template: Template list, indicating the desired order of
                the known elements in fieldnames.
        
        Returns:
            list: Sorted list
        
        Raises:
            ValueError: If either of the provided lists contain 
                duplicate values.
        """
        if len(set(fieldnames)) != len(fieldnames):
            raise ValueError("Input list must contain only unique elements.")
        
        if len(set(template)) != len(template):
            raise ValueError("Template list must contain only unique elements.")

        def find_position(name):
            try:
                return template.index(name)
            except ValueError:
                return len(template) + 1
        return sorted(fieldnames, key=find_position)
    
    @classmethod
    def sort_codebook_fieldnames(cls, fieldnames: List[str]) -> List[str]:

        t1 = ["exp_title", "exp_author", "exp_version", "alfred_version"]
        t2 = ["element_type", "name", "label_top", "label_left", "label_right", "label_bottom"]
        t3 = ["force_input", "default", "placeholder", "prefix", "suffix", "description"]

        template = t1 + t2 + t3

        return cls.sort_fieldnames(fieldnames, template)


    @staticmethod
    def flatten(data: dict) -> dict:
        eldata = data.pop("exp_data")
        data.pop("exp_move_history", None)
        data.pop("exp_plugin_queries", None)
        data.pop("_id", None)

        values = {}
        for name, elmnt in eldata.items():
            try:
                # if the value is a dictionary, like in multiple choice elements
                for subname, val in elmnt["value"].items():
                    values[f"{name}_{subname}"] = val
            except AttributeError:
                values[name] = elmnt["value"]
        
        adata = data.pop("additional_data", {})
        adata = flatten_dict(adata)
        
        maindata = {**data, **values}
        adata = prefix_keys_safely(data=adata, base=maindata, prefix="additional_data")
        return {**maindata, **adata}
    
    @staticmethod
    def regularize(data: dict) -> dict:
        pass

    @property
    def unlinked_data(self):
        data = {}
        data["type"] = self.UNLINKED_DATA
        data["exp_data"] = self._experiment.root_section.unlinked_data
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_id"] = self._experiment.exp_id
        data["exp_version"] = self._experiment.version
        data["alfred_version"] = self._experiment.alfred_version
        return data
    
    @property
    def unlinked_values(self):
        return {el["name"]: el["value"] for el in self.exp.root_section.unlinked_data.values()}

    
    def unlinked_data_with(self, saving_agent):
        if saving_agent.encrypt:
            return self.exp.data_manager.encrypt_values(self.unlinked_data)
        else:
            return self.unlinked_data
    
    @property
    def flat_session_data(self):
        return self.flatten(self.session_data)
    
    def flat_unlinked_data(self):
        return self.flatten(self.unlinked_data)
    
    def encrypt_values(self, data: dict) -> dict:
        data = copy.copy(data)
        for eldata in data["exp_data"].values():
            eldata["value"] = self.exp.encrypt(eldata["value"])
        return data
    
    def decrypt_values(self, data: dict) -> dict:
        data = copy.copy(data)
        for eldata in data["exp_data"].values():
            eldata["value"] = self.exp.decrypt(eldata["value"])
            return data
    
    def get_page_data(self, name: str) -> dict:
        return self.experiment.root_section.all_pages[name].data
    
    def get_section_data(self, name: str) -> dict:
        return self.experiment.root_section.all_subsections[name].data

    def iter_flat_mongo_data(self, data_type: str = "exp_data") -> Iterator[dict]:
        """ 
        Iterates over all datasets saved in the mongoDB associated with
        the experiment via its mongo_saving_agent.

        Args:
            data_type: Can be one of 'exp_data', or 'unlinked_data'

        Yields:
            dict: Flattened experiment data.
        """
        cursor = self.iterate_mongo_data(
            exp_id=self.exp.exp_id, 
            data_type=data_type, 
            secrets=self.exp.secrets
            )
        
        for dataset in cursor:
            yield self.flatten(dataset)
        
    def iter_flat_local_data(self, data_type: str = "exp_data") -> Iterator[dict]:
        """ 
        Iterates over all datasets saved via the experiment's
        local_saving_agent.

        Args:
            data_type: Can be one of 'exp_data', or 'unlinked_data'

        Yields:
            dict: Flattened experiment data
        """
        if data_type == "exp_data":
            path = self.exp.config.get("local_saving_agent", "path")
        elif data_type == "unlinked_data":
            path = self.exp.config.get("local_saving_agent_unlinked", "path")
        
        path = self.exp.subpath(path)
        cursor = self.iterate_local_data(data_type=data_type, directory=path)

        for dataset in cursor:
            yield self.flatten(dataset)
    
    @staticmethod
    def iterate_mongo_data(
        exp_id: str, data_type: str, secrets: ExperimentSecrets, exp_version: str = None
    ) -> Iterator[dict]:
        """Returns a MongoDB cursor, iterating over the experiment
        data in the database.

        .. versionadded:: 1.5

        Usage::
            cursor = data_manager.iterate_mongo_data(data_type="exp_dat")
            for doc in cursor:
                ...

        Args:
            exp_id: Experiment id
            data_type: The type of data to be collected. Can be 
                'exp_data', 'codebook', or 'unlinked'.
            secrets: Experiment secrets configuration object. This is
                used to extract information for database access.
            exp_version: If specified, data will only be queried for
                this specific version.
        """
        if data_type != "exp_data":
            section_name = f"mongo_saving_agent_{data_type}"
        else:
            section_name = "mongo_saving_agent"

        section = secrets.combine_sections("mongo_saving_agent", section_name)
        dbname = section["database"]
        colname = section["collection"]

        client = AutoMongoClient(section)
        db = client[dbname][colname]
        query = {"exp_id": exp_id, "type": data_type}

        if exp_version is not None:
            query["exp_version"] = exp_version

        return db.find(query)

    @classmethod
    def iterate_local_data(
        cls, data_type: str, directory: Union[str, Path], exp_version: str = None,
    ) -> Iterator[dict]:
        """Generator function, iterating over experiment data .json files
        in the specified directory.

        .. versionadded:: 1.5

        Usage::
            cursor = data_manager.collect_local_data(data_type="exp_data")
            for doc in cursor:
                ...

        Args:
            data_type: The type of data to be collected. Can be 
                'exp_data' or 'unlinked'.
            exp_version: If specified, data will only be queried for
                this specific version.
            directory: The directory in which to look for data.
        """
        path = Path(directory).resolve()
        if not path.is_absolute():
            raise ValueError("directory must be absolute")

        if not path.exists():
            return

        for fp in path.iterdir():
            if not fp.suffix == ".json":
                continue

            try:
                with open(fp, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except json.decoder.JSONDecodeError:
                continue
            except IsADirectoryError:
                continue

            doctype = doc.get("type")

            if data_type != doctype:
                continue

            yield doc

def decrypt_recursively(data: Union[list, dict, int, float, str, bytes], key: bytes) -> Union[list, dict, int, float, str, bytes]:
    """
    Used mainly for decrypting encrypted values in a nested dictionary.
    Can also decrypt single values.

    The encryption/decryption mechanism is symmetric.

    Returns:
        Decrypted object of the same type as the input.

    """
    f = Fernet(key=key)

    if isinstance(data, bytes):
        try:
            return f.decrypt(data)
        except InvalidToken:
            return data

    if isinstance(data, (int, float, str)):
        try:
            original_type = type(data)
            data_in_bytes = str(data).encode()
            decrypted_value = original_type(f.decrypt(data_in_bytes).decode())
            return decrypted_value
        except InvalidToken:
            return data

    elif isinstance(data, list):
        return [decrypt_recursively(entry, key=key) for entry in data]

    elif isinstance(data, dict):
        return {k: decrypt_recursively(v, key=key) for k, v in data.items()}



