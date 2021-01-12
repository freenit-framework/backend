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
    pip install -U --upgrade-strategy eager -e '.[dev]'
  fi
fi


echo "Backend"
echo "==============="
uwsgi --master --http 0.0.0.0:${FLASK_PORT} ${WEBSOCKET_FLAGS} --python-auto-reload 1 --honour-stdin --wsgi-file devel.py
