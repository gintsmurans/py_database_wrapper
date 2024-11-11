import re
import json
import datetime
import dataclasses

from enum import Enum
from dataclasses import dataclass, field, asdict

from decimal import Decimal
from typing import Any

from psycopg import sql


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
    - setStore(field_name: str, enable: bool = True): Enable/Disable storing a field.
    - setUpdate(field_name: str, enable: bool = True): Enable/Disable updating a field.

    To exclude a field from the dictionary representation of the instance, set metadata key "exclude" to True.
    To change exclude status of a field, use the following method:
    - setExclude(field_name: str, enable: bool = True): Exclude a field from dict representation.
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

    def fillDataFromDict(self, kwargs: dict[str, Any]):
        fieldNames = set([f.name for f in dataclasses.fields(self)])
        for key in kwargs:
            if key in fieldNames:
                setattr(self, key, kwargs[key])

        self.__post_init__()

    # Init data
    def __post_init__(self):
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = field_obj.metadata
            encode = metadata.get("encode", None)
            if encode is not None:
                setattr(self, field_name, encode(getattr(self, field_name)))

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
                metadata = classField.metadata
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
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = field_obj.metadata
            assert (
                "db_field" in metadata
                and isinstance(metadata["db_field"], tuple)
                and len(metadata["db_field"]) == 2
            ), f"db_field metadata is not set for {field_name}"
            fieldType: str = metadata["db_field"][1]
            schema["properties"][field_name] = {"type": fieldType}

        return schema

    def jsonEncoder(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)

        if isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S")

        if isinstance(obj, Enum):
            return obj.value

        if isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, str):
            return obj

        return str(obj)

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

    def validate(self) -> bool:
        raise NotImplementedError("`validate` is not implemented")

    def setStore(self, field_name: str, enable: bool = True) -> None:
        """
        Enable/Disable storing a field (insert into database)
        """
        if field_name in self.__dataclass_fields__:
            currentMetadata = self.__dataclass_fields__[field_name].metadata
            currentMetadata["store"] = enable
            self.__dataclass_fields__[field_name].metadata = currentMetadata

    def setUpdate(self, field_name: str, enable: bool = True) -> None:
        """
        Enable/Disable updating a field (update in database)
        """
        if field_name in self.__dataclass_fields__:
            currentMetadata = self.__dataclass_fields__[field_name].metadata
            currentMetadata["update"] = enable
            self.__dataclass_fields__[field_name].metadata = currentMetadata

    def setExclude(self, field_name: str, enable: bool = True) -> None:
        """
        Exclude a field from dict representation
        """
        if field_name in self.__dataclass_fields__:
            currentMetadata = dict(self.__dataclass_fields__[field_name].metadata)
            currentMetadata["exclude"] = enable
            self.__dataclass_fields__[field_name].metadata = currentMetadata

    ########################
    ### Database methods ###
    ########################

    def queryBase(self) -> sql.SQL | sql.Composed | str | None:
        """
        Base query for all queries
        """
        return None

    def storeData(self) -> dict[str, Any] | None:
        """
        Store data to database
        """
        storeData: dict[str, Any] = {}
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = field_obj.metadata
            if "store" in metadata and metadata["store"] == True:
                storeData[field_name] = getattr(self, field_name)

                if "decode" in metadata and metadata["decode"] is not None:
                    storeData[field_name] = metadata["decode"](storeData[field_name])

        return storeData

    def updateData(self) -> dict[str, Any] | None:
        """
        Update data to database
        """

        updateData: dict[str, Any] = {}
        for field_name, field_obj in self.__dataclass_fields__.items():
            metadata = field_obj.metadata
            if "update" in metadata and metadata["update"] == True:
                updateData[field_name] = getattr(self, field_name)

                if "decode" in metadata and metadata["decode"] is not None:
                    updateData[field_name] = metadata["decode"](updateData[field_name])

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
            "encode": lambda value: DBDataModel.strToDatetime(value),  # type: ignore
            "decode": lambda x: x.isoformat(),  # type: ignore
        },
    )
    """created_at is readonly by default and should be present in all tables"""

    updated_at: datetime.datetime = field(
        default_factory=datetime.datetime.now,
        metadata={
            "db_field": ("updated_at", "timestamptz"),
            "store": True,
            "update": True,
            "encode": lambda value: DBDataModel.strToDatetime(value),  # type: ignore
            "decode": lambda x: x.isoformat(),  # type: ignore
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
