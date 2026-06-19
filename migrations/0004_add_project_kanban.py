"""Auto-generated migration.

Created: 2026-06-19 21:10:05
"""

depends_on = "0003_create_mailing_list_table"


def upgrade(ctx):
    """Apply migration."""
    ctx.create_table(
        "project",
        fields=[
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'name',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'description',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'created_by_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_project_created_by_id',
                'columns': [
                    'created_by_id'
                ],
                'ref_table': 'user',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'SET NULL',
                'on_update': 'CASCADE'
            }
        ],
    )
    ctx.create_table(
        "board",
        fields=[
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'name',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'description',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'project_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_board_project_id',
                'columns': [
                    'project_id'
                ],
                'ref_table': 'project',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            }
        ],
        indexes=[
            {
                'name': 'idx_board_project_id_name',
                'fields': ['project_id', 'name'],
                'unique': True,
            }
        ],
    )
    ctx.create_table(
        "board_column",
        fields=[
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'name',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'position',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'board_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_board_column_board_id',
                'columns': [
                    'board_id'
                ],
                'ref_table': 'board',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            }
        ],
        indexes=[
            {
                'name': 'idx_board_column_board_id_name',
                'fields': ['board_id', 'name'],
                'unique': True,
            }
        ],
    )
    ctx.create_table(
        "task",
        fields=[
            {
                'name': 'id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': True,
                'unique': True,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'title',
                'python_type': 'str',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'description',
                'python_type': 'str',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'position',
                'python_type': 'int',
                'db_type': None,
                'nullable': False,
                'primary_key': False,
                'unique': False,
                'default': '0',
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'created_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'updated_at',
                'python_type': 'datetime',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'column_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'assignee_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            },
            {
                'name': 'parent_id',
                'python_type': 'int',
                'db_type': None,
                'nullable': True,
                'primary_key': False,
                'unique': False,
                'default': None,
                'auto_increment': False,
                'max_length': None,
                'max_digits': None,
                'decimal_places': None
            }
        ],
        foreign_keys=[
            {
                'name': 'fk_task_column_id',
                'columns': [
                    'column_id'
                ],
                'ref_table': 'board_column',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'name': 'fk_task_assignee_id',
                'columns': [
                    'assignee_id'
                ],
                'ref_table': 'user',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'SET NULL',
                'on_update': 'CASCADE'
            },
            {
                'name': 'fk_task_parent_id',
                'columns': [
                    'parent_id'
                ],
                'ref_table': 'task',
                'ref_columns': [
                    'id'
                ],
                'on_delete': 'SET NULL',
                'on_update': 'CASCADE'
            }
        ],
    )


def downgrade(ctx):
    """Revert migration."""
    ctx.drop_table("task")
    ctx.drop_table("board_column")
    ctx.drop_table("board")
    ctx.drop_table("project")
