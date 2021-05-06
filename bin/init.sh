#!/bin/sh


export OFFLINE=${OFFLINE:="no"}
export SYSPKG="no"
BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh


if [ "${OFFLINE}" = "yes" ]; then
  setup no
else
  setup
fi


flask admin create
