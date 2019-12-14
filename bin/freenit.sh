#!/bin/sh

set -e


NAME="${1}"
if [ -z "${NAME}" ]; then
  echo "Usage: $0 <project name>" >&2
  exit 1
fi


MODULES="api models schemas"
PROJECT_ROOT=`python -c 'import os; import freenit; print(os.path.dirname(os.path.abspath(freenit.__file__)))'`


mkdir ${NAME}
for module in ${MODULES}; do
  mkdir -p ${NAME}/${module}
  touch ${NAME}/${module}/__init__.py
done
touch ${NAME}/__init__.py
echo 'freenit' >requirements.txt
cp -r ${PROJECT_ROOT}/project/* .
echo "app_name=${NAME}  # noqa: E225" >name.py
echo "ipdb" >requirements_dev.txt
