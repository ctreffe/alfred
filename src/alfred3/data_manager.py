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

from pathlib import Path
from builtins import object
from typing import Union
from cryptography.fernet import Fernet, InvalidToken

from .exceptions import AlfredError
from .config import ExperimentSecrets


class DataManager(object):
    EXP_DATA = "exp_data"
    UNLINKED_DATA = "unlinked"
    CODEBOOK_DATA = "codebook"

    def __init__(self, experiment):
        self._experiment = experiment
        self._additional_data = {}

    def add_additional_data(self, key, value):
        self._additional_data[key] = value

    def get_additional_data_by_key(self, key):
        return self._additional_data[key]

    def get_data(self):
        data = self._experiment.page_controller.data
        data["type"] = self.EXP_DATA
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_version"] = self._experiment.version
        data["exp_type"] = self._experiment.type
        data["start_time"] = self._experiment.start_time
        data["start_timestamp"] = self._experiment.start_timestamp
        data["exp_finished"] = self._experiment.finished
        data["exp_session"] = self._experiment.session
        data["exp_condition"] = self._experiment.condition
        data["exp_id"] = self._experiment.exp_id
        data["session_id"] = self._experiment.session_id
        data["session_status"] = self._experiment.session_status
        data["additional_data"] = self._additional_data
        data["alfred_version"] = self._experiment.alfred_version
        data["save_time"] = time.time()

        return data

    def get_unlinked_data(self, encrypt=False):
        data = self._experiment.page_controller.unlinked_data(encrypt=encrypt)
        data["type"] = self.UNLINKED_DATA
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_id"] = self._experiment.exp_id

        return data

    def get_codebook_data(self):
        data = {}
        data["codebook"] = self._experiment.page_controller.codebook_data
        data["type"] = self.CODEBOOK_DATA
        data["exp_id"] = self._experiment.exp_id
        data["exp_author"] = self._experiment.author
        data["exp_title"] = self._experiment.title
        data["exp_version"] = self._experiment.version
        data["alfred_version"] = self._experiment.alfred_version
        data["save_time"] = time.time()
        return data

    def find_experiment_data_by_uid(self, uid):
        data = self._experiment._page_controller.data
        return DataManager._find_by_uid(data, uid)

    def find_additional_data_by_key_and_uid(self, key, uid):
        data = self._additional_data[key]
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


