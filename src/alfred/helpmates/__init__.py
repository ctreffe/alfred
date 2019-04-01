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


def parseXmlToDict(path, interface='web'):
    '''
    parseXmlTpDict ermöglicht das Einlesen von XML in Dictionaries.

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

    dataIn = open(path, 'rb').read()
    dataIn.replace('\r\n', '\n')
    dataOut = xmltodict.parse(dataIn)
    if interface == 'web':
        rec(dataOut, '<br>')
    elif interface == 'qt':
        rec(dataOut, '\n')
    else:
        raise ValueError('interface must be either "qt" or "web".')
    for k in list(dataOut['instr'].keys()):
        if k == 'instr':
            raise RuntimeError("Do not use 'instr' as tag")
        dataOut[k] = dataOut['instr'][k]
    return dataOut


def readCSVData(path):
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


def findExternalExperimentDataByUid(data, uid):
    def worker(data, uid):
        if data['uid'] == uid:
            return data
        elif 'subtreeData' in data:
            for item in data['subtreeData']:
                try:
                    d = worker(item, uid)
                    return d
                except Exception:
                    if item == data['subtreeData'][-1]:
                        raise AlfredError("did not find uuid in tree")
            raise AlfredError("Custom Error")
        else:
            raise AlfredError("did not find uuid in tree")
    return worker(data, uid)


def absExternalFilePath(filename):
    path = join(settings.general.external_files_dir, filename)
    path = abspath(path)
    return path
