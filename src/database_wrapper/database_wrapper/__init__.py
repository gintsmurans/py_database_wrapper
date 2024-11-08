"""
database_wrapper package - Base for database wrappers
"""

# Copyright 2024 Gints Murans

import logging

from . import utils
from .db_backend import DatabaseBackend
from .db_data_model import DBDataModel, DBDefaultsDataModel
from .db_wrapper_interface import DBWrapperInterface, OrderByItem, NoParam, T
from .db_wrapper import DBWrapper
from .db_wrapper_async import DBWrapperAsync

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("database_wrapper")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


# Expose the classes
__all__ = [
    # Database backend
    "DatabaseBackend",
    # Data models
    "DBDataModel",
    "DBDefaultsDataModel",
    # Wrappers
    "DBWrapperInterface",
    "DBWrapper",
    "DBWrapperAsync",
    # Helpers
    "OrderByItem",
    "NoParam",
    "T",
    "utils",
]
