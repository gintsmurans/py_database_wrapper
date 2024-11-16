from enum import Enum
import re
import json
import datetime
import dataclasses

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Literal, NotRequired, Type, TypeVar, TypedDict, cast

from .serialization import (
    SerializeType,
    deserializeValue,
    jsonEncoder,
    serializeValue,
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


@dataclass
class DBDataModel:
    """
    Base class for all database models.

    Attributes:
    - schemaName (str): The name of the schema in the database.
    - tableName (str): The name of the table in the database.
    - tableAlias (str): The alias of the table in the database.
    - idKey (str): The name of the primary key column in the database.
    - idValue (Any): The value of the primary key for the current instance.
    - id (int): The primary key value for the current instance.

    Methods:
    - __post_init__(): Initializes the instance after it has been created.
    - __repr__(): Returns a string representation of the instance.
    - __str__(): Returns a JSON string representation of the instance.
    - toDict(): Returns a dictionary representation of the instance.
    - toFormattedDict(): Returns a formatted dictionary representation of the instance.
    - toJsonSchema(): Returns a JSON schema for the instance.
    - jsonEncoder(obj: Any): Encodes the given object as JSON.
    - toJsonString(pretty: bool = False): Returns a JSON string representation of the instance.
    - strToDatetime(value: Any): Converts a string to a datetime object.
    - strToBool(value: Any): Converts a string to a boolean value.
    - strToInt(value: Any): Converts a string to an integer value.
    - validate(): Validates the instance.

    To enable storing and updating fields that by default are not stored or updated, use the following methods:
    - setStore(fieldName: str, enable: bool = True): Enable/Disable storing a field.
    - setUpdate(fieldName: str, enable: bool = True): Enable/Disable updating a field.

    To exclude a field from the dictionary representation of the instance, set metadata key "exclude" to True.
    To change exclude status of a field, use the following method:
    - setExclude(fieldName: str, enable: bool = True): Exclude a field from dict representation.
    """

    ######################
    ### Default fields ###
    ######################

    @property
    def schemaName(self) -> str | None:
        return None

    @property
    def tableName(self) -> str:
        raise NotImplementedError("`tableName` property is not implemented")

    @property
    def tableAlias(self) -> str | None:
        return None

    @property
    def idKey(self) -> str:
        return "id"

    @property
    def idValue(self) -> Any:
        return getattr(self, self.idKey)

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

    def fillDataFromDict(self, kwargs: dict[str, Any]) -> None:
        fieldNames = set([f.name for f in dataclasses.fields(self)])
        for key in kwargs:
            if key in fieldNames:
                setattr(self, key, kwargs[key])

        self.__post_init__()

    # Init data
    def __post_init__(self) -> None:
        for fieldName, fieldObj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, fieldObj.metadata)
            value = getattr(self, fieldName)

            # If serialize is set, and serialize is a SerializeType,
            # we use our serialization function
            # Here we actually need to deserialize the value to correct class type
            serialize = metadata.get("serialize", None)
            enumClass = metadata.get("enum_class", None)
            if serialize is not None and isinstance(serialize, SerializeType):
                value = deserializeValue(value, serialize, enumClass)
                setattr(self, fieldName, value)

            else:
                deserialize = metadata.get("deserialize", None)
                if deserialize is not None:
                    value = deserialize(value)
                    setattr(self, fieldName, value)

    # String - representation
    def __repr__(self) -> str:
        return "<%s %s>" % (self.__class__.__name__, self.__dict__)

    def __str__(self) -> str:
        return self.toJsonString()

    # Dict
    def dictFilter(self, pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        newDict: dict[str, Any] = {}
        for field in pairs:
            classField = self.__dataclass_fields__.get(field[0], None)
            if classField is not None:
                metadata = cast(MetadataDict, classField.metadata)
                if not "exclude" in metadata or not metadata["exclude"]:
                    newDict[field[0]] = field[1]

        return newDict

    def toDict(self) -> dict[str, Any]:
        return asdict(self, dict_factory=self.dictFilter)

    def toFormattedDict(self) -> dict[str, Any]:
        return self.toDict()

    # JSON
    def toJsonSchema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
            },
        }
        for fieldName, fieldObj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, fieldObj.metadata)
            assert (
                "db_field" in metadata
                and isinstance(metadata["db_field"], tuple)
                and len(metadata["db_field"]) == 2
            ), f"db_field metadata is not set for {fieldName}"
            fieldType: str = metadata["db_field"][1]
            schema["properties"][fieldName] = {"type": fieldType}

        return schema

    def jsonEncoder(self, obj: Any) -> Any:
        return jsonEncoder(obj)

    def toJsonString(self, pretty: bool = False) -> str:
        if pretty:
            return json.dumps(
                self.toDict(),
                ensure_ascii=False,
                sort_keys=True,
                indent=4,
                separators=(",", ": "),
                default=self.jsonEncoder,
            )

        return json.dumps(self.toDict(), default=self.jsonEncoder)

    #######################
    ### Helper methods ####
    #######################

    @staticmethod
    def strToDatetime(value: Any) -> datetime.datetime:
        if isinstance(value, datetime.datetime):
            return value

        if value and isinstance(value, str):
            pattern = r"^\d+(\.\d+)?$"
            if re.match(pattern, value):
                return datetime.datetime.fromtimestamp(float(value))

            return datetime.datetime.fromisoformat(value)

        return datetime.datetime.now(datetime.UTC)

    @staticmethod
    def strToBool(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if value:
            if isinstance(value, str):
                return value.lower() in ("true", "1")

            if isinstance(value, int):
                return value == 1

        return False

    @staticmethod
    def strToInt(value: Any) -> int:
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

    def setStore(self, fieldName: str, enable: bool = True) -> None:
        """
        Enable/Disable storing a field (insert into database)
        """
        if fieldName in self.__dataclass_fields__:
            currentMetadata = cast(
                MetadataDict,
                dict(self.__dataclass_fields__[fieldName].metadata),
            )
            currentMetadata["store"] = enable
            self.__dataclass_fields__[fieldName].metadata = currentMetadata

    def setUpdate(self, fieldName: str, enable: bool = True) -> None:
        """
        Enable/Disable updating a field (update in database)
        """
        if fieldName in self.__dataclass_fields__:
            currentMetadata = cast(
                MetadataDict,
                dict(self.__dataclass_fields__[fieldName].metadata),
            )
            currentMetadata["update"] = enable
            self.__dataclass_fields__[fieldName].metadata = currentMetadata

    def setExclude(self, fieldName: str, enable: bool = True) -> None:
        """
        Exclude a field from dict representation
        """
        if fieldName in self.__dataclass_fields__:
            currentMetadata = cast(
                MetadataDict,
                dict(self.__dataclass_fields__[fieldName].metadata),
            )
            currentMetadata["exclude"] = enable
            self.__dataclass_fields__[fieldName].metadata = currentMetadata

    ########################
    ### Database methods ###
    ########################

    def queryBase(self) -> Any:
        """
        Base query for all queries
        """
        return None

    def storeData(self) -> dict[str, Any] | None:
        """
        Store data to database
        """
        storeData: dict[str, Any] = {}
        for fieldName, fieldObj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, fieldObj.metadata)
            if "store" in metadata and metadata["store"] == True:
                storeData[fieldName] = getattr(self, fieldName)

                # If serialize is set, and serialize is a SerializeType,
                # we use our serialization function.
                # Otherwise, we use the provided serialize function
                # and we assume that it is callable
                serialize = metadata.get("serialize", None)
                if serialize is not None:
                    if isinstance(serialize, SerializeType):
                        storeData[fieldName] = serializeValue(
                            storeData[fieldName], serialize
                        )
                    else:
                        storeData[fieldName] = serialize(storeData[fieldName])

        return storeData

    def updateData(self) -> dict[str, Any] | None:
        """
        Update data to database
        """

        updateData: dict[str, Any] = {}
        for fieldName, fieldObj in self.__dataclass_fields__.items():
            metadata = cast(MetadataDict, fieldObj.metadata)
            if "update" in metadata and metadata["update"] == True:
                updateData[fieldName] = getattr(self, fieldName)

                # If serialize is set, and serialize is a SerializeType,
                # we use our serialization function.
                # Otherwise, we use the provided serialize function
                # and we assume that it is callable
                serialize = metadata.get("serialize", None)
                if serialize is not None:
                    if isinstance(serialize, SerializeType):
                        updateData[fieldName] = serializeValue(
                            updateData[fieldName], serialize
                        )
                    else:
                        updateData[fieldName] = serialize(updateData[fieldName])

        return updateData


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
    """updated_at is readonly by default and should be present in all tables"""

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

    def updateData(self) -> dict[str, Any] | None:
        """
        Update data to database
        """

        # Update updated_at
        self.updated_at = datetime.datetime.now(datetime.UTC)

        return super().updateData()
