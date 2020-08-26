from pprint import pprint

import csv
import json
import io


class CodeBookExporter:
    """Used to turn the codebook data into .csv format
    
    Usage:
    1. Initialize with codebook data dictionary
    2. Use :meth:`write_to_file` or :meth:`write_to_object` to create
        the csv file / object. 
    """

    ORDER = {
        "alfred_version": "0a",
        "exp_author": "0b",
        "exp_title": "0c",
        "exp_version": "0d",
        "identifier": "0e",
        "tree": "0f",
        "name": "0g",
        "element_type": "0h",
        "instruction": "0i",
        "desctiption": "0j",
        "default": "0k",
        "force_input": "0l",
        "description": "0m",
        "page_title": "0n",
    }

    def __init__(self, raw: dict):
        self.meta = raw
        self.meta.pop("save_time")
        self.meta.pop("type")
        self.codebook = self.meta.pop("codebook")

        self.sorted = None
        self.fieldnames = None

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
        writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, **kwargs)
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


class ExpDataExporter:
    """Used to turn experiment data dictionaries into easier to handle 
    formats.
    
    Usage:
    1. Initialize without arguments
    2. Use the method :meth:`process`, passing experiment data 
        dictionaries as arguments.
    
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
        fieldnames = list(self.meta_data_names)
        fieldnames += list(self.subtree_data_names)
        fieldnames += list(self.additional_data_names)
        return fieldnames

    def process_many(self, docs: list, add_to_instance=True) -> list:
        """Processes a list of data dictionaries containing alfred
        experiment data.
        
        Returns a list of flattened dictionaries.
        """
        for doc in docs:
            self.process_one(doc)

        return self.list_of_docs

    def process_one(self, doc, add_to_instance=True) -> dict:
        """Processes a dictionary containing alfred experiment data.
        
        The dict is flattened and returned.
        """

        try:
            additional_data_raw = doc.pop("additional_data")
            additional_data = self._process_additional_data(data=additional_data_raw)
        except KeyError:
            additional_data = {}

        subtree_data_raw = doc.pop("subtree_data")
        subtree_data = self._process_subtree(subtree=subtree_data_raw)

        meta_data = doc
        meta_data.pop("tag")
        meta_data.pop("type")
        meta_data.pop("uid")

        # add names to dicts (used as ordered sets) for fieldnames in csv writer
        [self.meta_data_names.update({entry: None}) for entry in list(meta_data)]
        [self.subtree_data_names.update({entry: None}) for entry in list(subtree_data)]
        [self.additional_data_names.update({entry: None}) for entry in list(additional_data)]

        full_data = {**meta_data, **subtree_data, **additional_data}

        if add_to_instance:
            self.list_of_docs.append(full_data)

        return full_data

    def _process_additional_data(self, data: dict):
        d = {}
        for k, v in data.items():
            d[f"additional_data.{k}"] = v
        return d

    def _process_subtree(self, subtree: list):
        """Recursive function that processes subtree data.
        Returns a flat dictionary with all element data belonging to
        an experiment, identified by unique keys.
        
        The keys are a combination of the element name and its tree, 
        i.e. its position in the experiment."""

        d = {}

        for branch in subtree:
            if "subtree_data" in branch:
                branch_subtree = branch.pop("subtree_data")
                subtree_data = self._process_subtree(subtree=branch_subtree)
                d.update(subtree_data)
                continue

            page_data = self._process_one_page(page=branch)
            d.update(page_data)

        return d

    @staticmethod
    def _process_one_page(page: dict) -> dict:
        """Returns a dictionary of page data, with keys containing the 
        page's tree (which indicates its position in the experiment).
        That way, the keys are experiment-wide unique."""
        page.pop("tag")
        page.pop("uid")
        tree = page.pop("tree")

        d = {}
        for k, v in page.items():
            d[f"{tree}.{k}"] = v

        return d

    def write_to_object(self, **kwargs) -> io.StringIO:
        csvfile = io.StringIO()

        writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, **kwargs)
        writer.writeheader()
        writer.writerows(self.list_of_docs)

        return csvfile

    def write_to_file(self, csvfile, **kwargs):
        writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, **kwargs)
        writer.writeheader()
        writer.writerows(self.list_of_docs)

