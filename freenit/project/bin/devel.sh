#!/bin/sh


BIN_DIR=`dirname $0`
PROJECT_ROOT="${BIN_DIR}/.."
export FLASK_PORT=${FLASK_PORT:=5000}
export FLASK_ENV="development"
API_ROOT="http://`hostname`:${FLASK_PORT}/doc/swaggerui"
export OFFLINE=${OFFLINE:=no}
export SYSPKG=${SYSPKG:="no"}


. ${BIN_DIR}/common.sh
setup no


cd "${PROJECT_ROOT}"
if [ "${SYSPKG}" = "no" ]; then
  if [ "${OFFLINE}" != "yes" ]; then
    pip install -U -r requirements_dev.txt
  fi
fi


echo "Backend"
echo "==============="
python wsgi.py
