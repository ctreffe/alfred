from builtins import map
from builtins import object
from flask import Flask, send_file, redirect, url_for, abort, request, make_response
import re

from ..settings import general, experiment

app = Flask(__name__)
if experiment.type == 'web':
    app.debug = general.debug


class C(object):
    experiment = None


script = C()
script.experiment = None
script.generator = None


def setExperiment(exp):
    script.experiment = exp


def setGenerator(generator):
    script.generator = generator


@app.route('/start', methods=['GET', 'POST'])
def start():
    exp = script.generator.generate_experiment()
    setExperiment(exp)
    exp.start()
    # html = exp.userInterfaceController.renderHtml() # Deprecated Command? Breaks Messages
    resp = make_response(redirect(url_for('experiment')))
    resp.cache_control.no_cache = True
    return resp


@app.route('/experiment', methods=['GET', 'POST'])
def experiment():

    move = request.values.get('move', None)
    directjump = request.values.get('directjump', None)
    par = request.values.get('par', None)

    kwargs = request.values.to_dict()
    kwargs.pop('move', None)
    kwargs.pop('directjump', None)
    kwargs.pop('par', None)

    if kwargs != {}:
        script.experiment.userInterfaceController.updateWithUserInput(kwargs)
    if move is None and directjump is None and par is None and kwargs == {}:
        pass
    elif directjump and par:
        posList = list(map(int, par.split('.')))
        script.experiment.userInterfaceController.moveToPosition(posList)
    elif move == 'started':
        pass
    elif move == 'forward':
        script.experiment.userInterfaceController.moveForward()
    elif move == 'backward':
        script.experiment.userInterfaceController.moveBackward()
    elif move == 'jump' and par and re.match('^\d+(\.\d+)*$', par):
        posList = list(map(int, par.split('.')))
        script.experiment.userInterfaceController.moveToPosition(posList)
    else:
        abort(400)

    html = script.experiment.userInterfaceController.renderHtml()
    resp = make_response(html)
    resp.cache_control.no_cache = True
    return resp


@app.route('/staticfile/<identifier>')
def staticfile(identifier):
    path, content_type = script.experiment.userInterfaceController.getStaticFile(identifier)
    resp = make_response(send_file(path, mimetype=content_type))
    return resp


@app.route('/dynamicfile/<identifier>')
def dynamicfile(identifier):
    strIO, content_type = script.experiment.userInterfaceController.getDynamicFile(identifier)
    resp = make_response(send_file(strIO, mimetype=content_type))
    resp.cache_control.no_cache = True
    return resp


@app.route('/callable/<identifier>', methods=['GET', 'POST'])
def callable(identifier):
    f = script.experiment.userInterfaceController.getCallable(identifier)
    if request.content_type == "application/json":
        values = request.get_json()
    else:
        values = request.values.to_dict()
    rv = f(**values)
    if rv is not None:
        resp = make_response(rv)
    else:
        resp = make_response(redirect(url_for('experiment')))
    resp.cache_control.no_cache = True
    return resp
