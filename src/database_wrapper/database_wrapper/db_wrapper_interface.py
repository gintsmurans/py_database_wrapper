import logging

from abc import ABC, abstractmethod
from typing import TypeVar, Any, overload

from .db_backend import DatabaseBackend
from .db_data_model import DBDataModel

OrderByItem = list[tuple[str, str | None]]


class NoParam:
    pass


# Bound T to DBDataModel
T = TypeVar("T", bound=DBDataModel)


class DBWrapperInterface(ABC):
    """
    Database wrapper class interface.

    This class defines the interface for the database wrapper classes.

    :property db: Database backend object.
    :property dbConn: Database connection object.
    :property logger: Logger object
    """

    ###########################
    ### Instance properties ###
    ###########################

    # Db backend
    db: DatabaseBackend
    """Database backend object."""

    dbConn: Any
    """Database connection object."""

    logger: logging.Logger | None
    """Logger object"""

    #######################
    ### Class lifecycle ###
    #######################

    @abstractmethod
    def __init__(
        self,
        db: DatabaseBackend,
        dbConn: Any = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (DatabaseBackend): The DatabaseBackend object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        ...

    @abstractmethod
    def __del__(self):
        """
        Deallocates the instance of the DBWrapper class.
        """
        ...

    @abstractmethod
    def close(self) -> Any:
        """
        Close resources. Usually you should not close connections here, just remove references.
        """
        ...

    ######################
    ### Helper methods ###
    ######################

    @abstractmethod
    def makeIdentifier(self, schema: str | None, name: str) -> Any:
        """
        Creates a SQL identifier object from the given name.

        Args:
            schema (str | None): The schema to create the identifier from.
            name (str): The name to create the identifier from.

        Returns:
            str: The created SQL identifier object.
        """
        ...

    @overload
    @abstractmethod
    def createCursor(self) -> Any: ...

    @overload
    @abstractmethod
    def createCursor(self, emptyDataClass: DBDataModel) -> Any: ...

    @abstractmethod
    def createCursor(self, emptyDataClass: DBDataModel | None = None) -> Any:
        """
        Creates a new cursor object.

        Args:
            emptyDataClass (T | None, optional): The data model to use for the cursor. Defaults to None.

        Returns:
            The created cursor object.
        """
        ...

    @abstractmethod
    def logQuery(self, cursor: Any, query: Any, params: tuple[Any, ...]) -> None:
        """
        Logs the given query and parameters.

        Args:
            cursor (Any): The database cursor.
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        ...

    @abstractmethod
    def turnDataIntoModel(
        self,
        emptyDataClass: T,
        dbData: dict[str, Any],
    ) -> T:
        """
        Turns the given data into a data model.
        By default we are pretty sure that there is no factory in the cursor,
        So we need to create a new instance of the data model and fill it with data

        Args:
            emptyDataClass (T): The data model to use.
            dbData (dict[str, Any]): The data to turn into a model.

        Returns:
            T: The data model filled with data.
        """
        ...

    #####################
    ### Query methods ###
    #####################

    @abstractmethod
    def filterQuery(self, schemaName: str | None, tableName: str) -> Any:
        """
        Creates a SQL query to filter data from the given table.

        Args:
            schemaName (str | None): The name of the schema to filter data from.
            tableName (str): The name of the table to filter data from.

        Returns:
            Any: The created SQL query object.
        """
        ...

    @abstractmethod
    def limitQuery(self, offset: int = 0, limit: int = 100) -> Any:
        """
        Creates a SQL query to limit the number of results returned.

        Args:
            offset (int, optional): The number of results to skip. Defaults to 0.
            limit (int, optional): The maximum number of results to return. Defaults to 100.

        Returns:
            Any: The created SQL query object.
        """
        ...

    @abstractmethod
    def getOne(
        self,
        emptyDataClass: Any,
        customQuery: Any = None,
    ) -> Any:
        """
        Retrieves a single record from the database.

        Args:
            emptyDataClass (Any): The data model to use for the query.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            Any: The result of the query.
        """
        ...

    @abstractmethod
    def getByKey(
        self,
        emptyDataClass: Any,
        idKey: str,
        idValue: Any,
        customQuery: Any = None,
    ) -> Any:
        """
        Retrieves a single record from the database using the given key.

        Args:
            emptyDataClass (Any): The data model to use for the query.
            idKey (str): The name of the key to use for the query.
            idValue (Any): The value of the key to use for the query.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            Any: The result of the query.
        """
        ...

    @abstractmethod
    def getAll(
        self,
        emptyDataClass: Any,
        idKey: str | None = None,
        idValue: Any | None = None,
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> Any:
        """
        Retrieves all records from the database.

        Args:
            emptyDataClass (T): The data model to use for the query.
            idKey (str | None, optional): The name of the key to use for filtering. Defaults to None.
            idValue (Any | None, optional): The value of the key to use for filtering. Defaults to None.
            orderBy (OrderByItem | None, optional): The order by item to use for sorting. Defaults to None.
            offset (int, optional): The number of results to skip. Defaults to 0.
            limit (int, optional): The maximum number of results to return. Defaults to 100.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            Any: The result of the query.
        """
        ...

    @abstractmethod
    def formatFilter(self, key: str, filter: Any) -> tuple[Any, ...]:
        """
        Formats a filter for the query.

        Args:
            key (str): The key to format.
            filter (Any): The filter to format.
        """
        ...

    @abstractmethod
    def createFilter(
        self, filter: dict[str, Any] | None
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Creates a filter for the query.

        Args:
            filter (dict[str, Any] | None): The filter to create.

        Returns:
            tuple[str, tuple[Any, ...]]: The created filter.
        """
        ...

    @abstractmethod
    def getFiltered(
        self,
        emptyDataClass: Any,
        filter: dict[str, Any],
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> Any: ...

    @abstractmethod
    def _store(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        storeData: dict[str, Any],
        idKey: str,
    ) -> Any:
        """
        Stores a record in the database.

        Args:
            emptyDataClass (DBDataModel): The data model to use for the query.
            schemaName (str | None): The name of the schema to store the record in.
            tableName (str): The name of the table to store the record in.
            storeData (dict[str, Any]): The data to store.
            idKey (str): The name of the key to use for the query.

        Returns:
            Any: The id of the record and the number of affected rows.
        """
        ...

    @overload
    @abstractmethod
    def store(self, records: T) -> Any:  # type: ignore
        ...

    @overload
    @abstractmethod
    def store(self, records: list[T]) -> Any: ...

    @abstractmethod
    def store(self, records: T | list[T]) -> Any:
        """
        Stores a record or a list of records in the database.

        Args:
            records (T | list[T]): The record or records to store.

        Returns:
            Any: The id of the record and
                the number of affected rows for a single record or a list of
                ids and the number of affected rows for a list of records.
        """
        ...

    @abstractmethod
    def _update(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        updateData: dict[str, Any],
        updateId: tuple[str, Any],
    ) -> Any:
        """
        Updates a record in the database.

        Args:
            emptyDataClass (DBDataModel): The data model to use for the query.
            schemaName (str | None): The name of the schema to update the record in.
            tableName (str): The name of the table to update the record in.
            updateData (dict[str, Any]): The data to update.
            updateId (tuple[str, Any]): The id of the record to update.

        Returns:
            Any: The number of affected rows.
        """
        ...

    @overload
    @abstractmethod
    def update(self, records: T) -> Any:  # type: ignore
        ...

    @overload
    @abstractmethod
    def update(self, records: list[T]) -> Any: ...

    @abstractmethod
    def update(self, records: T | list[T]) -> Any:
        """
        Updates a record or a list of records in the database.

        Args:
            records (T | list[T]): The record or records to update.

        Returns:
            Any: The number of affected rows for a single record or a list of
                affected rows for a list of records.
        """
        ...

    @abstractmethod
    def updateData(
        self,
        record: DBDataModel,
        updateData: dict[str, Any],
        updateIdKey: str | None = None,
        updateIdValue: Any = None,
    ) -> Any: ...

    @abstractmethod
    def _delete(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        deleteId: tuple[str, Any],
    ) -> Any:
        """
        Deletes a record from the database.

        Args:
            emptyDataClass (DBDataModel): The data model to use for the query.
            schemaName (str | None): The name of the schema to delete the record from.
            tableName (str): The name of the table to delete the record from.
            deleteId (tuple[str, Any]): The id of the record to delete.

        Returns:
            Any: The number of affected rows.
        """
        ...

    @overload
    @abstractmethod
    def delete(self, records: T) -> Any:  # type: ignore
        ...

    @overload
    @abstractmethod
    def delete(self, records: list[T]) -> Any: ...

    @abstractmethod
    def delete(self, records: T | list[T]) -> Any:
        """
        Deletes a record or a list of records from the database.

        Args:
            records (T | list[T]): The record or records to delete.

        Returns:
            Any: The number of affected rows for a single record or a list of
                affected rows for a list of records.
        """
        ...
