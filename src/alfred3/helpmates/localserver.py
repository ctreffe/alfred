from builtins import map, object
from builtins import callable as builtins_callable
from flask import Flask, send_file, redirect, url_for, abort, request, make_response, session, send_from_directory
from uuid import uuid4
from .. import settings
import re, os

app = Flask(__name__)
app.secret_key = "1327157a-0c8a-4e6d-becf-717a2a21cdba"
if settings.experiment.type == 'web':
    app.debug = settings.general.debug


class C(object):
    experiment = None


class Generator(object):

    def __init__(self, exp=None):
        self.experiment = exp

    def generate_experiment(self): # pylint: disable=method-hidden
        pass

    def set_experiment(self, exp):
        self.experiment = exp

    def set_generator(self, generator):
        # if the script.py contains generate_experiment directly, not as a class method
        if builtins_callable(generator):
            script.generator = Generator()
            self.generate_experiment = generator.__get__(self, Generator)
        # if the script.py contains Script.generate_experiment()
        elif builtins_callable(generator.generate_experiment):
            self.generate_experiment = generator.generate_experiment(self, Generator)

script = Generator()

@app.route('/start', methods=['GET', 'POST'])
def start():
    exp = script.generate_experiment(config=None)
    script.set_experiment(exp)
    script.experiment.start()
    
    session['page_tokens'] = []
    # html = exp.user_interface_controller.render_html() # Deprecated Command? Breaks Messages
    resp = make_response(redirect(url_for('experiment')))
    resp.cache_control.no_cache = True
    return resp


@app.route('/experiment', methods=['GET', 'POST'])
def experiment():

    if request.method == "POST":

        move = request.values.get('move', None)
        directjump = request.values.get('directjump', None)
        par = request.values.get('par', None)
        page_token = request.values.get('page_token', None)

        try:
            token_list = session['page_tokens']
            token_list.remove(page_token)
            session['page_tokens'] = token_list
        except ValueError:
            return redirect(url_for('experiment'))

        kwargs = request.values.to_dict()
        kwargs.pop('move', None)
        kwargs.pop('directjump', None)
        kwargs.pop('par', None)

        script.experiment.user_interface_controller.update_with_user_input(kwargs)
        if move is None and directjump is None and par is None and kwargs == {}:
            pass
        elif directjump and par:
            posList = list(map(int, par.split('.')))
            script.experiment.user_interface_controller.move_to_position(posList)
        elif move == 'started':
            pass
        elif move == 'forward':
            script.experiment.user_interface_controller.move_forward()
        elif move == 'backward':
            script.experiment.user_interface_controller.move_backward()
        elif move == 'jump' and par and re.match(r'^\d+(\.\d+)*$', par):
            posList = list(map(int, par.split('.')))
            script.experiment.user_interface_controller.move_to_position(posList)
        else:
            abort(400)
        return redirect(url_for('experiment'))

    elif request.method == "GET":
        page_token = str(uuid4())

        # this block extracts the list "page_tokens", if it exists in the session
        # it creates the list "page_tokens" as an empty list, if not. This is needed
        # for qt-wk experiments because they don't call the route /start
        try:
            token_list = session['page_tokens']
        except KeyError:
            token_list = []

        token_list.append(page_token)
        session['page_tokens'] = token_list

        html = script.experiment.user_interface_controller.render_html(page_token)
        resp = make_response(html)
        resp.cache_control.no_cache = True
        return resp

@app.route('/staticfile/<identifier>')
def staticfile(identifier):
    path, content_type = script.experiment.user_interface_controller.get_static_file(identifier)
    dirname, filename = os.path.split(path)
    resp = make_response(send_from_directory(dirname, filename, mimetype=content_type))
    return resp


@app.route('/dynamicfile/<identifier>')
def dynamicfile(identifier):
    strIO, content_type = script.experiment.user_interface_controller.get_dynamic_file(identifier)
    resp = make_response(send_file(strIO, mimetype=content_type))
    resp.cache_control.no_cache = True
    return resp


@app.route('/callable/<identifier>', methods=['GET', 'POST'])
def callable(identifier):
    f = script.experiment.user_interface_controller.get_callable(identifier)
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
