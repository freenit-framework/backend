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
      ${SED_CMD} '' -e "s/NAME/${NAME}/g" main.py
      ${SED_CMD} '' -e "s/NAME/${NAME}/g" pyproject.toml
      ;;
    *)
      ${SED_CMD} -e "s/NAME/${NAME}/g" main.py
      ${SED_CMD} -e "s/NAME/${NAME}/g" pyproject.toml
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

  echo "Success!"
  cd ..
}


frontend() {
  npx sv create "${NAME}"
  cd "${NAME}"
  case `uname` in
    *BSD)
      ${SED_CMD} '' -e "s/export default defineConfig/const config = defineConfig/" vite.config.ts
      ${SED_CMD} '' -e 's/^\t}$/\t},/' package.json
      ${SED_CMD} '' -e "s/^}//" package.json
      ;;
    *)
      ${SED_CMD} -e "s/export default defineConfig/const config = defineConfig/" vite.config.ts
      ${SED_CMD} -e 's/^\t}$/\t},/' package.json
      ${SED_CMD} -e "s/^}//" package.json
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
  "printWidth": 100,
  "semi": false,
}
EOF

  npm install
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

  cat >build.sh<<EOF
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
  chmod +x build.sh

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
.netlify
.wrangler
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

  npm install --save-dev @zerodevx/svelte-toast @freenit-framework/core @sveltejs/adapter-node @mdi/js

  rm -rf src/lib
  rm -rf src/routes/about src/routes/sverdle src/routes/*.svelte src/app.css

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
<script lang="ts">
  import './styles.css'
  import 'chota'
  import { onMount } from 'svelte'
  import { SvelteToast } from '@zerodevx/svelte-toast'
  import { LeftPane, MenuItems, MenuBar } from '@freenit-framework/core'
  import store from '\$lib/store'

  const options = {}
  let { children } = \$props()
  let open = \$state(false)

  const toggle = () => {
    open = !open
  }

  const logout = async () => {
    open = !open
    await store.auth.logout()
  }

  onMount(async () => { await store.auth.refresh_token() })
</script>

<svelte:head>
  <title>${NAME}</title>
  <meta name="${NAME}" content="${NAME}" />
</svelte:head>

<SvelteToast {options} />
<LeftPane {open} {toggle}>
  <MenuItems {toggle} {logout} {store} />
</LeftPane>

<section class="root">
  <MenuBar {toggle} title="${NAME}" />
  <div class="main">
    {@render children?.()}
  </div>
</section>

<style>
  .root {
    height: 100dvh;
    display: flex;
    flex-direction: column;
  }

  .main {
    height: 100%;
    width: 100%;
  }
</style>
EOF

  cat >src/routes/+page.svelte <<EOF
<div class="root">
  <div>Landing page is in src/routes/+page.svelte</div>
  <div>Menu and layout are in src/routes/+layout.svelte</div>
</div>
EOF

  mkdir src/routes/login
  cat >src/routes/login/+page.svelte <<EOF
<script lang="ts">
  import { Login } from '@freenit-framework/core'
  import store from '\$lib/store'
</script>

<Login store={store} />
EOF

  mkdir src/routes/register
  cat >src/routes/register/+page.svelte <<EOF
<script lang="ts">
  import { Register } from '@freenit-framework/core'
  import store from '\$lib/store'
</script>

<Register store={store} />
EOF

  mkdir -p 'src/routes/verify/[token]'
  cat >'src/routes/verify/[token]/+page.ts' <<EOF
export const load = ({ params }) => {
  return {
    token: params.token
  }
}
EOF
  cat >'src/routes/verify/[token]/+page.svelte' <<EOF
<script lang="ts">
  import { onMount } from 'svelte'
  import { goto } from '\$app/navigation'
  import store from '\$lib/store'

  const { data: props } = \$props()

  onMount(async () => {
    const response = await store.auth.verify(props.token)
    if (response.ok) {
      goto('/login')
    }
  })
</script>
EOF
  cat >'src/routes/verify/+page.svelte' <<EOF
<div class="root">
  <h1>Welcome</h1>
  <p>You should receive email to verify your account shortly!</p>
</div>

<style>
  .root {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    height: 100%;
  }
</style>
EOF

  mkdir -p 'src/routes/users/[pk]'
  cat >'src/routes/users/[pk]/+page.ts' <<EOF
export const load = ({ params }) => {
  return {
    pk: params.pk
  }
}
EOF
  cat >'src/routes/users/[pk]/+page.svelte' <<EOF
<script lang="ts">
  import { User } from '@freenit-framework/core'
  import store from '\$lib/store'

  const { data: props } = \$props()
</script>

<User pk={props.pk} store={store} />
EOF
  cat >'src/routes/users/+page.svelte' <<EOF
<script lang="ts">
  import { Users } from '@freenit-framework/core'
  import store from '\$lib/store'
</script>

<Users store={store} />
EOF

  mkdir -p 'src/routes/roles/[pk]'
  cat >'src/routes/roles/[pk]/+page.ts' <<EOF
export const load = ({ params }) => {
  return {
    pk: params.pk
  }
}
EOF
  cat >'src/routes/roles/[pk]/+page.svelte' <<EOF
<script lang="ts">
  import { Role } from '@freenit-framework/core'
  import store from '\$lib/store'

  const { data: props } = \$props()
</script>

<Role pk={props.pk} store={store} />
EOF
  cat >'src/routes/roles/+page.svelte' <<EOF
<script lang="ts">
  import { Roles } from '@freenit-framework/core'
  import store from '\$lib/store'
</script>

<Roles store={store} />
EOF

  mkdir -p 'src/routes/profile'
  cat >'src/routes/profile/+page.svelte' <<EOF
<script lang="ts">
  import { Profile } from '@freenit-framework/core'
  import store from '\$lib/store'
</script>

<Profile store={store} />
EOF

  mkdir -p src/lib/store
  cat >'src/lib/store/index.ts' <<EOF
import { BaseStore } from '@freenit-framework/core'

class Store extends BaseStore {
  constructor(prefix='/api/v1') {
    super(prefix)
  }
}

const store = new Store()
export default store
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
      sudo tmux split-window -t 0 "make -C services/\${service} BACKEND_URL=http://\${backend_hostname}:5000 devel offline=\${OFFLINE}"
    else
      tmux split-window -t 0 "env OFFLINE=\${OFFLINE} BACKEND_URL=http://\${backend_hostname}:5000 \${PROJECT_ROOT}/services/\${service}/bin/devel.sh"
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
