import datetime
import json
from decimal import Decimal
from enum import Enum
from typing import Any
from zoneinfo import ZoneInfo


class SerializeType(Enum):
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    JSON = "json"
    ENUM = "enum"


def json_encoder(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%dT%H:%M:%S")

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, str):
        return obj

    return str(obj)


def serialize_value(value: Any, s_type: SerializeType) -> Any:
    if s_type == SerializeType.DATETIME:
        if not isinstance(value, datetime.datetime):
            return value

        return value.isoformat()

    if s_type == SerializeType.DATE:
        if not isinstance(value, datetime.date):
            return value

        return value.isoformat()

    if s_type == SerializeType.TIME:
        if not isinstance(value, datetime.time):
            return value

        return value.isoformat()

    if s_type == SerializeType.JSON:
        return json.dumps(value, default=json_encoder)

    if s_type == SerializeType.ENUM:
        return value.value
    return value


def deserialize_value(
    value: Any,
    s_type: SerializeType,
    enum_class: type[Enum] | None = None,
    timezone: str | datetime.tzinfo | None = None,
) -> Any:
    if s_type == SerializeType.DATETIME:
        if isinstance(value, datetime.datetime):
            return value

        value = str(value)
        if value.replace(".", "", 1).isdigit():
            timestamp = float(value)
            if timestamp > 1e10:  # Check if timestamp is in milliseconds
                timestamp /= 1000

            if timezone is not None and isinstance(timezone, str):
                timezone = ZoneInfo(timezone)

            return datetime.datetime.fromtimestamp(timestamp, tz=timezone)

        return datetime.datetime.fromisoformat(value)

    if s_type == SerializeType.DATE:
        if isinstance(value, datetime.date):
            return value

        return datetime.date.fromisoformat(str(value))

    if s_type == SerializeType.TIME:
        if isinstance(value, datetime.time):
            return value

        return datetime.time.fromisoformat(str(value))

    if s_type == SerializeType.JSON:
        if isinstance(value, dict) or isinstance(value, list) or value is None:
            return value

        return json.loads(value)

    if s_type == SerializeType.ENUM:
        if enum_class is None:
            raise ValueError("enum_class must be provided when deserializing Enum")

        if isinstance(value, Enum) or value is None:
            return value

        return enum_class(value)

    return value
