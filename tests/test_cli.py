import os
import subprocess

import pytest


class TestTemplate:
    def test_basic_template(self, tmp_path):
        cmd = ["alfred3", "template", f"--path={tmp_path}"]
        subprocess.run(cmd)
        files = os.listdir(tmp_path)
        assert "script.py" in files
        assert "config.conf" in files

    @pytest.mark.skip(reason="Run manually")
    def test_big_template(self, tmp_path):
        cmd = ["alfred3", "template", f"--path={tmp_path}", "-b"]
        subprocess.run(cmd)
        files = os.listdir(tmp_path)

        assert "script.py" in files
        assert "config.conf" in files

        assert "secrets.conf" in files
