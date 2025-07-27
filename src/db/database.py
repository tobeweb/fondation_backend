"""Database helpers for interacting with Aurora Serverless or local SQLite.

The Lambda runtime resolves database connection parameters from environment variables
populated via the `serverless.yml` file and SSM Parameter Store.

During *local* development (i.e. when `STAGE == 'dev'` and `AWS_SAM_LOCAL` or
`IS_OFFLINE` env vars are truthy) we fall back to an in–process SQLite database
so that unit-tests and `serverless-offline` can run without AWS resources.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


_RDS_CLIENT = boto3.client("rds")


def _build_rds_engine() -> Engine:
    """Build a SQLAlchemy engine that authenticates to Aurora using IAM tokens."""
    host = os.environ["DB_HOST"]
    port = int(os.environ.get("DB_PORT", 3306))
    user = os.environ["DB_USER"]
    db_name = os.environ["DB_NAME"]
    region = os.environ.get("AWS_REGION", "eu-west-1")

    # Generate a short-lived auth token (15 min validity)
    password = _RDS_CLIENT.generate_db_auth_token(
        DBHostname=host, Port=port, DBUsername=user, Region=region
    )

    conn_str = (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        "?ssl_ca=rds-combined-ca-bundle.pem"
    )
    return create_engine(conn_str, pool_pre_ping=True, pool_recycle=300)


def _build_sqlite_engine() -> Engine:
    """Return an in-memory SQLite engine for local/dev usage."""
    return create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)


# Cache the engine after the first call for reuse across Lambda invocations
_engine: Engine | None = None


def get_engine() -> Engine:
    """Return a shared SQLAlchemy engine instance based on the environment."""
    global _engine

    if _engine is not None:
        return _engine

    is_offline = os.getenv("IS_OFFLINE") == "true" or os.getenv("AWS_SAM_LOCAL")
    stage = os.getenv("STAGE", "dev")

    if is_offline or stage == "dev":
        _engine = _build_sqlite_engine()
    else:
        _engine = _build_rds_engine()
    return _engine


@contextmanager
def db_session() -> Generator[Engine, None, None]:
    """Provide a transactional scope around a series of operations.

    Usage
    -----
    >>> with db_session() as conn:
    ...     conn.execute(text("SELECT 1"))
    """
    engine = get_engine()
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            yield connection
            trans.commit()
        except Exception:  # noqa: BLE001
            trans.rollback()
            raise 