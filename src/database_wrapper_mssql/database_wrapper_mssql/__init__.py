"""
db_wrap_mssql package - MSSQL database wrapper

Part of the db_wrap package
"""

# Copyright 2024 Gints Murans

import logging

from .db_wrapper_mssql import DBWrapperMSSQL
from .connector import MsConfig, MSSQL

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("db_wrap_mssql")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


__all__ = [
    "DBWrapperMSSQL",
    "MsConfig",
    "MSSQL",
]
