from builtins import map, object
from builtins import callable as builtins_callable
import logging
import traceback
from deprecation import deprecated

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

    exp = None
    generate_experiment = None
    exp_session = None
    expdir = None
    config = None

    @deprecated("1.2", "2.0")
    def set_generator(self, generator):
        """Included for backwards compatibility from v1.2.0 onwards.
        
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
        script.exp = script.generate_experiment()
    except AttributeError:
        script.log.debug("Error passed: " + traceback.format_exc())
    try:
        script.exp_session = script.exp.start_session(session_id=session_id, config=script.config)
    except Exception:
        script.log.exception("Expection during experiment generation.")
        abort(500)

    # start experiment
    try:
        script.exp_session.start()
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

            url_pagename = request.args.get("page", None) # https://basepath.de/experiment?page=name

            try:
                token_list = session["page_tokens"]
                token_list.remove(page_token)
                session["page_tokens"] = token_list
            except ValueError:
                return redirect(url_for("experiment"))

            data = request.values.to_dict()
            data.pop("move", None)
            data.pop("directjump", None)
            data.pop("par", None)
            data.pop("page_token", None)

            script.exp_session.movement_manager.current_page.set_data(data)

            if move is None and directjump is None and par is None and not data:
                pass
            elif move == "started":
                pass
            elif move == "forward":
                script.exp_session.movement_manager.forward()
            elif move == "backward":
                script.exp_session.movement_manager.backward()
            elif move.startswith("jump"):
                name = move[5:] # extract name. Jump-move-string: "jump>name"
                script.exp_session.movement_manager.jump_by_name(name=name)
            elif url_pagename:
                script.exp_session.movement_manager.jump_by_name(name=url_pagename)
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

            html = script.exp_session.user_interface_controller.render_html(page_token)
            resp = make_response(html)
            resp.cache_control.no_cache = True
            return resp
    except Exception:
        script.log.exception("Exception during experiment execution.")
        abort(500)


@app.route("/staticfile/<identifier>")
def staticfile(identifier):
    path, content_type = script.exp_session.user_interface_controller.get_static_file(identifier)
    dirname, filename = os.path.split(path)
    resp = make_response(send_from_directory(dirname, filename, mimetype=content_type))
    return resp


@app.route("/dynamicfile/<identifier>")
def dynamicfile(identifier):
    strIO, content_type = script.exp_session.user_interface_controller.get_dynamic_file(identifier)
    resp = make_response(send_file(strIO, mimetype=content_type))
    resp.cache_control.no_cache = True
    return resp


@app.route("/callable/<identifier>", methods=["GET", "POST"])
def callable(identifier):
    f = script.exp_session.user_interface_controller.get_callable(identifier)
    
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

# @app.route("/None")
# def none(): pass