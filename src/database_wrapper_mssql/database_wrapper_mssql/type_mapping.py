# type_mapping_mssql.py
import datetime
from decimal import Decimal

from database_wrapper import SerializeType

USE_DECIMAL = False

_MSSQL_TO_PY_BASE: dict[str, tuple[type, SerializeType | None]] = {
    # integers
    "tinyint": (int, None),  # 0..255 (note!)
    "smallint": (int, None),
    "int": (int, None),
    "bigint": (int, None),
    # floats
    "float": (float, None),  # double precision
    "real": (float, None),
    # bits
    "bit": (bool, None),
    # character
    "char": (str, None),
    "nchar": (str, None),
    "varchar": (str, None),
    "nvarchar": (str, None),
    "text": (str, None),
    "ntext": (str, None),
    # binary
    "binary": (bytes, None),
    "varbinary": (bytes, None),
    "image": (bytes, None),
    # temporal
    "date": (datetime.date, SerializeType.DATE),
    "time": (datetime.time, SerializeType.TIME),
    "smalldatetime": (datetime.datetime, SerializeType.DATETIME),
    "datetime": (datetime.datetime, SerializeType.DATETIME),
    "datetime2": (datetime.datetime, SerializeType.DATETIME),
    "datetimeoffset": (datetime.datetime, SerializeType.DATETIME),  # has TZ info
    # uniqueidentifier
    "uniqueidentifier": (str, None),  # or uuid.UUID if you prefer
}


def map_db_type(
    db_type: str, *, length: int | None = None, precision: int | None = None, scale: int | None = None
) -> tuple[type, SerializeType | None]:
    t = db_type.lower()

    # decimal/numeric with precision/scale
    if t in ("decimal", "numeric"):
        if USE_DECIMAL:
            return (Decimal, SerializeType.DECIMAL)
        return (float, None)

    # xml? treat as str (or dict with custom parser)
    if t == "xml":
        return (str, None)

    # geography/geometry -> str (or custom WKT/WKB class if you have one)
    if t in ("geography", "geometry"):
        return (str, None)

    # JSON in SQL Server isn’t a native type; teams store it in nvarchar(max) + ISJSON() checks.
    # If you detect that at introspection-time, you can override to JSON here.
    # e.g., if typ == nvarchar and col_has_isjson_flag: return (dict[str, Any], SerializeType.JSON)

    return _MSSQL_TO_PY_BASE.get(t, (str, None))
