#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="dev"

. ${BIN_DIR}/common.sh
setup

echo "Backend"
echo "==============="
python main.py
