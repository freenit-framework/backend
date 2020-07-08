.include <name.py>

USE_FREENIT = YES
SERVICE != echo ${app_name}
REGGAE_PATH := /usr/local/share/reggae

.include <${REGGAE_PATH}/mk/service.mk>

publish: build_lib
	@sudo cbsd jexec jname=${SERVICE} user=devel cmd=/usr/src/bin/publish.sh
