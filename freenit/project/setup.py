#!/usr/bin/env python

import pathlib

from setuptools import find_packages, setup

PROJECT_ROOT = pathlib.Path(__file__).parent
README = (PROJECT_ROOT / 'README.md').read_text()

setup(
    name='NAME',
    version='0.0.1',
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
        'Framework :: FastAPI',
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
    install_requires=['freenit'],
    extras_require={
        'build': [
            'twine',
        ],
        'dev': [
            'uvicorn',
        ],
        'test': [
            'pytest-asyncio',
            'pytest-factoryboy',
        ],
    },
)
