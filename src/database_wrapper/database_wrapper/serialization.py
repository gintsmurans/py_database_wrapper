import datetime
import json

from decimal import Decimal
from enum import Enum
from typing import Any, Type


class SerializeType(Enum):
    DATETIME = "datetime"
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

    if s_type == SerializeType.JSON:
        return json.dumps(value, default=json_encoder)

    if s_type == SerializeType.ENUM:
        return value.value
    return value


def deserialize_value(
    value: Any,
    s_type: SerializeType,
    enum_class: Type[Enum] | None = None,
) -> Any:
    if s_type == SerializeType.DATETIME:
        if isinstance(value, datetime.datetime):
            return value

        value = str(value)
        if value.replace(".", "", 1).isdigit():
            timestamp = float(value)
            if timestamp > 1e10:  # Check if timestamp is in milliseconds
                timestamp /= 1000
            return datetime.datetime.fromtimestamp(timestamp)

        return datetime.datetime.fromisoformat(value)

    if s_type == SerializeType.JSON:
        if isinstance(value, dict) or isinstance(value, list) or value is None:
            return value  # type: ignore

        return json.loads(value)

    if s_type == SerializeType.ENUM:
        if enum_class is None:
            raise ValueError("enum_class must be provided when deserializing Enum")

        if isinstance(value, Enum) or value is None:
            return value

        return enum_class(value)

    return value
