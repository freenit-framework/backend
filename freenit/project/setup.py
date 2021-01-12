#!/usr/bin/env python

import pathlib

from NAME import VERSION
from setuptools import find_packages, setup

PROJECT_ROOT = pathlib.Path(__file__).parent
README = (PROJECT_ROOT / 'README.md').read_text()

ldap = ['freenit[ldap]']
mongo = ['freenit[mongoengine]']
sql = ['freenit[sql]']
dev = ['freenit[dev]']

setup(
    name='NAME',
    version=VERSION,
    description='REST API framework based on Flask-Smorest',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/freenit-framework/backend',
    author='Goran Mekić',
    author_email='meka@tilda.center',
    license='BSD',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
    keywords=[
        'REST',
        'openapi',
        'swagger',
        'flask',
        'marshmallow',
        'apispec'
        'webargs',
    ],
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.5',
    install_requires=[
        'freenit[DBTYPE]',
    ],
    extras_require={
        'all': ldap + mongo + sql,
        'ldap': ldap,
        'mongo': mongo,
        'sql': sql,
        'dev': dev,
    },
)
