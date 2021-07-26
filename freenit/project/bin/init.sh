#!/bin/sh

export OFFLINE=${OFFLINE:="no"}
BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh


if [ "${OFFLINE}" = "yes" ]; then
  setup no
else
  setup
fi

if [ -e "alembic/versions" ]; then
  alembic upgrade head
else
  alembic init alembic
  alembic upgrade head
fi
