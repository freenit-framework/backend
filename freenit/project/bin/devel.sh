#!/bin/sh


BIN_DIR=`dirname $0`
PROJECT_ROOT="${BIN_DIR}/.."
export FLASK_PORT=${FLASK_PORT:=5000}
export FLASK_ENV="development"
export OFFLINE=${OFFLINE:=no}
export SYSPKG=${SYSPKG:="no"}
export WEBSOCKET=${WEBSOCKET:="no"}


. ${BIN_DIR}/common.sh
setup no


if [ "${SYSPKG}" = "no" ]; then
  if [ "${OFFLINE}" != "yes" ]; then
    pip install -U --upgrade-strategy eager -e ".[dev]"
  fi
fi


if [ "${WEBSOCKET}" = "yes" ]; then
  export WEBSOCKET_FLAGS="--gevent 16 --gevent-monkey-patch --http-websockets"
fi


echo "Backend"
echo "==============="
uwsgi --master --http 0.0.0.0:${FLASK_PORT} ${WEBSOCKET_FLAGS} --python-auto-reload 1 --honour-stdin --wsgi-file devel.py
