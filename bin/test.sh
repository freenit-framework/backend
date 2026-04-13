#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="test"
. ${BIN_DIR}/common.sh


setup yes no
pytest -v --ignore=freenit/project/
