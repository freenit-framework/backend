#!/bin/sh


export BIN_DIR=`dirname $0`
export PROJECT_ROOT=`readlink -f "${BIN_DIR}/.."`
export VIRTUALENV=${VIRTUALENV:="backend"}
export FLASK_ENV=${FLASK_ENV:="development"}
export PY_VERSION=${PY_VERSION:="3.6"}


setup() {
  if [ ! -d ~/.virtualenvs/${VIRTUALENV} ]; then
      python${PY_VERSION} -m venv ~/.virtualenvs/${VIRTUALENV}
  fi
  . ~/.virtualenvs/${VIRTUALENV}/bin/activate

  cd ${PROJECT_ROOT}
  pip install -U -r requirements_dev.txt
  cp templates/peewee_migrate.txt ~/.virtualenvs/${VIRTUALENV}/lib/python${PY_VERSION}/site-packages/peewee_migrate/template.txt
  flask migration run
}

