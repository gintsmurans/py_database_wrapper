"""
database_wrapper_pgsql package - PostgreSQL database wrapper

Part of the database_wrapper package
"""

# Copyright 2024 Gints Murans

import logging

from .db_wrapper_pgsql import DBWrapperPgSQL
from .connector import PgConfig, AsyncPgSQLWithPooling, PgSQL

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("database_wrapper_pgsql")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


__all__ = [
    "DBWrapperPgSQL",
    "PgConfig",
    "AsyncPgSQLWithPooling",
    "PgSQL",
]
