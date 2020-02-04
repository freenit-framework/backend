#!/bin/sh


export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
. "${PROJECT_ROOT}/name.py"
export VIRTUALENV=${VIRTUALENV:="${app_name}back"}
export FLASK_ENV=${FLASK_ENV:="production"}
export PY_VERSION=${PY_VERSION:="3.7"}


setup() {
  update=${1}
  if [ ! -d ${HOME}/.virtualenvs/${VIRTUALENV} ]; then
      python${PY_VERSION} -m venv "${HOME}/.virtualenvs/${VIRTUALENV}"
  fi
  . ${HOME}/.virtualenvs/${VIRTUALENV}/bin/activate

  cd ${PROJECT_ROOT}
  if [ "${update}" != "no" ]; then
    pip install -U pip
    pip install -U wheel
    pip install -U -r requirements.txt
  fi
  if [ -e "${BIN_DIR}/../migrations/main/001_initial.py" ]; then
    flask migration run
  fi
}
