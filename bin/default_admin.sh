#!/bin/sh

export FLASK_ENV=development
BIN_DIR=`dirname $0`
PROJECT_ROOT=`readlink -f "${BIN_DIR}/.."`
VIRTUALENV=${VIRTUALENV:="backend"}

. ~/.virtualenvs/${VIRTUALENV}/bin/activate
cd ${PROJECT_ROOT}
flask users create -a --password Sekrit admini@example.com
flask roles create -d Administrators admin
flask roles add admin@example.com admin
