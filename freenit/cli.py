import pathlib
import subprocess

from prompt_toolkit import prompt


def main():
    path = pathlib.Path(__file__).parent.resolve()
    project_name = prompt("Name of the project: ")
    subprocess.run([f"{path}/bin/freenit.sh", "project", project_name])
