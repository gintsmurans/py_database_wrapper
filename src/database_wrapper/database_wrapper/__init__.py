"""
database_wrapper package - Base for database wrappers
"""

# Copyright 2024 Gints Murans

import logging

from . import utils
from .db_backend import DatabaseBackend
from .db_data_model import MetadataDict, DBDataModel, DBDefaultsDataModel
from .common import OrderByItem, DataModelType, NoParam
from .db_wrapper import DBWrapper
from .db_wrapper_async import DBWrapperAsync
from .serialization import SerializeType
from .utils.dataclass_addons import ignore_unknown_kwargs

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
    "DBWrapper",
    "DBWrapperAsync",
    # Helpers
    "MetadataDict",
    "DataModelType",
    "OrderByItem",
    "NoParam",
    "utils",
    "SerializeType",
    "ignore_unknown_kwargs",
]
