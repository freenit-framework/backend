#!/bin/sh


export FLASK_ENV=development
export FLASK_PORT=${FLASK_PORT:=5000}
API_ROOT="http://`hostname`:${FLASK_PORT}/api/v0/doc/"
BIN_DIR=`dirname $0`
PROJECT_ROOT=`readlink -f "${BIN_DIR}/.."`
VIRTUALENV=${VIRTUALENV:="backend"}

if [ ! -d ~/.virtualenvs/${VIRTUALENV} ]; then
    python3.6 -m venv ~/.virtualenvs/${VIRTUALENV}
fi

. ~/.virtualenvs/${VIRTUALENV}/bin/activate
cd ${PROJECT_ROOT}
pip install -U -r requirements.txt
cp templates/peewee_migrate.txt ~/.virtualenvs/${VIRTUALENV}/lib/python3.6/site-packages/peewee_migrate/template.txt
echo "Backend"
echo "==============="
echo " * API_ROOT: ${API_ROOT}"
flask run -h 0.0.0.0 -p ${FLASK_PORT}
