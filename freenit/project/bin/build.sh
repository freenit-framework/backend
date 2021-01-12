#!/bin/sh


set -e

export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
export OFFLINE=${OFFLINE:=no}
export SYSPKG=${SYSPKG:="no"}
. ${BIN_DIR}/common.sh
setup


if [ "${SYSPKG}" = "no" ]; then
  if [ "${OFFLINE}" != "yes" ]; then
    pip install -U --upgrade-strategy eager wheel
    pip install -U --upgrade-strategy eager -e '.[dev]'
  fi
fi

cd ${PROJECT_ROOT}
rm -rf *.egg-info build dist
python setup.py sdist bdist_wheel
