#!/usr/bin/env python

import pathlib

from setuptools import find_packages, setup
from freenit.version import version

PROJECT_ROOT = pathlib.Path(__file__).parent
README = (PROJECT_ROOT / 'README.md').read_text()

setup(
    name='freenit',
    version=version,
    description='REST API framework based on FastAPI',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/freenit-framework/backend',
    author='Goran Mekić',
    author_email='meka@tilda.center',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords=[
        'REST',
        'openapi',
        'swagger',
        'fastapi',
    ],
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.8',
    install_requires=[
        'alembic',
        'aiosqlite',
        'fastapi-users-db-ormar',
        'uvicorn',
    ],
    extras_require={
        'build': [
            'twine',
        ],
        'dev': [
            'black',
        ],
        'test': [
            'pytest-asyncio',
            'pytest-factoryboy',
        ],
    },
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
