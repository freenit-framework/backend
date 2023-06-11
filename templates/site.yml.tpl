# -*- mode: ansible -*-
# vi: set ft=ansible :

---
- name: SERVICE provisioning
  hosts: SERVICE
  roles:
    - onelove-roles.freebsd-common
    - onelove-roles.freebsd_freenit
    - onelove-roles.freebsd_freenit_sql
    - onelove-roles.freebsd_freenit_ldap
    - devel
