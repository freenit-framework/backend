#!/bin/sh

BIN_DIR=`dirname $0`
PROJECT_ROOT=`readlink -f "${BIN_DIR}/.."`
VIRTUALENV=${VIRTUALENV:="backend"}

if [ ! -d ~/.virtualenvs/${VIRTUALENV} ]; then
    python3.6 -m venv ~/.virtualenvs/${VIRTUALENV}
fi
. ~/.virtualenvs/${VIRTUALENV}/bin/activate

cd ${PROJECT_ROOT}
pip install -U -r requirements_dev.txt
cp templates/peewee_migrate.txt ~/.virtualenvs/${VIRTUALENV}/lib/python3.6/site-packages/peewee_migrate/template.txt
py.test
