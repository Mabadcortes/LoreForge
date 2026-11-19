"""Alembic migration environment.

Migrations run with a synchronous engine (same psycopg 3 driver). They are a
one-off CLI process, so async adds nothing here, and a sync connection also
avoids the Windows ProactorEventLoop limitation of psycopg async.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import get_settings
from app.db.base import Base

# Import every model module here (e.g. `import app.models`) once they exist,
# so their tables are registered in Base.metadata for --autogenerate.

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Passed as a URL object, never via config.set_main_option(): the .ini parser
# would treat '%' characters in an escaped password as interpolation.
database_url = get_settings().database_url


def run_migrations_offline() -> None:
    """Emit the SQL to stdout instead of executing it (alembic upgrade --sql)."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply the migrations."""
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
