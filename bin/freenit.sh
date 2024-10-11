#!/bin/sh

set -e


help() {
  echo "Usage: $0 <type> <name>"
  echo "  type: project, backend, frontend"
  echo "  name: name used everywhere in the project"

}


if [ "${1}" = "--version" ]; then
  python${PY_VERSION} -c 'from freenit import __version__; print(__version__)'
  exit 0
fi


TYPE="${1}"
if [ -z "${TYPE}" ]; then
  help >&2
  exit 1
fi

case "${TYPE}" in
  project|backend|frontend)
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

  mkdir "${NAME}"
  cd "${NAME}"
  cp -r ${PROJECT_ROOT}/project/* .
  case `uname` in
    *BSD)
      ${SED_CMD} '' -e "s/NAME/${NAME}/g" setup.py
      ${SED_CMD} '' -e "s/NAME/${NAME}/g" main.py
      ${SED_CMD} '' -e "s/PROJECT/${NAME}/g" pyproject.toml
      ;;
    *)
      ${SED_CMD} -e "s/NAME/${NAME}/g" setup.py
      ${SED_CMD} -e "s/NAME/${NAME}/g" main.py
      ${SED_CMD} -e "s/PROJECT/${NAME}/g" pyproject.toml
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
  npm install --save-dev chota

  mkdir bin
  cd bin
  cat >common.sh<<EOF
#!/bin/sh


export BIN_DIR=\`dirname \$0\`
export PROJECT_ROOT="\${BIN_DIR}/.."
export OFFLINE=\${OFFLINE:=no}


setup() {
  cd \${PROJECT_ROOT}
  update=\${1}
  if [ "\${OFFLINE}" != "yes" -a "\${update}" != "no" ]; then
    npm install
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

env CI=true npm run test
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
npm run build
touch build/.keep
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
- onelove-roles.freebsd_node
- onelove-roles.freebsd_pm2
EOF

  cat >templates/site.yml.tpl<<EOF
# -*- mode: ansible -*-
# vi: set ft=ansible :

---
- name: SERVICE provisioning
  hosts: SERVICE
  roles:
    - onelove-roles.freebsd-common
    - onelove-roles.freebsd_node
    - onelove-roles.freebsd_pm2
EOF

  cat >.gitignore<<EOF
node_modules

# Output
.output
.vercel
/.svelte-kit
/build
/dist

# OS
.DS_Store
Thumbs.db

# Env
.env
.env.*
!.env.example
!.env.test

# Vite
vite.config.js.timestamp-*
vite.config.ts.timestamp-*

# Reggae
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

frontend() {
  npm create svelte "${NAME}"
  cd "${NAME}"
  case `uname` in
    *BSD)
      ${SED_CMD} '' -e "s/export default defineConfig/const config = defineConfig/" vite.config.ts
      ${SED_CMD} '' -e "s/^}//" package.json
      ${SED_CMD} '' -e 's/"type": "module"/"type": "module",/' package.json
      ${SED_CMD} '' -e "s/adapter-auto/adapter-node/" svelte.config.js
      ;;
    *)
      ${SED_CMD} -e "s/export default defineConfig/const config = defineConfig/" vite.config.ts
      ${SED_CMD} -e "s/^}//" package.json
      ${SED_CMD} -e 's/"type": "module"/"type": "module",/' package.json
      ${SED_CMD} -e "s/adapter-auto/adapter-node/" svelte.config.js
      ;;
  esac
  cat >>vite.config.ts<<EOF
if (process.env.BACKEND_URL) {
  config.server = {
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL,
        changeOrigin: true,
      }
    }
  }
}

export default config
EOF

  cat >>package.json<<EOF
  "overrides": {
    "rollup": "npm:@rollup/wasm-node"
  }
}
EOF
  cat >.prettierrc<<EOF
{
  "useTabs": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 80,
  "semi": false,
}
EOF
  npm install
  frontend_common
  npm install --save-dev @zerodevx/svelte-toast @freenit-framework/svelte-base @sveltejs/adapter-node @mdi/js

  rm -rf src/lib
  rm -rf src/routes/about src/routes/sverdle src/routes/*.svelte

  cat >src/routes/styles.css<<EOF
:root {
  font-family: Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

body {
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

:root {
  --bg-color: #ffffff;
  --bg-secondary-color: #f3f3f6;
  --color-primary: #14854F;
  --color-lightGrey: #d2d6dd;
  --color-grey: #747681;
  --color-darkGrey: #3f4144;
  --color-error: #d43939;
  --color-success: #28bd14;
  --grid-maxWidth: 120rem;
  --grid-gutter: 2rem;
  --font-size: 1.6rem;
  --font-color: #333333;
  --font-family-sans: sans-serif;
  --font-family-mono: monaco, "Consolas", "Lucida Console", monospace;
}
EOF

  cat >src/routes/+layout.svelte<<EOF
<script>
  import './styles.css'
  import 'chota'
  import { store } from '@freenit-framework/svelte-base'
  import { SvelteToast } from '@zerodevx/svelte-toast'

  const options = {}

  // First invocation of this function creates store, next invocations return
  // existing one, so only first invocation takes "prefix" argument into account
  store('/api/v1')
</script>

<svelte:head>
  <title>Freenit App</title>
  <meta name="Freenit" content="Freenit for Svelte" />
</svelte:head>

<SvelteToast {options} />
<div class="main">
  <slot />
</div>

<style>
  .main {
    height: 100vh;
    width: 100vw;
  }
</style>
EOF

  echo '<div class="root">Landing Page in src/routes/+page.svelte</div>' >src/routes/+page.svelte

  mkdir src/routes/login
  cat >src/routes/login/+page.svelte <<EOF
<script lang="ts">
  import { Login } from '@freenit-framework/svelte-base'
</script>

<Login />
EOF

  mkdir src/routes/register
  cat >src/routes/register/+page.svelte <<EOF
<script lang="ts">
  import { Register } from '@freenit-framework/svelte-base'
</script>

<Register />
EOF

  mkdir -p 'src/routes/verify/[token]'
  cat >'src/routes/verify/[token]/+page.svelte' <<EOF
<script lang="ts">
  import { onMount } from 'svelte'
  import { page } from '\$app/stores'
  import { goto } from '\$app/navigation'
  import { store } from '@freenit-framework/svelte-base'

  onMount(async () => {
    const response = await store().auth.verify(\$page.params.token)
    if (response.ok) {
      goto('/login')
    }
  })
</script>
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
      sudo tmux new-session -s "\${backend_app_name}" -d "make -C services/\${service} devel offline=\${OFFLINE}"
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
      sudo tmux new-session -s "\${backend_app_name}" -d "make -C services/\${service} devel offline=\${OFFLINE}"
    else
      tmux new-session -s "\${backend_app_name}" -d "env OFFLINE=\${OFFLINE} SYSPKG=\${SYSPKG} \${PROJECT_ROOT}/services/\${service}/bin/devel.sh"
    fi
  else
    if [ "\${REGGAE}" = "yes" ]; then
      sudo tmux split-window -h -p 50 -t 0 "make -C services/\${service} BACKEND_URL=http://\${backend_hostname}:5000 devel offline=\${OFFLINE}"
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

  echo "Creating services"
  mkdir services
  cd services

  echo "Creating backend"
  backend
  mv "${NAME}" backend

  echo "Creating frontend"
  frontend
  mv "${NAME}" frontend
  cd ..
}


${TYPE}
