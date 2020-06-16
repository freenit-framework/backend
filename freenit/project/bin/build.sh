#!/bin/sh


set -e

export BIN_DIR=`dirname $0`
export PROJECT_ROOT="${BIN_DIR}/.."
. ${BIN_DIR}/common.sh
setup


if [ "${OFFLINE}" != "yes" ]; then
  pip install -U -r requirements_dev.txt
fi

cd ${PROJECT_ROOT}
rm -rf *.egg-info build dist
python setup.py sdist bdist_wheel
