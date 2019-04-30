#!/bin/sh


BIN_DIR=`dirname $0`
export FLASK_PORT=${FLASK_PORT:=5000}
export FLASK_ENV="development"
API_ROOT="http://`hostname`:${FLASK_PORT}/doc/swaggerui"
. ${BIN_DIR}/common.sh
setup no


echo "Backend"
echo "==============="
echo " * API_ROOT: ${API_ROOT}"
flask run -h 0.0.0.0 -p ${FLASK_PORT}
