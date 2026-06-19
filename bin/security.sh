#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="test"
. ${BIN_DIR}/common.sh


setup no no
bandit `find freenit -type f -name '*.py' | grep -v -E 'freenit/(cli|local_config)\.py'`
