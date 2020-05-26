"""Creates alfred3 experiment templates in the current working
directory.
"""

import sys
from pathlib import Path

if __name__ == "__main__":

    # collect paths
    module_path = Path(__file__).resolve().parent / "files" / "exp_template"
    run = module_path / "run.py"
    config = module_path / "config.conf"
    gitignore = module_path / "gitignore_template.txt"
    files = [run, config]
    wd = Path.cwd()

    # process run.py, config.conf
    for path in files:
        content = path.read_text()
        target = wd / path.name
        target.write_text(content)

    # process gitignore
    gitignore_content = gitignore.read_text()
    gitignore_target = wd / ".gitignore"
    gitignore_target.write_text(gitignore_content)

    # process script
    if len(sys.argv) < 2:
        script = module_path / "hello_world.py"
        script_content = script.read_text()
    elif len(sys.argv) >= 2:
        raise NotImplementedError("Currently, there are no arguments available for this module.")

    script_target = wd / "script.py"
    script_target.write_text(script_content)

    # print out success
    print("Created an alfred3 experiment template in the current working directory.")
    print("You can start the experiment via 'python3 run.py'.")
