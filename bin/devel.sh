#!/bin/sh


BIN_DIR=`dirname $0`
export FLASK_PORT=${FLASK_PORT:=5000}
export FLASK_ENV="development"
API_ROOT="http://`hostname`:${FLASK_PORT}/api/v0/doc/"
export OFFLINE=${OFFLINE:=no}


. ${BIN_DIR}/common.sh
setup no


if [ "${OFFLINE}" != "yes" ]; then
  pip install -U -r requirements_dev.txt
fi


echo "Backend"
echo "==============="
echo " * API_ROOT: ${API_ROOT}"
flask run -h 0.0.0.0 -p ${FLASK_PORT}
