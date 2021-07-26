#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="test"
. ${BIN_DIR}/common.sh


setup no
pip install -U pip
pip install -U wheel
pip install -U --upgrade-strategy eager -e ".[test]"

pytest -v
