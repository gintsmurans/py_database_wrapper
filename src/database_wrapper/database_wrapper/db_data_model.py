from enum import Enum
import re
import json
import datetime
import dataclasses

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Literal, NotRequired, Type, TypeVar, TypedDict, cast

from .serialization import (
    SerializeType,
    deserialize_value,
    json_encoder,
    serialize_value,
)

EnumType = TypeVar("EnumType", bound=Enum)


class MetadataDict(TypedDict):
    db_field: tuple[str, str]
    store: bool
    update: bool
    exclude: NotRequired[bool]
    serialize: NotRequired[Callable[[Any], Any] | SerializeType | None]
    deserialize: NotRequired[Callable[[Any], Any] | None]
    enum_class: NotRequired[Type[Enum] | None]
    timezone: NotRequired[str | datetime.tzinfo | None]


@dataclass
class DBDataModel:
    """
    Base class for all database models.

    Attributes:
    - schema_name (str): The name of the schema in the database.
    - table_name (str): The name of the table in the database.
    - table_alias (str): The alias of the table in the database.
    - id_key (str): The name of the primary key column in the database.
    - id_value (Any): The value of the primary key for the current instance.
    - id (int): The primary key value for the current instance.

    Methods:
    - __post_init__(): Initializes the instance after it has been created.
    - __repr__(): Returns a string representation of the instance.
    - __str__(): Returns a JSON string representation of the instance.
    - to_dict(): Returns a dictionary representation of the instance.
    - to_formatted_dict(): Returns a formatted dictionary representation of the instance.
    - to_json_schema(): Returns a JSON schema for the instance.
    - json_encoder(obj: Any): Encodes the given object as JSON.
    - to_json_string(pretty: bool = False): Returns a JSON string representation of the instance.
    - str_to_datetime(value: Any): Converts a string to a datetime object.
    - str_to_bool(value: Any): Converts a string to a boolean value.
    - str_to_int(value: Any): Converts a string to an integer value.
    - validate(): Validates the instance.

    To enable storing and updating fields that by default are not stored or updated, use the following methods:
    - set_store(field_name: str, enable: bool = True): Enable/Disable storing a field.
    - set_update(field_name: str, enable: bool = True): Enable/Disable updating a field.

    To exclude a field from the dictionary representation of the instance, set metadata key "exclude" to True.
    To change exclude status of a field, use the following method:
    - set_exclude(field_name: str, enable: bool = True): Exclude a field from dict representation.
    """

    ######################
    ### Default fields ###
    ######################

    @property
    def schema_name(self) -> str | None:
        return None

    @property
    def table_name(self) -> str:
        raise NotImplementedError("`table_name` property is not implemented")

    @property
    def table_alias(self) -> str | None:
        return None

    @property
    def id_key(self) -> str:
        return "id"

    @property
    def id_value(self) -> Any:
        return getattr(self, self.id_key)

    # Id should be readonly by default and should be always present if record exists
    id: int = field(
        default=0,
        metadata={
            "db_field": ("id", "bigint"),
            "store": False,
            "update": False,
        },
    )
    """id is readonly by default"""

    # Raw data
    raw_data: dict[str, Any] = field(
        default_factory=dict,
        metadata={
            "db_field": ("raw_data", "jsonb"),
            "exclude": True,
            "store": False,
            "update": False,
        },
    )
    """This is for storing temporary raw data"""

    ##########################
    ### Conversion methods ###
    ##########################

    def fill_data_from_dict(self, kwargs: dict[str, Any]) -> None:
        field_names = set([f.name for f in dataclasses.fields(self)])
        for key in kwargs:
            if key in field_names:
                setattr(self, key, kwargs[key])

        self.__post_init__()

    # Init data
    def __post_init__(self) -> None:
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, field_obj.metadata)
            value = getattr(self, field_name)

            # If value is not set, we skip it
            if value is None:
                continue

            # If serialize is set, and serialize is a SerializeType,
            # we use our serialization function
            # Here we actually need to deserialize the value to correct class type
            serialize = metadata.get("serialize", None)
            enum_class = metadata.get("enum_class", None)
            timezone = metadata.get("timezone", None)
            if serialize is not None and isinstance(serialize, SerializeType):
                value = deserialize_value(value, serialize, enum_class, timezone)
                setattr(self, field_name, value)

            else:
                deserialize = metadata.get("deserialize", None)
                if deserialize is not None:
                    value = deserialize(value)
                    setattr(self, field_name, value)

    # String - representation
    def __repr__(self) -> str:
        return "<%s %s>" % (self.__class__.__name__, self.__dict__)

    def __str__(self) -> str:
        return self.to_json_string()

    # Dict
    def dict_filter(self, pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        new_dict: dict[str, Any] = {}
        for field in pairs:
            class_field = self.__dataclass_fields__.get(field[0], None)
            if class_field is not None:
                metadata = cast(MetadataDict, class_field.metadata)
                if not "exclude" in metadata or not metadata["exclude"]:
                    new_dict[field[0]] = field[1]

        return new_dict

    def to_dict(self) -> dict[str, Any]:
        return asdict(self, dict_factory=self.dict_filter)

    def to_formatted_dict(self) -> dict[str, Any]:
        return self.to_dict()

    # JSON
    def to_json_schema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
            },
        }
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, field_obj.metadata)
            assert (
                "db_field" in metadata and isinstance(metadata["db_field"], tuple) and len(metadata["db_field"]) == 2
            ), f"db_field metadata is not set for {field_name}"
            field_type: str = metadata["db_field"][1]
            schema["properties"][field_name] = {"type": field_type}

        return schema

    def json_encoder(self, obj: Any) -> Any:
        return json_encoder(obj)

    def to_json_string(self, pretty: bool = False) -> str:
        if pretty:
            return json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                indent=4,
                separators=(",", ": "),
                default=self.json_encoder,
            )

        return json.dumps(self.to_dict(), default=self.json_encoder)

    #######################
    ### Helper methods ####
    #######################

    @staticmethod
    def str_to_datetime(value: Any) -> datetime.datetime:
        if isinstance(value, datetime.datetime):
            return value

        if value and isinstance(value, str):
            pattern = r"^\d+(\.\d+)?$"
            if re.match(pattern, value):
                return datetime.datetime.fromtimestamp(float(value))

            return datetime.datetime.fromisoformat(value)

        return datetime.datetime.now(datetime.UTC)

    @staticmethod
    def str_to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if value:
            if isinstance(value, str):
                return value.lower() in ("true", "1")

            if isinstance(value, int):
                return value == 1

        return False

    @staticmethod
    def str_to_int(value: Any) -> int:
        if isinstance(value, int):
            return value

        if value and isinstance(value, str):
            return int(value)

        return 0

    def validate(self) -> Literal[True] | str:
        """
        True if the instance is valid, otherwise an error message.
        """
        raise NotImplementedError("`validate` is not implemented")

    def set_store(self, field_name: str, enable: bool = True) -> None:
        """
        Enable/Disable storing a field (insert into database)
        """
        if field_name in self.__dataclass_fields__:
            current_metadata = cast(
                MetadataDict,
                dict(self.__dataclass_fields__[field_name].metadata),
            )
            current_metadata["store"] = enable
            self.__dataclass_fields__[field_name].metadata = current_metadata

    def set_update(self, field_name: str, enable: bool = True) -> None:
        """
        Enable/Disable updating a field (update in database)
        """
        if field_name in self.__dataclass_fields__:
            current_metadata = cast(
                MetadataDict,
                dict(self.__dataclass_fields__[field_name].metadata),
            )
            current_metadata["update"] = enable
            self.__dataclass_fields__[field_name].metadata = current_metadata

    def set_exclude(self, field_name: str, enable: bool = True) -> None:
        """
        Exclude a field from dict representation
        """
        if field_name in self.__dataclass_fields__:
            current_metadata = cast(
                MetadataDict,
                dict(self.__dataclass_fields__[field_name].metadata),
            )
            current_metadata["exclude"] = enable
            self.__dataclass_fields__[field_name].metadata = current_metadata

    ########################
    ### Database methods ###
    ########################

    def query_base(self) -> Any:
        """
        Base query for all queries
        """
        return None

    def store_data(self) -> dict[str, Any] | None:
        """
        Store data to database
        """
        store_data: dict[str, Any] = {}
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, field_obj.metadata)
            if "store" in metadata and metadata["store"] == True:
                store_data[field_name] = getattr(self, field_name)

                # If serialize is set, and serialize is a SerializeType,
                # we use our serialization function.
                # Otherwise, we use the provided serialize function
                # and we assume that it is callable
                serialize = metadata.get("serialize", None)
                if serialize is not None:
                    if isinstance(serialize, SerializeType):
                        store_data[field_name] = serialize_value(store_data[field_name], serialize)
                    else:
                        store_data[field_name] = serialize(store_data[field_name])

        return store_data

    def update_data(self) -> dict[str, Any] | None:
        """
        Update data to database
        """

        update_data: dict[str, Any] = {}
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, field_obj.metadata)
            if "update" in metadata and metadata["update"] == True:
                update_data[field_name] = getattr(self, field_name)

                # If serialize is set, and serialize is a SerializeType,
                # we use our serialization function.
                # Otherwise, we use the provided serialize function
                # and we assume that it is callable
                serialize = metadata.get("serialize", None)
                if serialize is not None:
                    if isinstance(serialize, SerializeType):
                        update_data[field_name] = serialize_value(update_data[field_name], serialize)
                    else:
                        update_data[field_name] = serialize(update_data[field_name])

        return update_data


