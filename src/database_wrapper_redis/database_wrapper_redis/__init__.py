"""
database_wrapper_redis package - PostgreSQL database wrapper

Part of the database_wrapper package
"""

# Copyright 2024 Gints Murans

import logging

from .connector import (
    # Basics
    RedisConfig,
    RedisDefaultConfig,
    # Connectors
    RedisDB,
    RedisDBAsync,
    RedisDBWithPool,
    RedisDBWithPoolAsync,
    # Connection and Cursor types
    RedisClient,
    RedisClientAsync,
    RedisConnection,
    RedisConnectionAsync,
)

# Set the logger to a quiet default, can be enabled if needed
logger = logging.getLogger("database_wrapper_redis")
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


__all__ = [
    # Connectors
    "RedisDB",
    "RedisDBAsync",
    "RedisDBWithPool",
    "RedisDBWithPoolAsync",
    # Connection and Cursor types
    "RedisClient",
    "RedisClientAsync",
    "RedisConnection",
    "RedisConnectionAsync",
    # Helpers
    "RedisConfig",
    "RedisDefaultConfig",
]
