import importlib
import os
import subprocess


def db_setup():
    env = os.environ.copy()
    env.setdefault("FREENIT_ENV", "prod")
    subprocess.run(["oxyde", "migrate"], check=True, env=env)
    return importlib.import_module("freenit.app")


if __name__ == "__main__":
    db_setup()
