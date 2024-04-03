import subprocess
from prompt_toolkit import prompt

def main():
    project_name = prompt("Name of the project: ")
    subprocess.run(["bin/freenit.sh", "project", project_name])
