# LDAP Schemas

This directory contains optional OpenLDAP schema extensions used by Freenit.

## Files

- `omemo.schema` / `omemo.ldif` — OMEMO device bundle storage on user entries.
- `mailinglist.schema` / `mailinglist.ldif` — mailing list metadata storage in LDAP.

## Loading the schemas

### Traditional `slapd.conf`

```
include /path/to/omemo.schema
include /path/to/mailinglist.schema
```

Then restart `slapd`.

### Modern `cn=config` (OLC)

```bash
ldapadd -Y EXTERNAL -H ldapi:/// -f omemo.ldif
ldapadd -Y EXTERNAL -H ldapi:/// -f mailinglist.ldif
```

No restart required.

---

# OMEMO LDAP Schema

OpenLDAP schema extension for storing encrypted OMEMO device bundles on LDAP user entries.

## Adding omemoPerson to existing accounts

`omemoPerson` is an **auxiliary** object class, so it can be added to existing entries without recreating them.

### Single user

```bash
ldapmodify -x -D "cn=admin,dc=ldap" -W <<EOF
dn: uid=alice,ou=example.com,dc=account,dc=ldap
changetype: modify
add: objectClass
objectClass: omemoPerson
EOF
```

### All users at once

```bash
ldapsearch -x -b "dc=account,dc=ldap" "(objectClass=posixAccount)" dn | \
  awk '/^dn: /{print $0 "\nchangetype: modify\nadd: objectClass\nobjectClass: omemoPerson\n"}' | \
  ldapmodify -x -D "cn=admin,dc=ldap" -W
```

### Programmatically (bonsai)

```python
from bonsai import LDAPClient, LDAPSearchScope

client = LDAPClient("ldap://ldap.example.com")
client.set_credentials("SIMPLE", "cn=admin,dc=ldap", "password")

async with client.connect(is_async=True) as conn:
    res = await conn.search(
        "dc=account,dc=ldap",
        LDAPSearchScope.SUB,
        "(objectClass=posixAccount)",
        ["dn"]
    )
    for entry in res:
        entry["objectClass"] = ["omemoPerson"]
        await entry.modify()
```

Accounts without `omemoPerson` still work fine — freenit falls back to an empty bundle until the class is added.

## Freenit configuration

Update your freenit config to use the new attribute and object class:

```python
ldap = LDAP(
    host="ldap.example.com",
    userClasses=["pilotPerson", "posixAccount", "omemoPerson"],
    userOmemoAttr="omemoBundle",
)
```

---

# Mailing List LDAP Schema

OpenLDAP schema extension for storing Freenit mailing list metadata in LDAP.

This includes:

- `freenitMailingList` — mailing list entries
- `freenitPendingSubscriber` — pending subscribe/unsubscribe tokens
- `freenitModerationMessage` — messages awaiting moderation
- `freenitMailingListIdNext` — global numeric ID counter

## Preparing the directory

Create the mailing list container and the ID counter before using the LDAP backend:

```bash
ldapadd -x -D "cn=admin,dc=ldap" -W <<EOF
dn: ou=mailinglists,dc=ldap
objectClass: organizationalUnit
ou: mailinglists

dn: cn=mlidnext,dc=ldap
objectClass: freenitMailingListIdNext
cn: mlidnext
mlidNumber: 1
EOF
```

## Freenit configuration

To store mailing list metadata in LDAP, point the model module at the LDAP implementation and configure the LDAP backend:

```python
from freenit.base_config import BaseConfig, LDAP

class BaseConfig(BaseConfig):
    mailinglist = "freenit.models.ldap.mailinglist"
    ldap = LDAP(
        host="ldap.example.com",
        service_dn="cn=freenit,dc=service,dc=ldap",
        service_pw="secret",
        mailinglistBase="ou=mailinglists,dc=ldap",
        mailinglistClasses=["freenitMailingList"],
        pendingSubscriberClasses=["freenitPendingSubscriber"],
        moderationMessageClasses=["freenitModerationMessage"],
        mlidNextDN="cn=mlidnext,dc=ldap",
        mlidNextClass="freenitMailingListIdNext",
        mlidNextField="mlidNumber",
    )
```

The default SQL backend remains active unless `mailinglist` is changed.
