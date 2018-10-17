#!/bin/sh


BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh
setup

rm -rf application/static
flask collect --verbose
rm -rf application/static/app
