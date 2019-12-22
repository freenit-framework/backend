#!/bin/sh


export OFFLINE=${OFFLINE:=no}
BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh


if [ ! -e "${BIN_DIR}/../migrations/main/001_initial.py" ]; then
  flask migration create initial
fi


if [ "${OFFLINE}" = "yes" ]; then
  setup no
else
  setup
fi
flask admin create
