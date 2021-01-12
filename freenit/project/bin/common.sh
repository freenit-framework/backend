#!/bin/sh

export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
. "${PROJECT_ROOT}/name.py"
export VIRTUALENV=${VIRTUALENV:="${app_name}"}
export FLASK_ENV=${FLASK_ENV:="production"}
export PY_VERSION=${PY_VERSION:="3.7"}
export SYSPKG=${SYSPKG:="no"}
export DBTYPE=${DBTYPE:="sql"}


setup() {
  cd "${PROJECT_ROOT}"
  if [ "${SYSPKG}" = "no" ]; then
    update=${1}
    if [ ! -d ${HOME}/.virtualenvs/${VIRTUALENV} ]; then
        python${PY_VERSION} -m venv "${HOME}/.virtualenvs/${VIRTUALENV}"
    fi
    . ${HOME}/.virtualenvs/${VIRTUALENV}/bin/activate

    cd ${PROJECT_ROOT}
    if [ "${update}" != "no" ]; then
      pip install -U pip
      pip install -U wheel
      pip install -U --upgrade-strategy eager -e ".[${DBTYPE}]"
    fi
  fi
}
