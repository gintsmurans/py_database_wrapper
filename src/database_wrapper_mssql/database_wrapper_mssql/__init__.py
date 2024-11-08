"""
database_wrapper_mssql package - MSSQL database wrapper

Part of the database_wrapper package
"""

# Copyright 2024 Gints Murans

import logging

from .db_wrapper_mssql import DBWrapperMSSQL
from .connector import MsConfig, MSSQL

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("database_wrapper_mssql")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


__all__ = [
    "DBWrapperMSSQL",
    "MsConfig",
    "MSSQL",
]
