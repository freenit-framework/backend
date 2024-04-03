#!/bin/sh

BIN_DIR=`dirname $0`
PROJECT_DIR="${BIN_DIR}"
export FREENIT_ENV="build"
. ${BIN_DIR}/common.sh


setup


rm -rf *.egg-info build dist
find . -name '*.pyc' -exec rm -rf {} \;
hatchling build
