import datetime
import json
import re

from decimal import Decimal
from enum import Enum
from typing import Any, Type


class SerializeType(Enum):
    DATETIME = "datetime"
    JSON = "json"
    ENUM = "enum"


def jsonEncoder(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%dT%H:%M:%S")

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, str):
        return obj

    return str(obj)


def serializeValue(value: Any, sType: SerializeType) -> Any:
    if sType == SerializeType.DATETIME:
        if not isinstance(value, datetime.datetime):
            return value

        return value.isoformat()

    if sType == SerializeType.JSON:
        return json.dumps(value, default=jsonEncoder)

    if sType == SerializeType.ENUM:
        return value.value
    return value


def deserializeValue(
    value: Any,
    sType: SerializeType,
    enumClass: Type[Enum] | None = None,
) -> Any:
    if sType == SerializeType.DATETIME:
        if isinstance(value, datetime.datetime):
            return value

        if value and isinstance(value, str):
            pattern = r"^\d+(\.\d+)?$"
            if re.match(pattern, value):
                return datetime.datetime.fromtimestamp(float(value))

            return datetime.datetime.fromisoformat(value)

        return datetime.datetime.now(datetime.UTC)

    if sType == SerializeType.JSON:
        if isinstance(value, dict) or isinstance(value, list) or value is None:
            return value  # type: ignore

        return json.loads(value)

    if sType == SerializeType.ENUM:
        if enumClass is None:
            raise ValueError(
                "enumClass (enum_class) must be provided when deserializing Enum"
            )

        if isinstance(value, Enum) or value is None:
            return value

        return enumClass(value)

    return value
