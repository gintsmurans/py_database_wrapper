"""
database_wrapper_pgsql package - PostgreSQL database wrapper

Part of the database_wrapper package
"""

# Copyright 2024 Gints Murans

import logging

from .db_wrapper_pgsql import DBWrapperPgSQL
from .db_wrapper_pgsql_async import DBWrapperPgSQLAsync
from .connector import PgConfig, PgSQL, PgSQLWithPoolingAsync

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
    "PgSQLWithPoolingAsync",
    # Helpers
    "PgConfig",
]
