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


class DataManager(object):
    EXP_DATA = "exp_data"
    UNLINKED_DATA = "unlinked"
    CODEBOOK_DATA = "codebook"
    HISTORY = "move_history"

    instance_level_logging = False
    log = QueuedLoggingInterface(base_logger=__name__)

    def __init__(self, experiment):
        self._experiment = experiment
        self.exp = experiment
        self.additional_data = {}
        self.log.add_queue_logger(self, __name__)
        
        self.client_data = {}

        # the empty fields are initialized here below to enable name-
        # checking for all experiment members on these names
        self.client_data["client_resolution_screen"] = None
        self.client_data["client_resolution_inner"] = None
        self.client_data["client_referrer"] = None
        self.client_data["client_javascript_active"] = None
        self.client_data["client_device_type"] = None
        self.client_data["client_device_manufacturer"] = None
        self.client_data["client_device_family"] = None
        self.client_data["client_browser"] = None
        self.client_data["client_os_family"] = None
        self.client_data["client_os_name"] = None
        self.client_data["client_os_version"] = None

    @property
    def experiment(self):
        return self._experiment

    def add_additional_data(self, key, value):
        """Method for adding data to the additional data dictionary.

        .. deprecated:: 1.5
           Use the property
           :attr:`~alfred3.data_manager.DataManager.additional_data`
           directly instead.

        """

        self.additional_data[key] = value

    def get_additional_data_by_key(self, key):
        """Method for retrieving data from the additional data dictionary.

        .. deprecated:: 1.5
           Use the property
           :attr:`~alfred3.data_manager.DataManager.additional_data`
           directly instead.

        """
        return self.additional_data[key]

    @property
    def metadata(self):
        data = {}
        
        data["type"] = self.EXP_DATA
        data["alfred_version"] = self._experiment.alfred_version
        data["session_status"] = self._experiment.session_status
        
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_version"] = self._experiment.version
        data["exp_type"] = self._experiment.type
        data["exp_start_time"] = self._experiment.start_time
        data["exp_start_timestamp"] = self._experiment.start_timestamp
        data["exp_save_time"] = time.time()
        data["exp_finished"] = self._experiment.finished
        data["exp_session"] = self._experiment.session
        data["exp_condition"] = self._experiment.condition
        data["exp_id"] = self._experiment.exp_id
        data["exp_session_id"] = self._experiment.session_id
        
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
        # ul_eldata = self.experiment.root_section.unlinked_element_data
        return {**eldata}
    
    @property
    def session_data(self):
        d = {**self.metadata, **self.client_data}
        d["exp_data"] = self.element_data
        d["exp_move_history"] = self.move_history
        d["additional_data"] = self.additional_data
        return d
    
    @property
    def codebook_data(self) -> List[dict]:
        exp = self.extract_codebook_data(self.session_data)
        unlinked = self.extract_codebook_data(self.unlinked_data)

        return exp + unlinked
    
    @staticmethod
    def extract_codebook_data(exp_data: dict) -> List[dict]:
        meta = {}
        meta["alfred_version"] = exp_data["alfred_version"]
        meta["exp_author"] = exp_data["exp_author"]
        meta["exp_title"] = exp_data["exp_title"]
        meta["exp_version"] = exp_data["exp_version"]
        meta["exp_type"] = exp_data["exp_type"]

        codebook = exp_data.pop("exp_data")
        for entry in codebook.values():
            entry.pop("value", None)
            entry.update(meta)
        
        return [value for value in codebook.values()]
    
    @staticmethod
    def extract_fieldnames(data: dict) -> list:
        fieldnames = {}
        for element in data:
            fieldnames.update(element) 
        
        return list(fieldnames)

    @staticmethod
    def flatten(data: dict) -> dict:
        eldata = data.pop("exp_data")
        data.pop("exp_move_history", None)
        values = {name: elmnt["value"] for name, elmnt in eldata.items()}
        
        additional_data = data.pop("additional_data", {})

        return {**data, **values, **additional_data}

    @property
    def unlinked_data(self):
        data = {}
        data["type"] = self.UNLINKED_DATA
        data["exp_data"] = self._experiment.root_section.unlinked_data
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_id"] = self._experiment.exp_id
        data["exp_version"] = "__unlinked__"
        data["alfred_version"] = self.experiment.alfred_version
        data["exp_type"] = self._experiment.type
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

    def find_experiment_data_by_uid(self, uid):
        data = self._experiment._root_section.data
        return DataManager._find_by_uid(data, uid)

    def find_additional_data_by_key_and_uid(self, key, uid):
        data = self.additional_data[key]
        return DataManager._find_by_uid(data, uid)

    @staticmethod
    def _find_by_uid(data, uid):
        def worker(data, uid):
            if data["uid"] == uid:
                return data
            elif "subtree_data" in data:

                for item in data["subtree_data"]:
                    try:
                        d = worker(item, uid)
                        return d
                    except Exception:
                        if item == data["subtree_data"][-1]:
                            raise AlfredError("did not find uuid in tree")
                raise AlfredError("Custom Error")
            else:
                raise AlfredError("did not find uuid in tree")

        return worker(data, uid)

    def mongo_exp_data(self, data_type: str = "exp_data"):
        cursor = self.iterate_mongo_data(
            exp_id=self.exp.exp_id, 
            data_type=data_type, 
            secrets=self.exp.secrets
            )
        
        if data_type == "unlinked" and len(cursor) < 15:
            self.log.warning("Can't access unlinked data (too few datasets for unlinking).")
            return []
        
        return [self.flatten(dataset) for dataset in cursor]
    
    def local_exp_data(self, data_type: str = "exp_data"):
        if data_type == "exp_data":
            path = self.exp.config.get("local_saving_agent", "path")
        elif data_type == "unlinked_data":
            path = self.exp.config.get("local_saving_agent_unlinked", "path")
        
        path = self.exp.subpath(path)
        cursor = self.iterate_local_data(data_type=data_type, directory=path)

        if data_type == "unlinked" and len(cursor) < 15:
            self.log.warning("Can't access unlinked data (too few datasets for unlinking).")
            return []

        return [self.flatten(dataset) for dataset in cursor]
    
    @property
    def all_exp_data(self):
        return self.mongo_exp_data() + self.local_exp_data()
    
    @property
    def all_unlinked_data(self):
        return self.mongo_exp_data("unlinked") + self.local_exp_data("unlinked")
    
    @staticmethod
    def iterate_mongo_data(
        exp_id: str, data_type: str, secrets: ExperimentSecrets, exp_version: str = None
    ) -> Iterator[dict]:
        """Returns a MongoDB cursor, iterating over the experiment
        data in the database.

        .. versionadded:: 1.5

        Usage::
            cursor = data_manager.collect_mongo_data(data_type="exp_dat")
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
                'exp_data', 'codebook', or 'unlinked'.
            exp_version: If specified, data will only be queried for
                this specific version.
            directory: The directory in which to look for data.
        """
        path = Path(directory).resolve()
        if not path.is_absolute():
            raise ValueError("directory must be absolute")

        if not path.exists():
            cls.log.warning(f"{path} is not a directory.")
            return

        for fp in path.iterdir():
            if not fp.suffix == ".json":
                continue

            try:
                with open(fp, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except json.decoder.JSONDecodeError:
                cls.log.warning(f"Skipped file '{fp}' (not valid .json).")
                continue
            except IsADirectoryError:
                cls.log.debug(f"Skipped '{fp}' (not a directory).")
                continue

            doctype = doc.get("type")

            if data_type != doctype:
                continue

            yield doc


class DataDecryptor:
    """Used for decrypting encrypted values in a nested dictionary.
    
    The encryption/decryption mechanism is symmetric. The decryptor 
    needs to be initialized with a valid key.
    
    Use the method :meth:`decrypt` for decryption.
    """

    def __init__(self, key):
        self.f = Fernet(key=key)

    def decrypt(self, data):

        if isinstance(data, bytes):
            try:
                decrypted_value = self.f.decrypt(data)
                return decrypted_value
            except InvalidToken:
                return data

        if isinstance(data, (int, float, str)):
            try:
                original_type = type(data)
                data_in_bytes = str(data).encode()
                decrypted_value = original_type(self.f.decrypt(data_in_bytes).decode())
                return decrypted_value
            except InvalidToken:
                return data

        elif isinstance(data, list):
            derypted_list = []
            for entry in data:
                derypted_list.append(self.decrypt(entry))
            return derypted_list

        elif isinstance(data, dict):
            decrypted_dict = {}
            for k, v in data.items():
                decrypted_dict[k] = self.decrypt(v)
            return decrypted_dict
