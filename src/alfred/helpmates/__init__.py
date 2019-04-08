# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

A package for convenience functions
'''
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from os.path import abspath, isabs, join
import xmltodict
import csv
from alfred.exceptions import AlfredError
import alfred.settings as settings


def parse_xml_to_dict(path, interface='web'):
    '''
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
    '''

    if not isabs(path):
        path = join(settings.general.external_files_dir, path)

    def rec(input, replacement='<br>'):
        if isinstance(input, str):
            if input[0] == '\n':
                input = input[1:]
            if input[-1] == '\n':
                input = input[:-1]
            input = input.replace('\n', replacement)
        elif isinstance(input, dict):
            for k in input:
                input[k] = rec(input[k], replacement)
        else:
            raise RuntimeError('input must be unicode or dict')
        return input

    data_in = open(path, 'rb').read()
    data_in.replace('\r\n', '\n')
    data_out = xmltodict.parse(data_in)
    if interface == 'web':
        rec(data_out, '<br>')
    elif interface == 'qt':
        rec(data_out, '\n')
    else:
        raise ValueError('interface must be either "qt" or "web".')
    for k in list(data_out['instr'].keys()):
        if k == 'instr':
            raise RuntimeError("Do not use 'instr' as tag")
        data_out[k] = data_out['instr'][k]
    return data_out


def read_csv_data(path):
    """
    Diese Funktion ermöglicht das Einlesen von Datensätzen,
    die innerhalb des Experimentes gebraucht werden, z.B.
    verschiedene Schätzaufgaben eines Typs, die dann der VP
    randomisiert dargeboten werden. Die Daten müssen dabei
    als .csv Datei gespeichert sein. Dabei muss als Trenn-
    zeichen ein Semikolon ';' benutzt werden!

    Die Funktion muss mit dem Dateinamen der entsprechenden
    Datei aufgerufen werden und gibt ein Array of
    Arrays zurück (Toplevel sind die einzelnen Lines, darin
    enthalten dann ein Array mit den verschiedenen Spalten)

    """

    if not isabs(path):
        path = join(settings.general.external_files_dir, path)

    dataset = []
    file_input = open(path, 'r')

    file_reader = csv.reader(file_input, delimiter=';')

    for row in file_reader:

        temprow = []
        while row != []:
            tempstr = row.pop(0)
            tempstr = tempstr.decode('latin-1')
            temprow.append(tempstr)
        row = temprow
        dataset.append(row)

    dataset.pop(0)

    return dataset


def find_external_experiment_data_by_uid(data, uid):
    def worker(data, uid):
        if data['uid'] == uid:
            return data
        elif 'subtree_data' in data:
            for item in data['subtree_data']:
                try:
                    d = worker(item, uid)
                    return d
                except Exception:
                    if item == data['subtree_data'][-1]:
                        raise AlfredError("did not find uuid in tree")
            raise AlfredError("Custom Error")
        else:
            raise AlfredError("did not find uuid in tree")
    return worker(data, uid)


def abs_external_file_path(filename):
    path = join(settings.general.external_files_dir, filename)
    path = abspath(path)
    return path
