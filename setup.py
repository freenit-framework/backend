#!/usr/bin/env python

import pathlib

from setuptools import find_packages, setup

from freenit import __version__

PROJECT_ROOT = pathlib.Path(__file__).parent
README = (PROJECT_ROOT / "README.md").read_text()

extras_require = {
    "beanie": [
        "beanie",
    ],
    "build": [
        "twine",
    ],
    "dev": [
        "aiosqlite",
        "black",
        "isort",
        "uvicorn",
    ],
    "ldap": [
        "bonsai",
    ],
    "ormar": [
        "alembic",
        "ormar",
    ],
    "test": [
        "aiosqlite",
        "bandit",
        "black",
        "httpx",
        "isort",
        "pytest-asyncio",
        "pytest-factoryboy",
        "requests",
    ],
}

extras_require["all"] = (
    extras_require["beanie"] + extras_require["ldap"] + extras_require["ormar"]
)

setup(
    name="freenit",
    version=__version__,
    description="REST API framework based on FastAPI",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/freenit-framework/backend",
    author="Goran Mekić",
    author_email="meka@tilda.center",
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords=[
        "REST",
        "openapi",
        "swagger",
        "fastapi",
    ],
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.8",
    install_requires=[
        "fastapi",
        "passlib",
        "pydantic[email]",
        "pyjwt",
    ],
    extras_require=extras_require,
    include_package_data=True,
    package_data={
        "": [
            "project/*",
            "project/ansible/group_vars/*",
            "project/ansible/inventory/*",
            "project/ansible/roles/devel/*",
            "project/ansible/roles/devel/tasks/*",
            "project/ansible/roles/devel/vars/*",
            "project/bin/*",
            "project/project/*",
            "project/project/api/*",
            "project/project/models/*",
            "project/templates/*",
        ]
    },
    scripts=["bin/freenit.sh"],
)
