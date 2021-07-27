#!/bin/sh


set -e

export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
export FREENIT_ENV="build"
. ${BIN_DIR}/common.sh
setup


twine upload dist/freenit-* --verbose
