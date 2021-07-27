#!/bin/sh


export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
. "${PROJECT_ROOT}/name.py"
export VIRTUALENV=${VIRTUALENV:="${app_name}"}
export FREENIT_ENV=${FREENIT_ENV:="prod"}
export SYSPKG=${SYSPKG:="no"}


setup() {
  if [ "${SYSPKG}" = "no" ]; then
    update=${1}
    if [ ! -d ${HOME}/.virtualenvs/${VIRTUALENV} ]; then
        python${PY_VERSION} -m venv "${HOME}/.virtualenvs/${VIRTUALENV}"
    fi
    . ${HOME}/.virtualenvs/${VIRTUALENV}/bin/activate

    INSTALL_TARGET=".[${FREENIT_ENV}]"
    if [ "${FREENIT_ENV}" = "prod" ]; then
      INSTALL_TARGET="."
    fi
    cd ${PROJECT_ROOT}
    if [ "${update}" != "no" ]; then
      pip install -U pip
      pip install -U wheel
      pip install -U --upgrade-strategy eager -e "${INSTALL_TARGET}"
    fi
  fi

  if [ ! -e "alembic/versions" ]; then
    mkdir alembic/versions
    alembic revision --autogenerate -m initial
  fi
  alembic upgrade head
}
