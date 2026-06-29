"""Add blog tables.

Created: 2026-06-29 00:00:00
"""

depends_on = "0007_add_git"


def upgrade(ctx):
    """Apply migration."""
    ctx.create_table(
        "blog_tag",
        fields=[
            {
                "name": "id",
                "python_type": "int",
                "db_type": None,
                "nullable": True,
                "primary_key": True,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "name",
                "python_type": "str",
                "db_type": None,
                "nullable": False,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
        ],
        indexes=[
            {
                "name": "idx_blog_tag_name",
                "fields": ["name"],
                "unique": True,
            }
        ],
    )
    ctx.create_table(
        "blog_post",
        fields=[
            {
                "name": "id",
                "python_type": "int",
                "db_type": None,
                "nullable": True,
                "primary_key": True,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "title",
                "python_type": "str",
                "db_type": None,
                "nullable": False,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "slug",
                "python_type": "str",
                "db_type": None,
                "nullable": False,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "content",
                "python_type": "str",
                "db_type": None,
                "nullable": False,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "date",
                "python_type": "datetime",
                "db_type": None,
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "published",
                "python_type": "bool",
                "db_type": None,
                "nullable": False,
                "primary_key": False,
                "unique": False,
                "default": "0",
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "created_at",
                "python_type": "datetime",
                "db_type": None,
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "updated_at",
                "python_type": "datetime",
                "db_type": None,
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "author_id",
                "python_type": "int",
                "db_type": None,
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
        ],
        foreign_keys=[
            {
                "name": "fk_blog_post_author_id",
                "columns": ["author_id"],
                "ref_table": "user",
                "ref_columns": ["id"],
                "on_delete": "SET NULL",
                "on_update": "CASCADE",
            }
        ],
        indexes=[
            {
                "name": "idx_blog_post_slug",
                "fields": ["slug"],
                "unique": True,
            },
            {
                "name": "idx_blog_post_published",
                "fields": ["published"],
                "unique": False,
            },
        ],
    )
    ctx.create_table(
        "blog_post_tag",
        fields=[
            {
                "name": "id",
                "python_type": "int",
                "db_type": None,
                "nullable": True,
                "primary_key": True,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "post_id",
                "python_type": "int",
                "db_type": None,
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
            {
                "name": "tag_id",
                "python_type": "int",
                "db_type": None,
                "nullable": True,
                "primary_key": False,
                "unique": False,
                "default": None,
                "auto_increment": False,
                "max_length": None,
                "max_digits": None,
                "decimal_places": None,
            },
        ],
        foreign_keys=[
            {
                "name": "fk_blog_post_tag_post_id",
                "columns": ["post_id"],
                "ref_table": "blog_post",
                "ref_columns": ["id"],
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
            {
                "name": "fk_blog_post_tag_tag_id",
                "columns": ["tag_id"],
                "ref_table": "blog_tag",
                "ref_columns": ["id"],
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            },
        ],
        indexes=[
            {
                "name": "idx_blog_post_tag_post_id_tag_id",
                "fields": ["post_id", "tag_id"],
                "unique": True,
            }
        ],
    )


def downgrade(ctx):
    """Revert migration."""
    ctx.drop_table("blog_post_tag")
    ctx.drop_table("blog_post")
    ctx.drop_table("blog_tag")
