"""Alembic environment. Migrations run as the schema owner, never as the app role."""
import os

from sqlalchemy import create_engine, text

from alembic import context

config = context.config


def _url() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        raise RuntimeError("MIGRATION_DATABASE_URL is not set (owner credentials required)")
    return url


def run_migrations_online() -> None:
    engine = create_engine(_url())
    with engine.connect() as connection:
        connection.execute(text("SET search_path TO sethu, public"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=None,
            version_table="alembic_version",
            version_table_schema="sethu",
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported; run against the database.")
run_migrations_online()
