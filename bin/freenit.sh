#!/bin/sh

set -e


help() {
  echo "Usage: $0 <type> <name>"
  echo "  type: project, backend, react, svelte"
  echo "  name: name used everywhere in the project"

}


if [ "${1}" = "--version" ]; then
  python${PY_VERSION} -c 'from freenit.version import version; print(version)'
  exit 0
fi


TYPE="${1}"
if [ -z "${TYPE}" ]; then
  help >&2
  exit 1
fi

case "${TYPE}" in
  project|backend|react|svelte)
    ;;
  *)
    help >&2
    exit 1
    ;;
esac
shift

NAME="${1}"
if [ -z "${NAME}" ]; then
  help >&2
  exit 1
fi
shift

export SED_CMD="sed -i"

backend() {
  PROJECT_ROOT=`python${PY_VERSION} -c 'import os; import freenit; print(os.path.dirname(os.path.abspath(freenit.__file__)))'`

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

SYSPKG = YES
USE_FREENIT = YES
SERVICE != echo \${app_name}
REGGAE_PATH := /usr/local/share/reggae

.include <\${REGGAE_PATH}/mk/service.mk>
EOF

  mkdir -p templates ansible
  cd ansible
  mkdir -p group_vars inventory roles
  touch group_vars/.keep inventory/.keep roles/.keep
  cd ..
  echo ".include <\${REGGAE_PATH}/mk/ansible.mk>" >provisioners.mk

  cat >requirements.yml<<EOF
- onelove-roles.freebsd-common
- onelove-roles.freebsd_repo
- onelove-roles.freebsd_freenit
EOF

  cat >templates/site.yml.tpl<<EOF
# -*- mode: ansible -*-
# vi: set ft=ansible :

---
- name: SERVICE provisioning
  hosts: SERVICE
  roles:
    - onelove-roles.freebsd-common
    - onelove-roles.freebsd_repo
    - onelove-roles.freebsd_freenit
EOF

  cat >alembic/env.py<<EOF
import os
import sys

import ${NAME}.app
from ${NAME}.config import getConfig
from alembic import context
from freenit.migration import run_migrations_offline, run_migrations_online


sys.path.append(os.getcwd())
config = getConfig()


if context.is_offline_mode():
    run_migrations_offline(config)
else:
    run_migrations_online(config)
EOF

  cat >.gitignore<<EOF
.coverage
.pytest_cache
__pycache__
*.py[c,o]

ansible/group_vars/all
ansible/inventory/inventory
ansible/roles/*
ansible/site.yml
!ansible/roles/.keep
!ansible/roles/devel

alembic/versions/*
build
cbsd.conf
coverage.xml
fstab
junit.xml
local_config.py
project.mk
site.retry
vars.mk

dist/
*.egg-info/
*.sqlite
EOF

  echo "Success! Please edit setup.py!"
  cd ..
}


frontend_common() {
  echo "# ${NAME}" >README.md
  npm --save install chota

  mkdir bin
  cd bin
  cat >common.sh<<EOF
#!/bin/sh


export BIN_DIR=\`dirname \$0\`
export PROJECT_ROOT="\${BIN_DIR}/.."
export OFFLINE=\${OFFLINE:=no}
NPM=\`which npm 2>/dev/null\`
YARN=\`which yarn 2>/dev/null\`


if [ ! -z "\${NPM}" ]; then
  export PACKAGE_MANAGER="\${NPM} run"
  export PACKAGE_MANAGER_INSTALL="\${NPM}"
else
  export PACKAGE_MANAGER="\${YARN}"
  export PACKAGE_MANAGER_INSTALL="\${YARN}"
fi


setup() {
  if [ -z "\${PACKAGE_MANAGER}" ]; then
    echo "Install npm or yarn" >&2
    exit 1
  fi

  cd \${PROJECT_ROOT}
  update=\${1}
  if [ "\${OFFLINE}" != "yes" -a "\${update}" != "no" ]; then
    \${PACKAGE_MANAGER_INSTALL} install
  fi
}
EOF

  cat >init.sh<<EOF
#!/bin/sh


export OFFLINE=\${OFFLINE:=no}
BIN_DIR=\`dirname \$0\`
. \${BIN_DIR}/common.sh

setup
EOF
  chmod +x init.sh

  cat >test.sh<<EOF
#!/bin/sh


BIN_DIR=\`dirname \$0\`
. "\${BIN_DIR}/common.sh"
setup

env CI=true "\${PACKAGE_MANAGER}" test
EOF
  chmod +x test.sh

  cat >collect.sh<<EOF
#!/bin/sh


BIN_DIR=\`dirname \$0\`
. "\${BIN_DIR}/common.sh"
setup


echo "Frontend"
echo "========"
cd "\${PROJECT_ROOT}"
rm -rf build
${PACKAGE_MANAGER} build
EOF
  chmod +x collect.sh

  cd ..

  echo "app_name=\"${NAME}\"" >name.ini
  cat >Makefile<<EOF
.include <name.ini>

SYSPKG = YES
USE_FREENIT = YES
SERVICE != echo \${app_name}front
REGGAE_PATH := /usr/local/share/reggae
DEVEL_MODE = YES

.include <\${REGGAE_PATH}/mk/service.mk>
EOF

  mkdir -p templates ansible
  cd ansible
  mkdir -p group_vars inventory roles
  touch group_vars/.keep inventory/.keep roles/.keep
  cd ..
  echo ".include <\${REGGAE_PATH}/mk/ansible.mk>" >provisioners.mk

  cat >requirements.yml<<EOF
- onelove-roles.freebsd-common
- onelove-roles.freebsd_repo
- onelove-roles.freebsd_node
EOF

  cat >templates/site.yml.tpl<<EOF
# -*- mode: ansible -*-
# vi: set ft=ansible :

---
- name: SERVICE provisioning
  hosts: SERVICE
  roles:
    - onelove-roles.freebsd-common
    - onelove-roles.freebsd_repo
    - onelove-roles.freebsd_node
EOF

  cat >.gitignore<<EOF
.DS_Store
node_modules
build
.svelte-kit
package
.env
.env.*
.vercel
.output
dist
stats.html

.provisioned
ansible/group_vars/all
ansible/inventory/inventory
ansible/roles/*
ansible/site.yml
!ansible/roles/.keep
!ansible/roles/freenit
build/
cbsd.conf
site.retry
project.mk
vars.mk
EOF
}

react() {
  npm init vite@latest "${NAME}" -- --template react-ts
  cd "${NAME}"
  npm install --save @freenit-framework/axios react-router-dom
  frontend_common

  rm src/App.* src/index.css src/logo.svg
  mkdir src/routes
  cat >src/routing.tsx<<EOF
import React, { Fragment } from 'react'
import { Route, Routes } from 'react-router-dom'

const PRESERVED = import.meta.globEager('/src/routes/(_app|404).tsx')
const ROUTES = import.meta.globEager('/src/routes/**/[a-z[]*.tsx')

const preserved: { [key: string]: any } = Object.keys(PRESERVED).reduce((preserved, file) => {
  const key = file.replace(/\/src\/routes\/|\.tsx$/g, '')
  return { ...preserved, [key]: PRESERVED[file].default }
}, {})

const routes = Object.keys(ROUTES).map((route) => {
  const path = route
    .replace(/\/src\/routes|index|\.tsx$/g, '')
    .replace(/\[\.{3}.+\]/, '*')
    .replace(/\[(.+)\]/, ':')

  return { path, component: ROUTES[route].default }
})

export const Routing = () => {
  const NotFound = preserved?.['404'] || Fragment

  return (
    <Routes>
      {routes.map(({ path, component: Component = Fragment }) => (
        <Route key={path} path={path} element={<Component />} />
      ))}
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
EOF

  cat >src/main.tsx<<EOF
import React, { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import 'chota'
import { Routing } from './routing'

const container = document.getElementById('root');
const root = createRoot(container!);
root.render(
  <StrictMode>
    <BrowserRouter>
      <Routing />
    </BrowserRouter>
  </StrictMode>
);
EOF

  cat >src/routes/index.tsx<<EOF
export default function Landing() {
  return (
    <div>Hello World!</div>
  )
}
EOF

  case `uname` in
    *BSD)
      ${SED_CMD} '' -e "s/})//g" vite.config.ts
      ${SED_CMD} '' -e "s/plugins: \(.*\)/plugins: \1,/g" vite.config.ts
      ;;
    *)
      ${SED_CMD} -e "s/})//g" vite.config.ts
      ${SED_CMD} -e "s/plugins: \(.*\)/plugins: \1,/g" vite.config.ts
      ;;
  esac
  cat >>vite.config.ts<<EOF
  server: {
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL,
        changeOrigin: true
      }
    }
  }
})
EOF

  cd bin
  cat >devel.sh<<EOF
