#!/bin/sh


set -e


export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
. "${PROJECT_ROOT}/name.py"
. ${BIN_DIR}/common.sh
setup


if [ "${OFFLINE}" != "yes" ]; then
  pip install -U -r requirements_dev.txt
fi


rm -rf `find . -name __pycache__`
rm -rf .pytest_cache
flake8 .
py.test --cov="${app_name}" --cov-report=term-missing:skip-covered --cov-report=xml
