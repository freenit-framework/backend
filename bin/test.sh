#!/bin/sh


set -e


BIN_DIR=`dirname $0`
. ${BIN_DIR}/common.sh
setup


rm -rf `find . -name __pycache__`
rm -rf .pytest_cache
flake8 .
py.test --cov=application --cov-report=xml
