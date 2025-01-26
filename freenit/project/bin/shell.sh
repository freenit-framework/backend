#!/bin/sh

BIN_DIR=`dirname $0`

. ${BIN_DIR}/common.sh
setup

env PYTHONPATH=${PWD}/.. ipython