@dataclass
class DBDefaultsDataModel(DBDataModel):
    """
    This class includes default fields for all database models.

    Attributes:
    - created_at (datetime.datetime): The timestamp of when the instance was created.
    - updated_at (datetime.datetime): The timestamp of when the instance was last updated.
    - enabled (bool): Whether the instance is enabled or not.
    - deleted (bool): Whether the instance is deleted or not.
    """

    ######################
    ### Default fields ###
    ######################

    created_at: datetime.datetime = field(
        default_factory=datetime.datetime.now,
        metadata={
            "db_field": ("created_at", "timestamptz"),
            "store": True,
            "update": False,
            "serialize": SerializeType.DATETIME,
        },
    )
    """created_at is readonly by default and should be present in all tables"""

    updated_at: datetime.datetime = field(
        default_factory=datetime.datetime.now,
        metadata={
            "db_field": ("updated_at", "timestamptz"),
            "store": True,
            "update": True,
            "serialize": SerializeType.DATETIME,
        },
    )
    """updated_at should be present in all tables and is updated automatically"""

    disabled_at: datetime.datetime = field(
        default_factory=datetime.datetime.now,
        metadata={
            "db_field": ("disabled_at", "timestamptz"),
            "store": False,
            "update": False,
            "serialize": SerializeType.DATETIME,
        },
    )

    deleted_at: datetime.datetime = field(
        default_factory=datetime.datetime.now,
        metadata={
            "db_field": ("deleted_at", "timestamptz"),
            "store": False,
            "update": False,
            "serialize": SerializeType.DATETIME,
        },
    )

    enabled: bool = field(
        default=True,
        metadata={
            "db_field": ("enabled", "boolean"),
            "store": False,
            "update": False,
        },
    )
    deleted: bool = field(
        default=False,
        metadata={
            "db_field": ("deleted", "boolean"),
            "store": False,
            "update": False,
        },
    )

    def update_data(self) -> dict[str, Any] | None:
        """
        Update data to database
        """

        # Update updated_at
        self.updated_at = datetime.datetime.now(datetime.UTC)

        return super().update_data()
