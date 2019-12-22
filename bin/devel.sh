#!/bin/sh


BIN_DIR=`dirname $0`
export FLASK_PORT=${FLASK_PORT:=5000}
export FLASK_ENV="development"
export OFFLINE=${OFFLINE:=no}


. ${BIN_DIR}/common.sh
setup no


if [ "${OFFLINE}" != "yes" ]; then
  pip install -U -r requirements_dev.txt
fi


echo "Backend"
echo "==============="
flask run -h 0.0.0.0 -p ${FLASK_PORT}
