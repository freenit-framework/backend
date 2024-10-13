#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="dev"
export OFFLINE=${OFFLINE:="no"}


. ${BIN_DIR}/common.sh
setup

echo "Backend"
echo "==============="
python main.py