#!/bin/sh


BIN_DIR=\`dirname \$0\`
. "\${BIN_DIR}/common.sh"
setup

echo "Frontend"
echo "========"
env BACKEND_URL=\${BACKEND_URL} npm run dev -- --host 0.0.0.0
EOF
  chmod +x devel.sh
  cd ..
}

svelte() {
  npm init svelte@next "${NAME}"
  cd "${NAME}"
  npm install
  frontend_common
  cat >.prettierrc<<EOF
{
  "useTabs": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 80,
  "semi": false,
}
EOF

  case `uname` in
    *BSD)
      ${SED_CMD} '' -e "s/export default config//g" svelte.config.js
      ;;
    *)
      ${SED_CMD} -e "s/export default config//g" svelte.config.js
      ;;
  esac
  cat >>svelte.config.js<<EOF
if (process.env.BACKEND_URL) {
  config.kit.vite = {
    server: {
      proxy: {
        '/api': process.env.BACKEND_URL
      }
    }
  }
}

export default config
EOF
  npm run format
  cd bin
  cat >devel.sh<<EOF
#!/bin/sh


BIN_DIR=\`dirname \$0\`
. "\${BIN_DIR}/common.sh"
setup

echo "Frontend"
echo "========"
env BACKEND_URL=\${BACKEND_URL} npm run dev -- --host 0.0.0.0
EOF
  chmod +x devel.sh
  cd ../..
}

project() {
  echo "Creating project"
  mkdir "${NAME}"
  cd "${NAME}"
  echo "# ${NAME}" >README.md

  echo "Creating bin"
  mkdir bin
  cd bin
  cat >devel.sh<<EOF
#!/bin/sh

export BIN_DIR=\`dirname \$0\`
export PROJECT_ROOT="\${BIN_DIR}/.."
. "\${PROJECT_ROOT}/services/backend/name.py"
export backend_app_name=\${app_name}
export OFFLINE=\${OFFLINE:="no"}
export SYSPKG=\${SYSPKG:="no"}
RAW_SERVICES=\$@
export SERVICES=\${RAW_SERVICES:="backend frontend"}
firstone="yes"

if [ "\${REGGAE}" != "yes" ]; then
  "\${BIN_DIR}/download_repos.sh"
fi

for service in \${SERVICES}; do
  if [ "backend" = "\${service}" ]; then
    firstone="no"
    if [ "\${REGGAE}" = "yes" ]; then
      export backend_hostname=\$(sudo cbsd jexec user=devel "jname=\${backend_app_name}" hostname)
      sudo tmux new-session -s "\${backend_app_name}" -d "make -C services/\${service} devel"
    else
      export backend_hostname="localhost"
      tmux new-session -s "\${backend_app_name}" -d "env OFFLINE=\${OFFLINE} SYSPKG=\${SYSPKG} \${PROJECT_ROOT}/services/\${service}/bin/devel.sh"
    fi
  fi
done

for service in \${SERVICES}; do
  if [ "backend" = "\${service}" ]; then
    continue
  fi
  if [ "\${firstone}" = "yes" ]; then
    firstone="no"
    if [ "\${REGGAE}" = "yes" ]; then
      sudo tmux new-session -s "\${backend_app_name}" -d "make -C services/\${service} devel"
    else
      tmux new-session -s "\${backend_app_name}" -d "env OFFLINE=\${OFFLINE} SYSPKG=\${SYSPKG} \${PROJECT_ROOT}/services/\${service}/bin/devel.sh"
    fi
  else
    if [ "\${REGGAE}" = "yes" ]; then
      sudo tmux split-window -h -p 50 -t 0 "make -C services/\${service} BACKEND_URL=http://\${backend_hostname}:5000 devel"
    else
      tmux split-window -h -p 50 -t 0 "env OFFLINE=\${OFFLINE} BACKEND_URL=http://\${backend_hostname}:5000 \${PROJECT_ROOT}/services/\${service}/bin/devel.sh"
    fi
  fi
done

if [ "\${REGGAE}" = "yes" ]; then
  sudo tmux select-layout tiled
  sudo tmux a -t "\${backend_app_name}"
else
  tmux select-layout tiled
  tmux a -t "\${backend_app_name}"
fi
EOF
  chmod +x devel.sh

  cat >download_repos.sh<<EOF
#!/bin/sh

export BIN_DIR=\`dirname \$0\`
export PROJECT_ROOT="\${BIN_DIR}/.."

if [ ! -d "\${PROJECT_ROOT}/services" ]; then
  mkdir "\${PROJECT_ROOT}/services"
fi

if [ ! -d "\${PROJECT_ROOT}/services/backend" ]; then
  git clone https://github.com/freenit-framework/backend "\${PROJECT_ROOT}/services/backend"

fi
if [ ! -d "\${PROJECT_ROOT}/services/frontend" ]; then
  git clone https://github.com/freenit-framework/frontend "\${PROJECT_ROOT}/services/frontend"
fi
EOF
  chmod +x download_repos.sh

  cat >update_repos.sh<<EOF
#!/bin/sh

export BIN_DIR=\`dirname \$0\`
export PROJECT_ROOT="\${BIN_DIR}/.."
SERVICES_ROOT="\${PROJECT_ROOT}/services"

cd "\${SERVICES_ROOT}"
ls -1 | while read service; do
  echo "\${service}"
  cd "\${service}"
  git pull
  cd -
done
cd ..
git pull
EOF
  chmod +x update_repos.sh
  cd ..

  cat >Makefile<<EOF
REGGAE_PATH = /usr/local/share/reggae
# USE = letsencrypt nginx
SERVICES += backend https://github.com/freenit-framework/backend
SERVICES += frontend https://github.com/freenit-framework/frontend
USE_FREENIT = YES

.include <\${REGGAE_PATH}/mk/project.mk>
EOF

  cat >.gitignore<<EOF
services/
vars.mk
EOF

  echo "DEVEL_MODE = YES" >vars.mk

  echo "Creating services"
  mkdir services
  cd services

  echo "Creating backend"
  backend
  mv "${NAME}" backend

  echo "Creating frontend"
  FRONTEND_TYPE=${FRONTEND_TYPE:=svelte}
  if [ "${FRONTEND_TYPE}" = "svelte" ]; then
    svelte
  elif [ "${FRONTEND_TYPE}" = "react" ]; then
    react
  else
    help >&2
    exit 1
  fi
  mv "${NAME}" frontend
  cd ..
}


${TYPE}
