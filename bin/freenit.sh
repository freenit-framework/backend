#!/bin/sh


NAME="${1}"
if [ -z "${NAME}" ]; then
  echo "Usage: $0 <project name>" >&2
  exit 1
fi


PROJECT_ROOT=`python${PY_VERSION} -c 'import os; import freenit; print(os.path.dirname(os.path.abspath(freenit.__file__)))'`


mkdir ${NAME}
touch ${NAME}/__init__.py
echo 'freenit' >requirements.txt
cp -r ${PROJECT_ROOT}/project/* .
mv api ${NAME}
mv models ${NAME}
mv schemas ${NAME}
echo "app_name=\"${NAME}\"  # noqa: E225" >name.py
echo "ipdb" >requirements_dev.txt
