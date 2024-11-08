"""
database_wrapper_sqlite package - Sqlite database wrapper

Part of the database_wrapper package
"""

# Copyright 2024 Gints Murans

import logging

# from .db_wrapper_sqlite import DBWrapperSqlite
from .connector import SqliteConfig, Sqlite

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("database_wrapper_sqlite")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


__all__ = [
    # "DBWrapperSqlite",
    "SqliteConfig",
    "Sqlite",
]
