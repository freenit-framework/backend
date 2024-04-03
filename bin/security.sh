#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="test"
. ${BIN_DIR}/common.sh


setup no
bandit `find freenit -type f -name '*.py' | grep -v 'freenit/cli\.py'`
