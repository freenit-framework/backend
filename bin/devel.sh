#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="dev"
export OFFLINE=${OFFLINE:="no"}


. ${BIN_DIR}/common.sh
setup

echo "Backend"
echo "==============="
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
