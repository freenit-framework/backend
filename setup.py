#!/usr/bin/env python3

import pathlib

from setuptools import find_packages, setup

PROJECT_ROOT = pathlib.Path(__file__).parent
README = (PROJECT_ROOT / 'README.md').read_text()

setup(
    name='freenit',
    version='0.0.23',
    description='REST API framework based on Flask-Smorest',
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
        'Framework :: Flask',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
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
        'bcrypt',
        'flask-collect>=1.3.2',
        'flask-cors>=2.1.2',
        'flask-jwt-extended>=3.24.1',
        'flask-security>=3.0.0',
        'flask-smorest>=0.18.2',
        'peewee-migrate>=1.1.6',
    ],
    include_package_data=True,
    package_data={
        '': [
            'static/swaggerui/*',
            'templates/*',
            'project/*',
            'project/bin/*',
            'project/api/*',
            'project/models/*',
        ]
    },
    scripts=['bin/freenit.sh'],
)
