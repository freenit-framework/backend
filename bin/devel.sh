#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="all"
export OFFLINE=${OFFLINE:="no"}


. ${BIN_DIR}/common.sh
setup

export FREENIT_ENV="dev"
python migrate.py

echo "Backend"
echo "==============="
python main.py
