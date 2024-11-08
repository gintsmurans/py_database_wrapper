"""
database_wrapper package - Base for database wrappers
"""

# Copyright 2024 Gints Murans

import logging

from . import utils
from .db_backend import DatabaseBackend
from .db_data_model import DBDataModel, DBDefaultsDataModel
from .db_wrapper import DBWrapper, T, OrderByItem

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("database_wrapper")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


# Expose the classes
__all__ = [
    "DatabaseBackend",
    "DBDataModel",
    "DBDefaultsDataModel",
    "DBWrapper",
    "T",
    "OrderByItem",
    "utils",
]
