#!/bin/sh


BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh
setup yes


flask users create -a --password Sekrit admin@example.com
