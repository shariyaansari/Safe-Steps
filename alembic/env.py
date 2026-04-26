from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
import asyncio

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import os
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import Base
import models

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in {
        "spatial_ref_sys", "topology", "layer", "edges", "faces",
        "node", "street_type_lookup", "zip_lookup", "zip_lookup_base",
        "zip_state", "zip_state_loc", "place_lookup", "county_lookup",
        "countysub_lookup", "direction_lookup", "secondary_unit_lookup",
        "state_lookup", "geocode_settings", "geocode_settings_default",
        "pagc_gaz", "pagc_lex", "pagc_rules", "loader_lookuptables",
        "loader_platform", "loader_variables", "addr", "addrfeat",
        "bg", "county", "cousub", "featnames", "place", "state", "tabblock",
        "tabblock20", "tract", "zcta5"
    }:
        return False
    return True

def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
