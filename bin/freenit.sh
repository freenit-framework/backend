#!/bin/sh

set -e


if [ "${1}" = "--version" ]; then
  python${PY_VERSION} -c 'from freenit.version import version; print(version)'
  exit 0
fi


NAME="${1}"
if [ -z "${NAME}" ]; then
  echo "Usage: $0 <project name>" >&2
  exit 1
fi


PROJECT_ROOT=`python${PY_VERSION} -c 'import os; import freenit; print(os.path.dirname(os.path.abspath(freenit.__file__)))'`
export SED_CMD="sed -i"

mkdir ${NAME}
cd ${NAME}
cp -r ${PROJECT_ROOT}/project/* .
case `uname` in
  *BSD)
    ${SED_CMD} '' -e "s/NAME/${NAME}/g" setup.py
    ${SED_CMD} '' -e "s/NAME/${NAME}/g" main.py
    ;;
  *)
    ${SED_CMD} -e "s/NAME/${NAME}/g" setup.py
    ${SED_CMD} -e "s/NAME/${NAME}/g" main.py
    ;;
esac
mv project ${NAME}
echo "app_name=\"${NAME}\"  # noqa: E225" >name.py
echo "DEVEL_MODE = YES" >vars.mk
echo "# ${NAME}" >README.md


cat >Makefile<< EOF
.include <name.py>

USE_FREENIT = YES
SERVICE != echo \${app_name}
REGGAE_PATH := /usr/local/share/reggae

.include <\${REGGAE_PATH}/mk/service.mk>
EOF

cat >.gitignore <<EOF
.coverage
.provisioned
.pytest_cache
__pycache__

ansible/group_vars/all
ansible/inventory/inventory
ansible/roles/*
ansible/site.yml
!ansible/roles/.keep
!ansible/roles/devel

build
cbsd.conf
coverage.xml
fstab
local_config.py
project.mk
site.retry
vars.mk

dist/
*.sqlite
*.egg-info/
EOF

cat >alembic/env.py<<EOF
import os
import sys

import ${NAME}.app
from alembic import context
from freenit.migration import run_migrations_offline, run_migrations_online


sys.path.append(os.getcwd())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF


echo "Success! Please edit setup.py!"
