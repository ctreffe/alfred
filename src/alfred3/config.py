"""Provides configuration handling for alfred3 experiments.

.. moduleauthor:: Johannes Brachem <jbrachem@posteo.de>
"""


import os
import platform
import sys
from configparser import ConfigParser, SectionProxy
from pathlib import Path
from typing import Union


class ExperimentConfig(ConfigParser):
    """Provides basic functionality for alfred3 configuration.

    Configuration files are parsed in the following order (later files
    override settings from earlier ones):

        1. Default configuration
        2. :attr:`global_config_name` in "/etc/alfred/" (for unix operating 
            systems)
        3. :attr:`global_config_name` in the user's home directory
        4. :attr:`env_location`
        5. :attr:`exp_config_name` in the experiment directory (usual place 
            for user's experiment-specific config)
        6. Objects given in the argument `config_objects`.

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
        config_objects: A list of dictionaries and/or strings with alfred
            configuration in ini format. Defaults to `None`.
        *args: Variable length argument list, will be passed on to the
            parent class.
        **kwargs: Arbitrary keyword arguments, will be passed on to the
            parent class.
    
    Attributes:
        env_location: Environment variable key that corresponds to a 
            full filepath (including filename) to an alfred configuration
            file.
        global_config_name: Name of the general library-wide 
            configuration files.
        exp_config_name: Name of the experiment-specific configuration 
            file.
    
    .. _documentation: https://docs.python.org/3/library/configparser.html#configparser.ConfigParser
    """

    env_location = "ALFRED_CONFIG_FILE"
    global_config_name = "alfred.conf"
    exp_config_name = "config.conf"

    def __init__(self, expdir: str, config_objects: list = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._config_objects = config_objects if config_objects is not None else []

        self._config_files = []
        self._pkg_path = Path(__file__).resolve().parent
        self.expdir = Path(expdir) if expdir else None
        self._parse_alfred_config()

    def _collect_config_files(self):
        """Collect user-defined config files from config locations.
        """

        files = []

        if platform.system() in ["Linux", "Darwin"]:
            files.append(Path("/etc/alfred").joinpath(self.global_config_name))

        files.append(Path.home().joinpath(self.global_config_name))
        files.append(os.getenv(self.env_location))

        if self.expdir:
            files.append(self.expdir.joinpath(self.exp_config_name))

        self._config_files = [str(p) for p in files if p is not None]

    def _parse_alfred_config(self):
        """Parse all config files from different locations.
        """

        default = self._pkg_path / "files" / self.global_config_name
        with open(default, encoding="utf-8") as f:
            self.read_file(f)

        self._collect_config_files()
        self.read(self._config_files)

        for obj in self._config_objects:
            if type(obj) not in [str, dict]:
                raise TypeError(
                    (
                        "The argument config_objects must be a list, containing only "
                        + "strings and/or dictionaries."
                    )
                )

            try:
                self.read_dict(obj)
            except AttributeError:
                self.read_string(obj)

    def as_dict(self) -> dict:
        """Converts the ConfigParser structure into a nested dict.

        Each section name is a first level key in the the dict, and the 
        key values of the section becomes the dict in the second level::

            {
                'section_name': {
                    'key': 'value'
                }
            }
        
        Returns:
            dict: A dictionary representation of the parser instance.
        """

        return {section_name: dict(self[section_name]) for section_name in self.sections()}

    def get_section(self, name: str) -> SectionProxy:
        """Returns a section of the parser, if it exists.

        Args:
            name: Name of the section you wish to retrieve.

        Returns:
            SectionProxy: A :class:`~configparser.SectionProxy` object.
                If the requested section does not exist, the method
                returns `None`.
        """

        try:
            return self[name]

        except KeyError:
            return None


class ExperimentSecrets(ExperimentConfig):
    """Provides functionality for parsing secrets like DB credentials.

    This class is used only to set the attributes :attr:`env_location`,
    :attr:`global_config_name`, and :attr:`exp_config_name`. Otherwise
    it behaves exactly like :class:`ExperimentConfig`.
    """

    env_location = "ALFRED_SECRETS_FILE"
    global_config_name = "secrets.conf"
    exp_config_name = "secrets.conf"


def init_configuration(expdir: str) -> dict:
    """Returns a dictionary with experiment config and secrets.

    Args:
        expdir: Experiment directory. Handed over to 
            :class:`ExperimentConfig` and :class:`ExperimentSecrets`
    """

    exp_config = ExperimentConfig(expdir=expdir)
    exp_secrets = ExperimentSecrets(expdir=expdir)
    config = {"exp_config": exp_config, "exp_secrets": exp_secrets}
    return config
