#!/bin/sh


export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
export VIRTUALENV=${VIRTUALENV:="backend"}
export FLASK_ENV=${FLASK_ENV:="production"}
export PY_VERSION=${PY_VERSION:="3.6"}


setup() {
  update=${1}
  if [ ! -d ${HOME}/.virtualenvs/${VIRTUALENV} ]; then
      python${PY_VERSION} -m venv "${HOME}/.virtualenvs/${VIRTUALENV}"
      cp "${PROJECT_ROOT}/templates/activate.fish" "${HOME}/.virtualenvs/${VIRTUALENV}/bin"
  fi
  . ${HOME}/.virtualenvs/${VIRTUALENV}/bin/activate

  cd ${PROJECT_ROOT}
  if [ "${update}" != "no" ]; then
    pip install -U pip
    pip install -U wheel
    pip install -U -r requirements.txt
  fi
  flask migration run
}
