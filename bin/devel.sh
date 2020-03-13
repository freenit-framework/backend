#!/bin/sh


BIN_DIR=`dirname $0`
export FLASK_PORT=${FLASK_PORT:=5000}
export FLASK_ENV="development"
export OFFLINE=${OFFLINE:="no"}
export SYSPKG=${SYSPKG:="no"}


. ${BIN_DIR}/common.sh
setup no

if [ "${SYSPKG}" = "no" ]; then
  if [ "${OFFLINE}" != "yes" ]; then
    pip install -U -r requirements_dev.txt
  fi
fi


echo "Backend"
echo "==============="
python wsgi.py
