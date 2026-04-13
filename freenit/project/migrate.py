import importlib
import os
import shutil
import subprocess  # nosec B404


def run_migrations():
    env = os.environ.copy()
    env.setdefault("FREENIT_ENV", "prod")
    oxyde = shutil.which("oxyde")
    if oxyde is None:
        raise RuntimeError("oxyde executable not found in PATH")
    subprocess.run([oxyde, "migrate"], check=True, env=env)  # nosec B603


def db_setup():
    run_migrations()

    from name import app_name

    return importlib.import_module(f"{app_name}.app")


if __name__ == "__main__":
    db_setup()
