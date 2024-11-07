"""
db_wrapper_mysql package - MySQL database wrapper

Part of the db_wrapper package
"""

# Copyright 2024 Gints Murans

import logging

from .db_wrapper_mysql import DBWrapperMysql
from .connector import MyConfig, MySQL

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("db_wrapper_mysql")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


__all__ = [
    "DBWrapperMysql",
    "MyConfig",
    "MySQL",
]
