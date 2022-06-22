#!/usr/bin/env python

import pathlib

from setuptools import find_packages, setup

PROJECT_ROOT = pathlib.Path(__file__).parent
README = (PROJECT_ROOT / "README.md").read_text()

setup(
    name="NAME",
    version="0.0.1",
    description="REST API based on Freenit",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/organization/backend",
    author="John Doe",
    author_email="john@example.com",
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
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
    install_requires=["freenit[ormar]"],
    extras_require={
        "build": ["freenit[build]"],
        "dev": ["freenit[dev]"],
        "test": ["freenit[test]"],
    },
)
