#!/bin/sh

BIN_DIR=`dirname $0`
PROJECT_ROOT=`readlink -f "${BIN_DIR}/.."`

if [ ! -d ~/.virtualenvs/${VIRTUALENV} ]; then
    vex --make ${VIRTUALENV} pip install -U pip
fi
