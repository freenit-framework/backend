#!/bin/sh

BIN_DIR=`dirname $0`
PROJECT_DIR="${BIN_DIR}"
. ${BIN_DIR}/common.sh


setup no
pip install -U pip
pip install -U wheel
pip install -U --upgrade-strategy eager -e ".[build]"


rm -rf *.egg-info build dist
python setup.py sdist bdist_wheel
