#!/bin/sh


export OFFLINE=${OFFLINE:=no}
BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh

if [ "${OFFLINE}" = "yes" ]; then
  setup no
else
  setup
fi


flask users create -a --password Sekrit admin@example.com