class CodeBookExporter:
    """Used to turn the codebook data into .csv format
    
    Usage:
    1. Initialize
    2. Process codebook via :meth:`process`
    3. Use :meth:`write_to_file` or :meth:`write_to_object` to create
        the csv file / object. 
    """

    ORDER = {
        "alfred_version": "0a",
        "exp_author": "0b",
        "exp_title": "0c",
        "exp_version": "0d",
        "exp_id": "0d1",
        "page_title": "0d2",
        "identifier": "0e",
        "tree": "0f",
        "name": "0g",
        "element_type": "0h",
        "instruction": "0i",
        "desctiption": "0j",
        "default": "0k",
        "force_input": "0l",
        "description": "0m",
        "prefix": "0n",
        "suffix": "0o",
        "item": "1a",
        "n_levels": "1b",
        "item_label_left": "1c",
        "item_label_right": "1c1",
        "top_labels": "1d",
        "bottom_labels": "1e",
        "shuffle": "1f",
        "transposed": "1g",
        "unlinked": "z1",
        "duplicate_identifier": "z2",
    }

    def __init__(self):
        self.meta = None
        self.codebook = None
        self.sorted = None
        self.fieldnames = None

    @property
    def full_codebook(self):
        return {**self.meta, "codebook": self.codebook}

    def reset(self):
        self.meta = None
        self.codebook = None
        self.sorted = None
        self.fieldnames = None

    def process(self, raw: dict, dot_notation: bool = True):
        self.meta = raw
        self.meta.pop("save_time")
        data_type = self.meta.pop("type")
        if not data_type == DataManager.CODEBOOK_DATA:
            return
        try:
            self.meta.pop("_id")  # remove ID in case of MongoDB download
            self.meta.pop("_default_id")
        except KeyError:
            pass

        if dot_notation:
            cb = self.meta.pop("codebook")
            d = {}
            for key, value in cb.items():
                dot_tree = value["tree"].replace("_", ".")
                dot_identifier = dot_tree + "." + value["name"]

                value["tree"] = dot_tree
                value["identifier"] = dot_identifier
                d[key] = value
            self.codebook = d
        else:
            self.codebook = self.meta.pop("codebook")

        self._find_fieldnames()
        self._sort_fieldnames()

    def _find_fieldnames(self):
        names = set(self.meta)

        for el in self.codebook.values():
            for k in el.keys():
                names.add(k)

        self.fieldnames = list(names)

    def _sort_helper(self, item: str):
        try:
            return str(self.ORDER[item])
        except KeyError:
            return item

    def _sort_fieldnames(self):
        self.fieldnames.sort(key=lambda item: self._sort_helper(item))

    def write_to_file(self, csvfile, **kwargs):

        with open(csvfile, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames, **kwargs)
            writer.writeheader()

            for element in self.codebook.values():
                writer.writerow({**self.meta, **element})

    def write_to_object(self, **kwargs) -> io.StringIO:
        csvfile = io.StringIO()
        writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, **kwargs)
        writer.writeheader()

        for element in self.codebook.values():
            writer.writerow({**self.meta, **element})

        return csvfile

    @property
    def list_of_docs(self):
        out = list()
        for element in self.codebook.values():
            out.append({**self.meta, **element})

        return out

    def write_local_data_to_file(
        self,
        in_file: Union[str, Path],
        out_dir: Union[str, Path],
        csv_name: str = None,
        overwrite: bool = False,
        **kwargs,
    ):
        """Export codebook data from a local .json file to a .csv file
        
        If the *in_file* is not an absolute path, it is assumed that it resides in
        the current working directory.

        Args:
            in_file: The .json file to export.
            out_dir: The .csv file will be placed in this directory.
            csv_name: Name of the .csv file.
            overwrite: If true, existing files of the name *csv_name* 
                will be overwritten.
        """
        if csv_name and overwrite:
            csv_name = csv_name
        elif csv_name and not overwrite:
            csv_name = find_unique_name(directory=out_dir, filename=csv_name)
        elif not csv_name and overwrite:
            csv_name = Path(in_file).name.replace(".json", ".csv")
        else:
            csv_name = find_unique_name(
                directory=out_dir, filename=Path(in_file).name.replace(".json", ".csv")
            )

        in_file = Path(in_file).resolve()

        if not in_file.is_absolute():
            in_file = Path.cwd() / in_file

        outfile = Path(out_dir) / csv_name

        try:
            with open(in_file, "r") as f:
                doc = json.load(f)
        except json.decoder.JSONDecodeError:
            self.reset()
            return
        except IsADirectoryError:
            return

        if not doc.get("type") == DataManager.CODEBOOK_DATA:
            self.reset()
            return

        self.process(doc)
        self.write_to_file(outfile, delimiter=kwargs.get("delimiter", ","))

    def write_mongo_data_to_file(
        self, collection, exp_id, exp_version, out_dir: Union[str, Path], csv_name: str, **kwargs
    ):
        """Export codebook data from a MongoDB collection and save to a
        .csv file.
        
        Args:
            collection: A pymongo collection object, containig the data.
            exp_id: ID of the experiment whose data will be exported.
            out_dir: The .csv file will be placed in this directory.
            csv_name: Name of the .csv file.
            data_type: A string, specifying the data type to
                export (generally, either 'exp_data' or 'unlinked').
        """

        if csv_name:
            csv_name = find_unique_name(
                directory=out_dir, filename=csv_name, exp_version=exp_version
            )
        else:
            csv_name = find_unique_name(
                directory=out_dir, filename="codebook.csv", exp_version=exp_version
            )

        outfile = Path(out_dir) / csv_name

        doc = collection.find_one(
            {"exp_id": exp_id, "exp_version": exp_version, "type": DataManager.CODEBOOK_DATA}
        )
        self.process(doc)
        self.write_to_file(outfile, delimiter=kwargs.get("delimiter", ","))


