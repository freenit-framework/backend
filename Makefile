SERVICE = backend
REGGAE_PATH :=/usr/local/share/reggae

.if exists(provisioners.mk)
.include <provisioners.mk>
.endif
.include <${REGGAE_PATH}/mk/service.mk>
