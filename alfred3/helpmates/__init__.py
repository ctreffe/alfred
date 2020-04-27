# -*- coding:utf-8 -*-

"""
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

A package for convenience functions
"""
from __future__ import print_function

import csv
import re
import socket
from os.path import abspath, isabs, isfile, join

import xmltodict
from future import standard_library

from alfred3 import alfredlog, settings
from alfred3.exceptions import AlfredError

standard_library.install_aliases()

logger = alfredlog.getLogger(__name__)


def parse_xml_to_dict(path, interface="web", code=False):
    """
    parse_xml_to_dict ermöglicht das Einlesen von XML in Dictionaries.

    die Variable Interface legt fest, wie Dictionary-Einträge
    optimiert werden. Vorerst geht es dabei nur um die Übersetzung
    von LineBreak anweisungen für Qt oder HTML.

    Das Dictionary wird abschließend daraufhin optimiert, dass
    keine Value mit einem LineBreak beginnt.

    So kann man Text schreiben, der nicht geparst wird, so dass
    z.B. html Anweisungen normal interpretiert werden können:

    <![CDATA[
    some input with html code
    ]]>
    """

    # if there is no file to be found under the given path, the function
    # tries to look for the file in the "external files directory".
    # This used to be default behavior.
    # The new implementation allows for smoother handling of multiple
    # directories and should be backwards-compatible in most cases.
    # If issues are suspectetd, a warning is logged.
    path2 = join(settings.general.external_files_dir, path)
    if isfile(path) and isfile(path2) and not path == path2:
        logger.warning(
            "parse_xml_to_dict: There is a file {p1}, but there is also a file {p2} in the external files directory. Previous versions of Alfred would have used {p2} by default, now {p1} is used. Please make sure that you are importing the correct file.".format(
                p1=path, p2=path2
            )
        )

    if not isfile(path):
        path = path2
        logger.warning(
            "parse_xml_to_dict: Found no file under {p1}. Searching under {p2} now.".format(
                p1=path, p2=path2
            )
        )

    def rec(input, replacement="<br>"):
        if isinstance(input, str):
            if input[0] == "\n":
                input = input[1:]
            if input[-1] == "\n":
                input = input[:-1]
            input = input.replace("\n", replacement)
        elif isinstance(input, dict):
            for k in input:
                input[k] = rec(input[k], replacement)
        else:
            raise RuntimeError("input must be unicode or dict")
        return input

    with open(path, "r", encoding="utf-8") as f:
        data_in = f.read().replace("\r\n", "\n")

    data_out = xmltodict.parse(data_in)

    if interface == "web" and not code:
        rec(data_out, "<br>")
    elif interface == "qt" and not code:
        rec(data_out, "\n")
    elif (interface == "web" or interface == "qt") and code:
        pass
    else:
        raise ValueError('interface must be either "qt" or "web".')

    for k in list(data_out["instr"].keys()):
        if k == "instr":
            raise RuntimeError("Do not use 'instr' as tag")
        data_out[k] = data_out["instr"][k]

    return data_out


def read_csv_data(path: str, delimiter: str = ";", **kwargs) -> list:
    """
    Diese Funktion ermöglicht das Einlesen von Datensätzen,
    die innerhalb des Experimentes gebraucht werden, z.B.
    verschiedene Schätzaufgaben eines Typs, die dann der VP
    randomisiert dargeboten werden. Die Daten müssen dabei
    als .csv Datei gespeichert sein. Das Trennzeichen ist Standardmäßig ";" 
    und kann im Funktionsaufruf spezifiziert werden.

    Leere Zeilen werden ignoriert.

    Die Funktion muss mit dem Dateinamen der entsprechenden
    Datei aufgerufen werden und gibt ein Array of
    Arrays zurück (Toplevel sind die einzelnen Lines, darin
    enthalten dann ein Array mit den verschiedenen Spalten)

    """

    if not isabs(path):
        path = join(settings.general.external_files_dir, path)

    out = []
    with open(path, "r", encoding="utf-8") as f:
        file_reader = csv.reader(f, delimiter=delimiter, **kwargs)

        for row in file_reader:
            if row:
                out.append(row)

    return out


def find_external_experiment_data_by_uid(data, uid):
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


def abs_external_file_path(filename):
    path = join(settings.general.external_files_dir, filename)
    path = abspath(path)
    return path


def socket_checker(port):
    try:
        s = socket.socket()
        s.bind(("127.0.0.1", port))
        s.listen(1)
        s.close()
        return True
    except Exception:
        s.close()
        return False


# These functions import external .html, .css and .js files
# .decode('utf-8') is needed to display special characters such as €, ä, etc.
# .replace("\n", "") is used to collapse the file to a single line, so that we can easily use it elsewhere in alfred
# re.sub() is used to remove comments from the code, because they would cause problems in the single line objects

# ------------------------------------------------------------------- #
# --- FUNCTION FOR READING IN HTML FILES --- #
# ------------------------------------------------------------------- #


def read_html(file):

    with open(file, "r") as f:
        data = f.read().decode("utf-8")
        no_comments = re.sub(r"<--(.|\n)*-->", "", data)  # remove comments
        out = no_comments.replace("\n", "")  # collapse to one line

    return out


# ------------------------------------------------------------------- #
# --- FUNCTION FOR READING IN CSS FILES --- #
# ------------------------------------------------------------------- #


def read_css(file):

    with open(file, "r") as f:
        data = f.read().decode("utf-8")
        no_comments = re.sub(r"/\*(.|\n)*\*/", "", data)  # remove comments
        out = no_comments.replace("\n", "")  # collapse to one line

    return out


# ------------------------------------------------------------------- #
# --- FUNCTION FOR READING IN JAVASCRIPT FILES --- #
# ------------------------------------------------------------------- #


def read_js(file):

    with open(file, "r") as f:
        data = f.read().decode("utf-8")
        no_comments = re.sub(r"(//.*)|(/\*(.|\n)*\*/)", "", data)  # remove comments
        out = no_comments.replace("\n", "")  # collapse to one line

    return out
