#!/bin/sh

set -e


if [ "${1}" = "--version" ]; then
  echo "0.1.9"
  exit 0
fi


NAME="${1}"
TYPE="${2}"
if [ -z "${NAME}" -o -z "${TYPE}" ]; then
  echo "Usage: $0 <project name> <project type>" >&2
  exit 1
fi


PROJECT_ROOT=`python${PY_VERSION} -c 'import os; import freenit; print(os.path.dirname(os.path.abspath(freenit.__file__)))'`
SED_CMD="sed -i"

case `uname` in
  *BSD)
    SED_CMD="sed -i ''"
    ;;
esac


mkdir ${NAME}
cd ${NAME}
echo "freenit[${TYPE}]" >requirements.txt
cp -r ${PROJECT_ROOT}/project/* .
${SED_CMD} -e "s/TYPE/${TYPE}/g" project/models/role.py
${SED_CMD} -e "s/TYPE/${TYPE}/g" project/models/user.py
mv project ${NAME}
echo "app_name=\"${NAME}\"  # noqa: E225" >name.py
echo "ipdb" >requirements_dev.txt
echo "DEVEL_MODE = YES" >vars.mk
