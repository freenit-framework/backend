"""Add omemo_bundle to user table.

Created: 2026-05-24
"""

depends_on = "0001_initial"


def upgrade(ctx):
    """Apply migration."""
    ctx.add_column(
        "user",
        {
            "name": "omemo_bundle",
            "python_type": "str",
            "db_type": None,
            "nullable": True,
            "primary_key": False,
            "unique": False,
            "default": None,
            "auto_increment": False,
        },
    )


def downgrade(ctx):
    """Revert migration."""
    ctx.drop_column("user", "omemo_bundle")
