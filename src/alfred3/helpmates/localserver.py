from builtins import map, object
from builtins import callable as builtins_callable
import logging

from uuid import uuid4
from pathlib import Path

from flask import (
    Flask,
    send_file,
    redirect,
    url_for,
    abort,
    request,
    make_response,
    session,
    send_from_directory,
)
from uuid import uuid4
from ..config import ExperimentConfig, ExperimentSecrets
from .. import alfredlog
import re, os


class Script:

    experiment = None
    expdir = None
    config = None

    def generate_experiment(self, config=None):  # pylint: disable=method-hidden
        """Hook for the ``generate_experiment`` function extracted from 
        the user's script.py. It is meant to be replaced in ``run.py``.
        """

        return ""

    def set_generator(self, generator):
        """Included for backwards compatibility from v1.2.0 onwards.
        
        TODO: Remove in v2.0.0
        """
        # if the script.py contains generate_experiment directly, not as a class method
        if builtins_callable(generator):
            self.generate_experiment = generator.__get__(self, Script)
        # if the script.py contains Script.generate_experiment()
        elif builtins_callable(generator.generate_experiment):
            self.generate_experiment = generator.generate_experiment(self, Script)


class Generator(Script):
    """Included for backwards compatibility from v1.2.0 onwards.

    TODO: Remove in v2.0.0
    """

    pass


app = Flask(__name__)
script = Script()

# Included for backwards compatibility with trad. run.py from v1.2.0 onwards
# TODO: Remove in v2.0.0
app.secret_key = "1327157a-0c8a-4e6d-becf-717a2a21cdba"


@app.route("/start", methods=["GET", "POST"])
def start():

    logger = logging.getLogger(f"alfred3")
    logger.info("Starting experiment initialization.")

    # Try-except block for compatibility with alfred3 previous to v1.2.0
    # TODO: Remove try-except block in v2.0.0 (keep "try" part)
    # pylint: disable=unsubscriptable-object
    exp_id = script.config["exp_config"].get("metadata", "exp_id")
    session_id = script.config["exp_config"].get("metadata", "session_id")
    log = alfredlog.QueuedLoggingInterface("alfred3", f"exp.{exp_id}")
    log.session_id = session_id
    script.log = log

    # generate experiment
    try:
        script.experiment = script.generate_experiment(config=script.config)
    except Exception:
        script.log.exception("Expection during experiment generation.")
        abort(500)

    # start experiment
    try:
        script.experiment.start()
    except Exception:
        log.exception("Exception during experiment startup.")
        abort(500)

    # Experiment startup message

    session["page_tokens"] = []

    # html = exp.user_interface_controller.render_html() # Deprecated Command? Breaks Messages
    resp = make_response(redirect(url_for("experiment")))
    resp.cache_control.no_cache = True

    return resp


@app.route("/experiment", methods=["GET", "POST"])
def experiment():
    try:
        if request.method == "POST":

            move = request.values.get("move", None)
            directjump = request.values.get("directjump", None)
            par = request.values.get("par", None)
            page_token = request.values.get("page_token", None)

            try:
                token_list = session["page_tokens"]
                token_list.remove(page_token)
                session["page_tokens"] = token_list
            except ValueError:
                return redirect(url_for("experiment"))

            kwargs = request.values.to_dict()
            kwargs.pop("move", None)
            kwargs.pop("directjump", None)
            kwargs.pop("par", None)

            script.experiment.user_interface_controller.update_with_user_input(kwargs)
            if move is None and directjump is None and par is None and kwargs == {}:
                pass
            elif directjump and par:
                posList = list(map(int, par.split(".")))
                script.experiment.user_interface_controller.move_to_position(posList)
            elif move == "started":
                pass
            elif move == "forward":
                script.experiment.user_interface_controller.move_forward()
            elif move == "backward":
                script.experiment.user_interface_controller.move_backward()
            elif move == "jump" and par and re.match(r"^\d+(\.\d+)*$", par):
                posList = list(map(int, par.split(".")))
                script.experiment.user_interface_controller.move_to_position(posList)
            else:
                abort(400)
            return redirect(url_for("experiment"))

        elif request.method == "GET":
            page_token = str(uuid4())

            # this block extracts the list "page_tokens", if it exists in the session
            # it creates the list "page_tokens" as an empty list, if not. This is needed
            # for qt-wk experiments because they don't call the route /start
            try:
                token_list = session["page_tokens"]
            except KeyError:
                token_list = []

            token_list.append(page_token)
            session["page_tokens"] = token_list

            html = script.experiment.user_interface_controller.render_html(page_token)
            resp = make_response(html)
            resp.cache_control.no_cache = True
            return resp
    except Exception:
        script.log.exception("")
        abort(500)


@app.route("/staticfile/<identifier>")
def staticfile(identifier):
    path, content_type = script.experiment.user_interface_controller.get_static_file(identifier)
    dirname, filename = os.path.split(path)
    resp = make_response(send_from_directory(dirname, filename, mimetype=content_type))
    return resp


@app.route("/dynamicfile/<identifier>")
def dynamicfile(identifier):
    strIO, content_type = script.experiment.user_interface_controller.get_dynamic_file(identifier)
    resp = make_response(send_file(strIO, mimetype=content_type))
    resp.cache_control.no_cache = True
    return resp


@app.route("/callable/<identifier>", methods=["GET", "POST"])
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
        resp = make_response(redirect(url_for("experiment")))
    resp.cache_control.no_cache = True
    return resp
