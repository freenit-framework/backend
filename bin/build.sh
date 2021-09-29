#!/bin/sh

BIN_DIR=`dirname $0`
PROJECT_DIR="${BIN_DIR}"
export FREENIT_ENV="build"
. ${BIN_DIR}/common.sh


setup no


rm -rf *.egg-info build dist
python setup.py sdist bdist_wheel
