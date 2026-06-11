# OMEMO LDAP Schema

OpenLDAP schema extension for storing encrypted OMEMO device bundles.

## Files

- `omemo.schema` — traditional schema file for `slapd.conf`
- `omemo.ldif` — OLC format for `cn=config`

## Loading

### slapd.conf

```
include /path/to/omemo.schema
```

Then restart `slapd`.

### cn=config

```bash
ldapadd -Y EXTERNAL -H ldapi:/// -f omemo.ldif
```

## Adding omemoPerson to existing accounts

```bash
ldapmodify -x -D "cn=admin,dc=ldap" -W <<EOF
dn: uid=alice,dc=example,dc=com
changetype: modify
add: objectClass
objectClass: omemoPerson
EOF
```

## Freenit config

```python
from freenit.base_config import LDAP

ldap = LDAP(
    host="ldap.example.com",
    userClasses=["pilotPerson", "posixAccount", "omemoPerson"],
    userOmemoAttr="omemoBundle",
)
```
