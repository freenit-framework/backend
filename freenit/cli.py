import os
import pathlib
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        raise ValueError(f"Usage: {sys.argv[0]}: <project name>")
    project_name = sys.argv[1]
    path = pathlib.Path(__file__).parent.resolve()
    executable = f"{path}/../bin/freenit.sh"
    if not os.path.exists(executable):
        executable = f"{path}/bin/freenit.sh"
    subprocess.run([executable, "project", project_name])
