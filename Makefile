CBSD_WORKDIR != sysrc -n cbsd_workdir
SERVICE = backend
REGGAE_PATH :=/usr/local/share/reggae

.if exists(provisioners.mk)
.include <provisioners.mk>
.endif
.include <${REGGAE_PATH}/mk/service.mk>

print-virtualenv:
	@echo ${CBSD_WORKDIR}/jails-data/${SERVICE}-data/usr/home/devel/.virtualenvs/backend

shell: up
	@sudo cbsd jexec user=devel jname=${SERVICE} /usr/src/bin/shell.sh
