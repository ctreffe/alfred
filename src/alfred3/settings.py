# -*- coding: utf-8 -*-

"""
Modul enthält alle allgemeinen Einstellungen (für die gesamte
alfred Instanz, also nicht experimentspezifisch) sowie die Möglichkeit
experimentspezifische Einstellungen vorzunehmen, die dann unter
Experiment.settings abgefragt werden können.
"""

import codecs, configparser, io, os, sys
from builtins import object, str

from future import standard_library
from pathlib import Path

from ._helper import Decrypter, _DictObj

standard_library.install_aliases()


def _package_path():
    root = __file__
    if os.path.islink(root):
        root = os.path.realpath(root)
    return os.path.dirname(os.path.abspath(root))


#: package_path is the absolute filepath where alfred package is installed
package_path = _package_path()

##########################################################################
# Global Settings
##########################################################################


# define settings files
config_files = [  # most importent file last
    os.path.join(package_path, "files/alfred.conf"),
]
if os.environ.get("ALFRED_CONFIG_FILE"):
    config_files += [os.environ.get("ALFRED_CONFIG_FILE")]
else:
    config_files += [
        "/etc/alfred" if sys.platform.startswith("linux") else None,
        os.path.join(sys.prefix, "etc/alfred"),
    ]
config_files += [os.path.join(os.getcwd(), "config.conf")]

running_script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
config_files += [os.path.join(running_script_path, "config.conf")]

config_files = [x for x in config_files if x is not None]

# create config parser
_config_parser = configparser.ConfigParser()

# read _config_files
for config_file in config_files:
    if os.path.exists(config_file):
        _config_parser.read_file(codecs.open(config_file, "r", "utf8"))

# transform data from config_files to actual python objects

# general
general = _DictObj()
general.debug = _config_parser.getboolean("general", "debug")
general.runs_on_mortimer = _config_parser.getboolean("general", "runs_on_mortimer", fallback=False)
general.external_files_dir = _config_parser.get("general", "external_files_dir")

if not os.path.isabs(general.external_files_dir):
    general.external_files_dir = os.path.join(os.getcwd(), general.external_files_dir)

debugmode = general.debug

# metadata
metadata = _DictObj()
metadata.title = _config_parser.get("metadata", "title")
metadata.author = _config_parser.get("metadata", "author")
metadata.version = _config_parser.get("metadata", "version")
metadata.exp_id = _config_parser.get("metadata", "exp_id")
# check if metadata is given correctly
if not metadata.title:
    raise ValueError(
        "You need to define an experiment title in config.conf. Make sure to remove title definition from script.py"
    )
if not metadata.author:
    raise ValueError(
        "You need to define an author in config.conf. Make sure to remove author definition from script.py"
    )
if not metadata.version:
    raise ValueError(
        "You need to define an experiment version in config.conf. Make sure to remove version definition from script.py"
    )
if not metadata.exp_id:
    raise ValueError(
        "You need to define an experiment id in config.conf. IMPORTANT: For local experiments that write data to an online data base, this experiment id needs to be unique. OTHERWISE, DATA MAY BE LOST."
    )

# experiment
experiment = _DictObj()
experiment.type = _config_parser.get("experiment", "type")
experiment.fullscreen = _config_parser.getboolean("experiment", "fullscreen", fallback=False)
experiment.qt_full_screen = _config_parser.getboolean("experiment", "qt_fullscreen")
experiment.web_layout = _config_parser.get("experiment", "web_layout")

if not experiment.type:
    raise ValueError(
        "You need to define an experiment type in config.conf. Make sure to remove type definition from script.py"
    )
if not (experiment.type == "qt" or experiment.type == "web" or experiment.type == "qt-wk"):
    raise ValueError("experiment.type must be qt, qt-wk or web")


# logging
log = _DictObj()
log.syslog = _config_parser.getboolean("log", "syslog")
log.stderrlog = _config_parser.getboolean("log", "stderrlog")
log.path = _config_parser.get("log", "path")
log.level = _config_parser.get("log", "level")

# navigation
navigation = _DictObj()
navigation.forward = _config_parser.get("navigation", "forward")
navigation.backward = _config_parser.get("navigation", "backward")
navigation.finish = _config_parser.get("navigation", "finish")

# failure saving agent
failure_local_saving_agent = _DictObj()
failure_local_saving_agent.level = _config_parser.getint("failure_local_saving_agent", "level")
failure_local_saving_agent.path = _config_parser.get("failure_local_saving_agent", "path")
failure_local_saving_agent.name = _config_parser.get("failure_local_saving_agent", "name")

# webserver
webserver = _DictObj()
webserver.basepath = str(_config_parser.get("webserver", "basepath"))

# debug default values
debug = _DictObj()
debug.default_values = _config_parser.getboolean("debug", "set_default_values")
debug.disable_minimum_display_time = _config_parser.getboolean(
    "debug", "disable_minimum_display_time"
)
debug.reduce_countdown = _config_parser.getboolean("debug", "reduce_countdown")
debug.reduced_countdown_time = _config_parser.get("debug", "reduced_countdown_time")
debug.log_levelOverride = _config_parser.getboolean("debug", "log_level_override")
debug.log_level = _config_parser.get("debug", "log_level")
debug.disable_saving = _config_parser.getboolean("debug", "disable_saving")

