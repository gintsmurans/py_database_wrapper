# type_mapping_pg.py
import datetime
from decimal import Decimal
from typing import Any

from database_wrapper import SerializeType

# Flip this if you want lossless decimals
USE_DECIMAL = False

_PG_TO_PY_BASE: dict[str, tuple[type, SerializeType | None]] = {
    # integers
    "int2": (int, None),
    "int4": (int, None),
    "int8": (int, None),
    # floats
    "float4": (float, None),
    "float8": (float, None),
    # bool
    "bool": (bool, None),
    "boolean": (bool, None),
    # text
    "text": (str, None),
    "varchar": (str, None),
    "bpchar": (str, None),
    "citext": (str, None),
    # json
    "json": (dict[str, Any], SerializeType.JSON),
    "jsonb": (dict[str, Any], SerializeType.JSON),
    # temporal
    "timestamptz": (datetime.datetime, SerializeType.DATETIME),
    "timestamp": (datetime.datetime, SerializeType.DATETIME),
    "date": (datetime.date, SerializeType.DATE),
    "time": (datetime.time, SerializeType.TIME),
    "timetz": (datetime.time, SerializeType.TIME),
    # UUID
    "uuid": (str, None),  # or python's uuid.UUID if you prefer
}


def map_db_type(
    db_type: str, *, length: int | None = None, precision: int | None = None, scale: int | None = None
) -> tuple[type, SerializeType | None]:
    t = db_type.lower()
    if t == "numeric":
        if USE_DECIMAL:
            return (Decimal, SerializeType.DECIMAL)
        return (float, None)

    # money: tends to need Decimal
    if t in ("money", "smallmoney"):
        return (Decimal, SerializeType.DECIMAL) if USE_DECIMAL else (float, None)

    # fall back to base
    return _PG_TO_PY_BASE.get(t, (str, None))
