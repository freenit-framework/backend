#!/bin/sh

export FLASK_CONFIG="dev"
BIN_DIR=`dirname $0`
PROJECT_ROOT=`readlink -f "${BIN_DIR}/.."`

. ~/.virtualenvs/${VIRTUALENV}/bin/activate
cd ${PROJECT_ROOT}
pip install -U -r requirements.txt
./manage.py db migrate
./manage.py create_admin -e admin@example.com -p Sekrit
echo "Backend"
echo "==============="
./manage.py runserver