debug.InputElement = _config_parser.get("debug", "InputElement_default")
debug.TextEntryElement = str(_config_parser.get("debug", "TextEntryElement_default"))
debug.RegEntryElement = str(_config_parser.get("debug", "RegEntryElement_default"))
debug.PasswordElement = str(_config_parser.get("debug", "PasswordElement_default"))
debug.NumberEntryElement = _config_parser.get("debug", "NumberEntryElement_default")
debug.TextAreaElement = str(_config_parser.get("debug", "TextAreaElement_default"))
debug.SingleChoiceElement = _config_parser.get("debug", "SingleChoiceElement_default")
debug.MultipleChoiceElement = _config_parser.getboolean("debug", "MultipleChoiceElement_default")
debug.SingleChoiceElement = _config_parser.get("debug", "SingleChoiceElement_default")
debug.LikertElement = _config_parser.get("debug", "LikertElement_default")
debug.LikertListElement = _config_parser.get("debug", "LikertListElement_default")
debug.LikertMatrix = _config_parser.get("debug", "LikertMatrix_default")
debug.WebLikertImageElement = _config_parser.get("debug", "WebLikertImageElement_default")
debug.WebLikertListElement = _config_parser.get("debug", "WebLikertListElement_default")


class ExperimentSpecificSettings(object):
    """ This class contains experiment specific settings """

    def __init__(self, config_string=""):
        config_parser = configparser.ConfigParser()
        config_files = [
            x
            for x in [  # most importent file last
                os.path.join(package_path, "files/alfred.conf"),
                os.environ.get("ALFRED_CONFIG_FILE"),
                os.path.join(os.getcwd(), "config.conf"),
                os.path.join(running_script_path, "config.conf"),
            ]
            if x is not None
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                config_parser.read_file(codecs.open(config_file, "r", "utf8"))
        if config_string:
            config_parser.read_file(io.StringIO(config_string))

        # handle section by hand
        sections_by_hand = [
            "mongo_saving_agent",
            "couchdb_saving_agent",
            "local_saving_agent",
            "fallback_mongo_saving_agent",
            "fallback_couchdb_saving_agent",
            "fallback_local_saving_agent",
            "level2_fallback_local_saving_agent",
        ]

        decrypter = Decrypter()

        self.local_saving_agent = _DictObj()
        self.local_saving_agent.use = config_parser.getboolean("local_saving_agent", "use")
        self.local_saving_agent.assure_initialization = config_parser.getboolean(
            "local_saving_agent", "assure_initialization"
        )
        self.local_saving_agent.level = config_parser.getint("local_saving_agent", "level")
        self.local_saving_agent.path = config_parser.get("local_saving_agent", "path")
        self.local_saving_agent.name = config_parser.get("local_saving_agent", "name")

        self.couchdb_saving_agent = _DictObj()
        self.couchdb_saving_agent.use = config_parser.getboolean("couchdb_saving_agent", "use")
        self.couchdb_saving_agent.assure_initialization = config_parser.getboolean(
            "couchdb_saving_agent", "assure_initialization"
        )
        self.couchdb_saving_agent.level = config_parser.getint("couchdb_saving_agent", "level")
        self.couchdb_saving_agent.url = config_parser.get("couchdb_saving_agent", "url")
        self.couchdb_saving_agent.database = config_parser.get("couchdb_saving_agent", "database")

        self.mongo_saving_agent = _DictObj()
        self.mongo_saving_agent.use = config_parser.getboolean("mongo_saving_agent", "use")
        self.mongo_saving_agent.assure_initialization = config_parser.getboolean(
            "mongo_saving_agent", "assure_initialization"
        )
        self.mongo_saving_agent.level = config_parser.getint("mongo_saving_agent", "level")
        self.mongo_saving_agent.host = config_parser.get("mongo_saving_agent", "host")
        self.mongo_saving_agent.database = config_parser.get("mongo_saving_agent", "database")
        self.mongo_saving_agent.collection = config_parser.get("mongo_saving_agent", "collection")
        self.mongo_saving_agent.use_ssl = config_parser.getboolean("mongo_saving_agent", "use_ssl")
        self.mongo_saving_agent.ca_file_path = config_parser.get(
            "mongo_saving_agent", "ca_file_path"
        )
        self.mongo_saving_agent.encrypted_login_data = config_parser.getboolean(
            "mongo_saving_agent", "encrypted_login_data"
        )
        self.mongo_saving_agent.login_from_env = config_parser.getboolean(
            "mongo_saving_agent", "login_from_env"
        )
        self.mongo_saving_agent.user = config_parser.get("mongo_saving_agent", "user")
        self.mongo_saving_agent.password = config_parser.get("mongo_saving_agent", "password")
        self.mongo_saving_agent.auth_source = config_parser.get(
            "mongo_saving_agent", "auth_source", fallback="admin"
        )

        if self.mongo_saving_agent.use and self.mongo_saving_agent.login_from_env:
            (
                self.mongo_saving_agent.user,
                self.mongo_saving_agent.password,
            ) = decrypter.decrypt_login(from_env=True)
        elif self.mongo_saving_agent.use and self.mongo_saving_agent.encrypted_login_data:
            (
                self.mongo_saving_agent.user,
                self.mongo_saving_agent.password,
            ) = decrypter.decrypt_login(
                self.mongo_saving_agent.user, self.mongo_saving_agent.password
            )

        self.fallback_local_saving_agent = _DictObj()
        self.fallback_local_saving_agent.use = config_parser.getboolean(
            "fallback_local_saving_agent", "use"
        )
        self.fallback_local_saving_agent.assure_initialization = config_parser.getboolean(
            "fallback_local_saving_agent", "assure_initialization"
        )
        self.fallback_local_saving_agent.level = config_parser.getint(
            "fallback_local_saving_agent", "level"
        )
        self.fallback_local_saving_agent.path = config_parser.get(
            "fallback_local_saving_agent", "path"
        )
        self.fallback_local_saving_agent.name = config_parser.get(
            "fallback_local_saving_agent", "name"
        )

        self.fallback_couchdb_saving_agent = _DictObj()
        self.fallback_couchdb_saving_agent.use = config_parser.getboolean(
            "fallback_couchdb_saving_agent", "use"
        )
        self.fallback_couchdb_saving_agent.assure_initialization = config_parser.getboolean(
            "fallback_couchdb_saving_agent", "assure_initialization"
        )
        self.fallback_couchdb_saving_agent.level = config_parser.getint(
            "fallback_couchdb_saving_agent", "level"
        )
        self.fallback_couchdb_saving_agent.url = config_parser.get(
            "fallback_couchdb_saving_agent", "url"
        )
        self.fallback_couchdb_saving_agent.database = config_parser.get(
            "fallback_couchdb_saving_agent", "database"
        )

        self.fallback_mongo_saving_agent = _DictObj()
        self.fallback_mongo_saving_agent.use = config_parser.getboolean(
            "fallback_mongo_saving_agent", "use"
        )
        self.fallback_mongo_saving_agent.assure_initialization = config_parser.getboolean(
            "fallback_mongo_saving_agent", "assure_initialization"
        )
        self.fallback_mongo_saving_agent.level = config_parser.getint(
            "fallback_mongo_saving_agent", "level"
        )
        self.fallback_mongo_saving_agent.host = config_parser.get(
            "fallback_mongo_saving_agent", "host"
        )
        self.fallback_mongo_saving_agent.database = config_parser.get(
            "fallback_mongo_saving_agent", "database"
        )
        self.fallback_mongo_saving_agent.collection = config_parser.get(
            "fallback_mongo_saving_agent", "collection"
        )
        self.fallback_mongo_saving_agent.use_ssl = config_parser.getboolean(
            "fallback_mongo_saving_agent", "use_ssl"
        )
        self.fallback_mongo_saving_agent.ca_file_path = config_parser.get(
            "fallback_mongo_saving_agent", "ca_file_path"
        )
        self.fallback_mongo_saving_agent.encrypted_login_data = config_parser.getboolean(
            "fallback_mongo_saving_agent", "encrypted_login_data"
        )
        self.fallback_mongo_saving_agent.user = config_parser.get(
            "fallback_mongo_saving_agent", "user"
        )
        self.fallback_mongo_saving_agent.password = config_parser.get(
            "fallback_mongo_saving_agent", "password"
        )

        if (
            self.fallback_mongo_saving_agent.use
            and self.fallback_mongo_saving_agent.encrypted_login_data
        ):
            (
                self.fallback_mongo_saving_agent.user,
                self.fallback_mongo_saving_agent.password,
            ) = decrypter.decrypt_login(
                self.fallback_mongo_saving_agent.user, self.fallback_mongo_saving_agent.password
            )

        self.level2_fallback_local_saving_agent = _DictObj()
        self.level2_fallback_local_saving_agent.use = config_parser.getboolean(
            "level2_fallback_local_saving_agent", "use"
        )
        self.level2_fallback_local_saving_agent.assure_initialization = config_parser.getboolean(
            "level2_fallback_local_saving_agent", "assure_initialization"
        )
        self.level2_fallback_local_saving_agent.level = config_parser.getint(
            "level2_fallback_local_saving_agent", "level"
        )
        self.level2_fallback_local_saving_agent.path = config_parser.get(
            "level2_fallback_local_saving_agent", "path"
        )
        self.level2_fallback_local_saving_agent.name = config_parser.get(
            "level2_fallback_local_saving_agent", "name"
        )

        for section in config_parser.sections():
            if section in sections_by_hand:
                continue
            setattr(self, section, _DictObj())
            for option in config_parser.options(section):
                # WARNING: Automatic section variables are always transformed into lowercase!
                getattr(self, section)[option] = str(config_parser.get(section, option))
