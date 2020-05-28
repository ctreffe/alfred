import os
import platform
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Union


class AlfredConfig(ConfigParser):
    """Provides basic functionality for alfred3 configuration.

    This is a child class of :py:class:`configparser.ConfigParser`, 
    which parses alfred configuration files and objects on intialization
    and behaves just like a usual `ConfigParser` afterwards, most
    importantly providing the methods ``get(section, option)``,
    ``getint(section, option)``, ``getfloat(section, option)``,
    and ``getboolean(section, option)`` for retrieving values from the
    parser instance. There are many more methods available, which are
    documented in the official ConfigParser `documentation`_.

    Args:
        expdir: Path to the experiment directory.
        config_object: A list of dictionaries and/or strings with alfred
            configuration in ini format. Defaults to `None`.
        *args: Variable length argument list, will be passed on to the
            parent class.
        **kwargs: Arbitrary keyword arguments, will be passed on to the
            parent class.
    
    .. _documentation: https://docs.python.org/3/library/configparser.html#configparser.ConfigParser
    """

    env_location = "ALFRED_CONFIG_FILE"
    config_name = "config.conf"


    def __init__(self, expdir: str = None, config_objects: list = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._config_objects = config_objects

        self._config_files = []
        self._pkg_path = Path(__file__).resolve().parent
        self._expdir = Path(expdir) if expdir else Path.cwd()
        self._parse_alfred_config()

    def _collect_config_files(self):
        """Collect config files from config locations.

        The method looks in the following locations in that order:

        1. "/etc/alfred/<config_name>.conf" (for unix operating systems)
        2. "<config_name>.conf" in user's home directory
        3. Filepath provided in enviroment variable env_location
        4. "config.conf" in experiment directory (usual place for
            user's experiment-specific config)
        """

        files = []

        if platform.system() in ["Linux", "Darwin"]:
            files.append(Path("/etc/alfred/alfred.conf"))

        files.append(Path.home().joinpath("alfred.conf"))
        files.append(os.getenv("ALFRED_CONFIG_FILE"))

        files.append(self._expdir.joinpath("config.conf"))

        self._config_files = [str(p) for p in files if p is not None]

    def _parse_alfred_config(self):
        """Parse alfred config files from different locations.

        The files are parsed in the following order (later files take
        precedence over earlier ones):

        1. Default configuration from "<pkg_path>/files/default.conf"
        2. User-specified configuration gathered via 
            `self._collect_config_files()`
        3. User-specified configuration from self.config_object
            (mainly intended for use with mortimer)
        """
        default = self._pkg_path / "files" / "default.conf"
        with open(default, encoding="utf-8") as f:
            self.read_file(f)

        self._collect_config_files()
        self.read(self._config_files)

        for obj in self._config_objects:
            try:
                self.read_dict(obj)
            except AttributeError:
                self.read_string(obj)


class AlfredSecrets(AlfredConfig):
    """Provides functionality for parsing secrets like DB credentials.

    This is a child class of :py:class:`alfred3.config.AlfredConfig`.
    It behaves largely the same way, ultimately inheriting from 
    :py:class:`configparser.ConfigParser`. 

    The only difference is, that it looks for different files 
    (`secrets.conf`) and in different locations than its parent.
    """

    def _collect_config_files(self):
        """Collect secrets.conf files from config locations.

        The method looks in the following locations in that order:

        1. "/etc/alfred/secrets.conf" (for unix operating systems)
        2. "secrets.conf" in user's home directory
        3. Filepath provided in enviroment variable "ALFRED_SECRETS_FILE"
        4. "secrets.conf" in experiment directory (the usual place for
            user's experiment-specific config)
        """

        files = []

        if platform.system() in ["Linux", "Darwin"]:
            files.append(Path("/etc/alfred/secrets.conf"))

        files.append(Path.home().joinpath("secrets.conf"))
        files.append(os.getenv("ALFRED_SECRETS_FILE"))

        files.append(self._expdir.joinpath("secrets.conf"))

        self._config_files = [str(p) for p in files if p is not None]

    pass
