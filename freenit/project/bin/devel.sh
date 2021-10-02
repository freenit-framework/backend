#!/bin/sh

BIN_DIR=`dirname $0`
export FREENIT_ENV="dev"
export OFFLINE=${OFFLINE:="no"}


. ${BIN_DIR}/common.sh
setup

if [ ! -e "alembic/versions" ]; then
  mkdir -p alembic/versions
  alembic revision --autogenerate -m initial
fi
alembic upgrade head

echo "Backend"
echo "==============="
python main.py
