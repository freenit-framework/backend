#!/bin/sh


set -e

export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
. "${PROJECT_ROOT}/name.py"
export FLASK_ENV="testing"
export DBTYPE="all"

. ${BIN_DIR}/common.sh
setup


if [ "${OFFLINE}" != "yes" ]; then
  pip install -U -r requirements_dev.txt
fi


CI=${1}
if [ "${CI}" = "ci" ]; then
  cp local_config_ci.py local_config.py
fi


cd "${PROJECT_ROOT}"
rm -rf `find . -name __pycache__`
rm -rf .pytest_cache
flake8 .

export DBTYPE="sql"
py.test --ignore=${app_name}/project/ --cov=${app_name} --cov-report=term-missing:skip-covered --cov-report=xml
