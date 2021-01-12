#!/bin/sh


BIN_DIR=`dirname $0`
PROJECT_ROOT="${BIN_DIR}/.."
PROCESSES=4
WSGI_MODULE=wsgi
PORT=${PORT:=9000}
export FLASK_ENV="production"

. ${BIN_DIR}/common.sh
setup
pip install -U --upgrade-strategy eager uwsgi


cd ${PROJECT_ROOT}
exec uwsgi \
  --wsgi-file ${WSGI_MODULE}.py \
  --master \
  --processes ${PROCESSES} \
  --uwsgi-socket :${PORT} \
  --vacuum
