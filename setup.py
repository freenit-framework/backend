#!/usr/bin/env python3

import pathlib

from setuptools import find_packages, setup

PROJECT_ROOT = pathlib.Path(__file__).parent
README = (PROJECT_ROOT / 'README.md').read_text()

ldap = ['ldap3']
mongo = ['flask-mongoengine']
sql = [
    'peewee',
    'peewee-migrate>=1.1.6',
]

setup(
    name='freenit',
    version='0.1.16',
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
        'email-validator',
    ],
    extras_require={
        'all': ldap + mongo + sql,
        'ldap': ldap,
        'mongo': mongo,
        'sql': sql,
    },
    include_package_data=True,
    package_data={
        '': [
            'project/*',
            'project/ansible/group_vars/*',
            'project/ansible/inventory/*',
            'project/ansible/roles/devel/*',
            'project/bin/*',
            'project/project/*',
            'project/project/api/*',
            'project/project/models/*',
            'project/project/schemas/*',
            'project/project/templates/*',
            'project/templates/*',
            'project/tests/*',
            'static/swaggerui/*',
            'templates/*',
        ]
    },
    scripts=['bin/freenit.sh'],
)
