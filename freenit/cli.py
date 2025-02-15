import os
import pathlib
import subprocess

from prompt_toolkit import prompt


def main():
    path = pathlib.Path(__file__).parent.resolve()
    project_name = prompt("Name of the project: ")
    executable = f"{path}/../bin/freenit.sh"
    if not os.path.exists(executable):
        executable = f"{path}/bin/freenit.sh"
    subprocess.run([executable, "project", project_name])
