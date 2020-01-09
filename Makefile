.include <name.py>

SERVICE != echo ${app_name}back
REGGAE_PATH := /usr/local/share/reggae

.include <${REGGAE_PATH}/mk/service.mk>

build:
	@sudo cbsd jexec jname=${SERVICE} user=devel cmd=/usr/src/bin/build.sh

publish: build
	@sudo cbsd jexec jname=${SERVICE} user=devel cmd=/usr/src/bin/publish.sh
