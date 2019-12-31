.include <name.py>

SERVICE != echo ${app_name}back
REGGAE_PATH := /usr/local/share/reggae

.include <${REGGAE_PATH}/mk/service.mk>
