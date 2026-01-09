"""
database_wrapper_pgsql package - PostgreSQL database wrapper

Part of the database_wrapper package
"""

# Copyright 2024 Gints Murans

import logging

from .connector import (
    # Basics
    PgConfig,
    # Connection and Cursor types
    PgConnectionType,
    PgConnectionTypeAsync,
    PgCursorType,
    PgCursorTypeAsync,
    # Connectors
    PgSQL,
    PgSQLAsync,
    PgSQLWithPooling,
    PgSQLWithPoolingAsync,
)
from .db_wrapper_pgsql import DBWrapperPgSQL
from .db_wrapper_pgsql_async import DBWrapperPgSQLAsync
from .pg_introspector import PostgresIntrospector

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("database_wrapper_pgsql")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


__all__ = [
    # Wrappers
    "DBWrapperPgSQL",
    "DBWrapperPgSQLAsync",
    # Connectors
    "PgSQL",
    "PgSQLAsync",
    "PgSQLWithPooling",
    "PgSQLWithPoolingAsync",
    # Connection and Cursor types
    "PgConnectionType",
    "PgCursorType",
    "PgConnectionTypeAsync",
    "PgCursorTypeAsync",
    # Helpers
    "PgConfig",
    "PostgresIntrospector",
]
