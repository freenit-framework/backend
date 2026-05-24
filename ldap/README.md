# OMEMO LDAP Schema

OpenLDAP schema extension for storing encrypted OMEMO device bundles on LDAP user entries.

## Files

- `omemo.schema` — traditional schema file for `slapd.conf` setups
- `omemo.ldif` — OLC/LDIF format for modern `cn=config` setups

## Loading the schema

### Traditional slapd.conf

Add to `slapd.conf`:

```
include /path/to/omemo.schema
```

Then restart `slapd`.

### Modern cn=config (OLC)

```bash
ldapadd -Y EXTERNAL -H ldapi:/// -f omemo.ldif
```

No restart required.

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
