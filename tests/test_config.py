import os

import pytest

from alfred3.config import ExperimentConfig, ExperimentSecrets


class TestExperimentConfig:
    def test_default_config(self, tmp_path):
        """Assert that default settings are parsed."""

        config = ExperimentConfig(expdir=str(tmp_path))
        assert config.get("metadata", "exp_id") == "default_id"

    def test_exp_config(self, tmp_path):
        """Assert that an arbitrary option from a config.conf in the
        experiment directory is parsed."""

        d = tmp_path
        conf_file = d / "config.conf"
        conf_file.write_text("[config_test]\nfile = testconfig.conf")
        config = ExperimentConfig(expdir=str(d))
        assert config.get("config_test", "file") == "testconfig.conf"

    def test_config_string(self, tmp_path):
        fp = str(tmp_path)
        config_string = "[config_test]\nfile = string"
        config = ExperimentConfig(expdir=fp, config_objects=[config_string])

        assert config.get("config_test", "file") == "string"

    def test_config_dict(self, tmp_path):
        fp = str(tmp_path)
        config_dict = {"config_test": {"file": "string"}}
        config = ExperimentConfig(expdir=fp, config_objects=[config_dict])

        assert config.get("config_test", "file") == "string"

    def test_config_list(self, tmp_path):
        fp = str(tmp_path)
        config_string = "[config_test]\nfile_str = string\nfile = 1"
        config_dict = {"config_test": {"file_dict": "dict", "file": 2}}
        config_list = [config_string, config_dict]
        config = ExperimentConfig(expdir=fp, config_objects=config_list)

        assert config.get("config_test", "file_str") == "string"
        assert config.get("config_test", "file_dict") == "dict"
        assert config.getint("config_test", "file") == 2

    def test_config_objects_errors(self, tmp_path):
        fp = str(tmp_path)
        config_string = 1

        with pytest.raises(TypeError) as excinfo:
            ExperimentConfig(expdir=fp, config_objects=[config_string])

        assert "Config objects" in str(excinfo.value)

    def test_config_environ(self, tmp_path):
        fp = str(tmp_path)
        d = tmp_path / "test"
        d.mkdir()
        config_file = d / "config.conf"
        os.environ["ALFRED_CONFIG_FILE"] = str(config_file)

        config_file.write_text("[config_test]\nfile = environ.conf")

        config = ExperimentConfig(expdir=fp)

        assert config.get("config_test", "file") == "environ.conf"

    def test_config_order(self, tmp_path):
        fp = str(tmp_path)

        d = tmp_path / "test"
        d.mkdir()
        environ_config = d / "config.conf"
        os.environ["ALFRED_CONFIG_FILE"] = str(environ_config)

        environ_config_content = []
        environ_config_content.append("[config_test]")
        environ_config_content.append("file1 = environ_config")
        environ_config_content.append("file2 = environ_config")
        environ_config_content.append("file3 = environ_config")
        environ_config.write_text("\n".join(environ_config_content))

        expdir_config = tmp_path / "config.conf"
        expdir_config_content = []
        expdir_config_content.append("[config_test]")
        expdir_config_content.append("file2 = expdir_config")
        expdir_config_content.append("file3 = expdir_config")
        expdir_config.write_text("\n".join(expdir_config_content))

        config_dict = {"config_test": {"file3": "dict"}}

        config = ExperimentConfig(expdir=fp, config_objects=[config_dict])
        config_file1 = config.get("config_test", "file1")
        config_file2 = config.get("config_test", "file2")
        config_file3 = config.get("config_test", "file3")

        assert config_file1 == "environ_config"
        assert config_file2 == "expdir_config"
        assert config_file3 == "dict"


class TestExperimentSecrets:
    def test_exp_secrets(self, tmp_path):
        """Assert that an arbitrary option from a secrets.conf in the
        experiment directory is parsed."""

        d = tmp_path
        secrets_file = d / "secrets.conf"
        secrets_file.write_text("[config_test]\nfile = testconfig.conf")
        secrets = ExperimentSecrets(expdir=str(d))
        assert secrets.get("config_test", "file") == "testconfig.conf"

    def test_secrets_environ(self, tmp_path):
        fp = str(tmp_path)
        d = tmp_path / "test"
        d.mkdir()
        secrets_file = d / "secrets.conf"
        os.environ["ALFRED_SECRETS_FILE"] = str(secrets_file)

        secrets_file.write_text("[config_test]\nfile = environ.conf")

        secrets = ExperimentSecrets(expdir=fp)

        assert secrets.get("config_test", "file") == "environ.conf"