class ExpDataExporter:
    """Used to turn experiment data dictionaries into easier to handle 
    formats.
    
    Usage:
    1. Initialize without arguments
    2. Use the method :meth:`process_one` or :meth:`process_many`.
    
    Then, you have several options:

    - Access the data directly via the :attr:`list_of_docs`, a list of
        flattened dictionaries, where each dictionary contains the
        data from one experiment session.
    - Access the data directly via the :attr:`list_of_lists`. The first
        entry in this list contains the variable names. The subsequent
        entries each contain the values of one session.
    - Write in .csv format to an object via :meth:`write_to_object`
    - Write in .csv format to a file via :meth:`write_to_file`
    """

    def __init__(self):
        self.meta_data_names = dict()
        self.subtree_data_names = dict()
        self.additional_data_names = dict()

        self.list_of_docs = []

    @property
    def list_of_lists(self):
        """Returns the experiment data as a list of lists.
        
        The first sublist contains the variable names. The subsequent
        sublists each contain the values for one session.
        """

        if not self.list_of_docs:
            raise ValueError("List of documents is empty.")

        out = []

        header = list(self.list_of_docs[0])
        out.append(header)

        for doc in self.list_of_docs:
            out.append(list(doc.values()))

        return out

    @property
    def fieldnames(self):
        fieldnames = sorted(list(self.meta_data_names))
        fieldnames += sorted(list(self.subtree_data_names))
        fieldnames += sorted(list(self.additional_data_names))
        return fieldnames

    def process_many(self, docs: list, add_to_instance=True, **pageargs) -> list:
        """Processes a list of data dictionaries containing alfred
        experiment data.
        
        Returns a list of flattened dictionaries.
        """
        for doc in docs:
            self.process_one(doc, **pageargs)

        return self.list_of_docs

    def process_one(self, doc, add_to_instance=True, **pageargs) -> dict:
        """Processes a dictionary containing alfred experiment data.
        
        The dict is flattened and returned.
        The fields 'tag', 'type', and 'uid' are removed.

        
        pageargs:
            remove_linebreaks: Indicates, whether ``\\n`` should be removed
                    from strings. Defaults to `False`.
            missings: An optional value to be inserted for missing values.
                Defaults to `None`.
            dot_notation: Indicates, whether the section tree in the
                variable name should be written with dots or underscores 
                as separation symbols. Defaults to `True`.
        """

        try:
            additional_data_raw = doc.pop("additional_data")
            additional_data = self._process_additional_data(
                data=additional_data_raw, remove_linebreaks=pageargs.get("remove_linebreaks")
            )
        except KeyError:
            additional_data = {}

        subtree_data_raw = doc.pop("subtree_data")
        subtree_data = self._process_subtree(subtree=subtree_data_raw, **pageargs)

        meta_data = doc
        meta_data.pop("type")
        meta_data.pop("tag")
        # meta_data.pop("uid")
        try:
            meta_data.pop("_id")
            meta_data.pop("_default_id")
        except KeyError:
            pass
        try:
            meta_data.pop("_unlinked_id")
        except KeyError:
            pass

        # add names to dicts (used as ordered sets) for fieldnames in csv writer
        [self.meta_data_names.update({entry: None}) for entry in meta_data]
        [self.subtree_data_names.update({entry: None}) for entry in list(subtree_data)]
        [self.additional_data_names.update({entry: None}) for entry in list(additional_data)]

        full_data = {**meta_data, **subtree_data, **additional_data}

        if add_to_instance:
            self.list_of_docs.append(full_data)

        return full_data

    def _process_additional_data(self, data: dict, remove_linebreaks: bool = False):
        d = {}
        for k, v in data.items():
            if remove_linebreaks and isinstance(v, str):
                v = v.replace("\n", "")
            d[f"additional_data.{k}"] = v
        return d

    def _process_subtree(self, subtree: list, **pageargs):
        """Recursive function that processes subtree data.
        Returns a flat dictionary with all element data belonging to
        an experiment, identified by unique keys.
        
        The keys are a combination of the element name and its tree, 
        i.e. its position in the experiment.
        """

        d = {}

        for branch in subtree:
            if "subtree_data" in branch:
                branch_subtree = branch.pop("subtree_data")
                subtree_data = self._process_subtree(subtree=branch_subtree, **pageargs)
                d.update(subtree_data)
                continue

            page_data = self._process_one_page(
                page=branch,
                remove_linebreaks=pageargs.get("remove_linebreaks"),
                missings=pageargs.get("missings"),
            )
            d.update(page_data)

        return d

    @staticmethod
    def _process_one_page(
        page: dict,
        remove_linebreaks: bool = False,
        missings: str = None,
        dot_notation: bool = True,
    ) -> dict:
        """Returns a dictionary of page data, with keys containing the 
        page's tree (which indicates its position in the experiment).
        That way, the keys are experiment-wide unique.
        
        Args:
            page: Dictionary of page data.
            remove_linebreaks: Indicates, whether `\n` should be removed
                from strings.
            missings: An optional value to be inserted for missing values.
            dot_notation: Indicates, whether the section tree in the
                variable name should be written with dots or underscores 
                as separation symbols.
        """
        tree = page.pop("tree")
        try:
            page.pop("tag")
            page.pop("uid")
        except KeyError:
            pass

        d = {}
        for key, value in page.items():
            if remove_linebreaks and isinstance(value, str):
                value = value.replace("\n", "")
            if not value:

                value = missings

            if dot_notation:
                insert_key = tree.replace("_", ".") + "." + key
            else:
                insert_key = f"{tree}_{key}"

            d[insert_key] = value

        return d

    def write_to_object(self, shuffle=False, **writer_args) -> io.StringIO:
        if shuffle:
            random.shuffle(self.list_of_docs)

        csvfile = io.StringIO()

        writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, **writer_args)
        writer.writeheader()
        writer.writerows(self.list_of_docs)

        return csvfile

    def write_to_file(self, csvfile, shuffle=False, **writer_args):
        if shuffle:
            random.shuffle(self.list_of_docs)

        with open(csvfile, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames, **writer_args)
            writer.writeheader()
            writer.writerows(self.list_of_docs)

    def write_local_data_to_file(
        self,
        in_dir: Union[str, Path],
        out_dir: Union[str, Path],
        data_type: str = None,
        csv_name: str = None,
        overwrite: bool = False,
        **kwargs,
    ):
        """Exports experiment or unlinked data from all .json files in a 
        the directory *in_dir* to a .csv file.

        The function expects that only .json files of one type 
        (experiment data or unlinked data) are present in *in_dir*. 
        If multiple types are present, the function will raise a ValueError.
        
        You can manually specify the *data_type* that you want to export.

        Args:
            in_dir: This directory will be scanned for .json files with
                a fitting 'type' field. If it is not absolute, it is
                assumed that *in_dir* is a subdirectory of the current
                working directory.
            out_dir: The .csv file will be placed in this directory.
            data_type: An optional string, specifying the data type to
                export (generally, either 'exp_data' or 'unlinked').
            csv_name: Name of the .csv file.
            overwrite: If true, existing files of the name *csv_name* 
                will be overwritten.
        """

        if csv_name and overwrite:
            csv_name = csv_name
        elif csv_name and not overwrite:
            csv_name = find_unique_name(directory=out_dir, filename=csv_name)
        elif not csv_name and overwrite:
            csv_name = f"{data_type}.csv"
        else:
            csv_name = find_unique_name(directory=out_dir, filename=f"{data_type}.csv")

        in_dir = Path(in_dir).resolve()
        if not in_dir.is_absolute():
            in_dir = Path.cwd() / in_dir

        if not in_dir.exists():
            return

        type_previous = None
        for filename in os.listdir(in_dir):
            if not filename.endswith(".json"):
                continue

            fp = Path(in_dir) / filename

            try:
                with open(fp, "r") as f:
                    doc = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f"Skipped file '{fp}' (not valid .json).")
                continue
            except IsADirectoryError:
                continue

            type_current = doc.get("type")

            if not type_current in [DataManager.EXP_DATA, DataManager.UNLINKED_DATA]:
                continue

            if data_type and not data_type == type_current:
                continue

            if type_previous and not type_current == type_previous:
                raise ValueError(
                    "Different data types found in directory. Please specify the 'type' parameter."
                )

            type_previous = type_current

            self.process_one(doc, **kwargs)

        csvfile = Path(out_dir) / csv_name
        shuffle = True if data_type == "unlinked" else False
        self.write_to_file(csvfile, shuffle=shuffle, delimiter=kwargs.get("delimiter", ","))

    def write_mongo_data_to_file(
        self,
        collection,
        exp_id: str,
        out_dir: Union[str, Path],
        data_type: str,
        csv_name: str = None,
        **kwargs,
    ):
        """Exports experiment data from a MongoDB collection to a .csv 
        file.
        
        Args:
            collection: A pymongo collection object, containig the data.
            exp_id: ID of the experiment whose data will be exported.
            out_dir: The .csv file will be placed in this directory.
            data_type: A string, specifying the data type to
                export (generally, either 'exp_data' or 'unlinked').
            csv_name: Name of the .csv file.
        """
        if csv_name:
            csv_name = find_unique_name(directory=out_dir, filename=csv_name)
        else:
            csv_name = find_unique_name(directory=out_dir, filename=f"{data_type}.csv")
        outfile = Path(out_dir) / csv_name

        docs = list(collection.find({"exp_id": exp_id, "type": data_type}))
        self.process_many(docs, **kwargs)
        self.write_to_file(outfile, delimiter=kwargs.get("delimiter", ","))


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
