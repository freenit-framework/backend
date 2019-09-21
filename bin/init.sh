#!/bin/sh


export OFFLINE=${OFFLINE:=no}
BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh

if [ "${OFFLINE}" = "yes" ]; then
  setup no
else
  setup
fi


flask admin create
