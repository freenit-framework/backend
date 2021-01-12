#!/bin/sh


BIN_DIR=`dirname $0`
export FLASK_ENV="development"
. ${BIN_DIR}/common.sh
setup no

ipython -c 'from devel import application' -i
