#!/bin/sh


export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
. "${PROJECT_ROOT}/name.py"
export VIRTUALENV=${VIRTUALENV:="${app_name}"}
export FREENIT_ENV=${FREENIT_ENV:="prod"}
export SYSPKG=${SYSPKG:="no"}
export SYSPKG=`echo ${SYSPKG} | tr '[:lower:]' '[:upper:]'`
export DB_TYPE=${DB_TYPE:="sql"}
export PIP_INSTALL="pip install -U --upgrade-strategy eager"
export OFFLINE=${OFFLINE:="no"}


setup() {
  cd ${PROJECT_ROOT}
  if [ "${SYSPKG}" != "YES" ]; then
    if [ ! -d ${HOME}/.virtualenvs/${VIRTUALENV} ]; then
        python${PY_VERSION} -m venv "${HOME}/.virtualenvs/${VIRTUALENV}"
    fi
    . ${HOME}/.virtualenvs/${VIRTUALENV}/bin/activate

    if [ "${1}" != "no" -a "${OFFLINE}" != "yes" ]; then
      ${PIP_INSTALL} pip wheel
      ${PIP_INSTALL} -e ".[${DB_TYPE},${FREENIT_ENV}]"
    fi
  fi

  if [ "${DB_TYPE}" = "sql" ]; then
    if [ ! -e "alembic/versions" ]; then
      mkdir alembic/versions
      alembic revision --autogenerate -m initial
    fi
    python migrate.py
  fi
}
