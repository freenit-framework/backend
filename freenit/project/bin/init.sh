#!/bin/sh


export OFFLINE=${OFFLINE:=no}
BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh


if [ "${OFFLINE}" = "yes" ]; then
  setup no
else
  setup
fi

if [ ! -e migrations/main/001_initial.py ]; then
  flask migration create initial
fi


flask migration run
flask admin create
