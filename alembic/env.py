import os
import sys

from alembic import context
from freenit.migration import run_migrations_offline, run_migrations_online

sys.path.append(os.getcwd())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
