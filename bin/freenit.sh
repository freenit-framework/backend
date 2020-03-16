#!/bin/sh

set -e


NAME="${1}"
if [ -z "${NAME}" ]; then
  echo "Usage: $0 <project name>" >&2
  exit 1
fi


PROJECT_ROOT=`python${PY_VERSION} -c 'import os; import freenit; print(os.path.dirname(os.path.abspath(freenit.__file__)))'`


mkdir ${NAME}
cd ${NAME}
echo 'freenit' >requirements.txt
cp -r ${PROJECT_ROOT}/project/* .
mv project ${NAME}
echo "app_name=\"${NAME}\"  # noqa: E225" >name.py
echo "ipdb" >requirements_dev.txt
echo "DEVEL_MODE = YES" >vars.mk
cat > Makefile << EOF
.include <name.py>

SERVICE != echo \${app_name}back
REGGAE_PATH := /usr/local/share/reggae
SYSPKG := YES

shell: up
	@sudo cbsd jexec user=devel jname=\${SERVICE} /usr/src/bin/shell.sh

init: up
	@sudo cbsd jexec jname=\${SERVICE} env OFFLINE=\${offline} SYSPKG=\${SYSPKG} /usr/src/bin/init.sh

do_devel:
	@sudo cbsd jexec jname=\${SERVICE} env OFFLINE=\${offline} SYSPKG=\${SYSPKG} /usr/src/bin/devel.sh

.include <\${REGGAE_PATH}/mk/service.mk>
EOF
