import logging

from typing import TypeVar, cast, Any, overload

from .db_backend import DatabaseBackend
from .db_data_model import DBDataModel
from .utils.return_model import ReturnModel


OrderByItem = list[tuple[str, str | None]]


class NoParam:
    pass


# Bound T to DBDataModel
T = TypeVar("T", bound=DBDataModel)


class DBWrapper:
    """
    Database wrapper class.
    """

    ###########################
    ### Instance properties ###
    ###########################

    # Db backend
    db: Any
    """Database backend object"""

    dbConn: Any
    """
    Database connection object.

    Its not always set. Currently is used as a placeholder for async connections.
    For sync connections db - DatabaseBackend.connection is used.
    """

    # logger
    logger: logging.Logger

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    def __init__(
        self,
        db: DatabaseBackend,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (DatabaseBackend): The DatabaseBackend object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        self.db = db
        self.dbConn = None

        if logger is None:
            loggerName = f"{__name__}.{self.__class__.__name__}"
            self.logger = logging.getLogger(loggerName)
        else:
            self.logger = logger

    def __del__(self):
        """
        Deallocates the instance of the DBWrapper class.
        """
        self.logger.debug("Dealloc")

        # Force remove instances so that there are no circular references
        if hasattr(self, "db") and self.db:
            self.db = None

        if hasattr(self, "dbConn") and self.dbConn:
            self.dbConn = None

    async def close(self) -> None:
        """
        Async method for closing async resources.
        """
        raise NotImplementedError("Method not implemented")

    ######################
    ### Helper methods ###
    ######################

    def makeIdentifier(self, schema: str | None, name: str) -> Any:
        """
        Creates a SQL identifier object from the given name.

        Args:
            name (str): The name to create the identifier from.

        Returns:
            str: The created SQL identifier object.
        """
        if schema:
            return f"{schema}.{name}"

        return name

    @overload
    async def createCursor(self) -> Any: ...

    @overload
    async def createCursor(self, emptyDataClass: DBDataModel) -> Any: ...

    async def createCursor(self, emptyDataClass: DBDataModel | None = None) -> Any:
        """
        Creates a new cursor object.

        Args:
            emptyDataClass (T | None, optional): The data model to use for the cursor. Defaults to None.

        Returns:
            AsyncCursor[DictRow] | AsyncCursor[T]: The created cursor object.
        """
        assert self.db is not None, "Database connection is not set"
        return self.db.cursor

    def logQuery(self, cursor: Any, query: Any, params: tuple[Any, ...]) -> None:
        """
        Logs the given query and parameters.

        Args:
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        self.logger.debug(f"Query: {query} with params: {params}")

    #####################
    ### Query methods ###
    #####################

    def filterQuery(self, schemaName: str | None, tableName: str) -> Any:
        """
        Creates a SQL query to filter data from the given table.

        Args:
            tableName (str): The name of the table to filter data from.

        Returns:
            Any: The created SQL query object.
        """
        fullTableName = self.makeIdentifier(schemaName, tableName)
        return f"SELECT * FROM {fullTableName}"

    def limitQuery(self, offset: int = 0, limit: int = 100) -> Any:
        """
        Creates a SQL query to limit the number of results returned.

        Args:
            offset (int, optional): The number of results to skip. Defaults to 0.
            limit (int, optional): The maximum number of results to return. Defaults to 100.

        Returns:
            Any: The created SQL query object.
        """
        return f"LIMIT {limit} OFFSET {offset}"

    # Action methods
    async def getOne(
        self,
        emptyDataClass: T,
        customQuery: Any = None,
    ) -> ReturnModel[T | None]:
        """
        Retrieves a single record from the database.

        Args:
            emptyDataClass (T): The data model to use for the query.

        Returns:
            ReturnModel[T | None]: The result of the query.
        """
        # Query
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        idKey = emptyDataClass.idKey
        idValue = emptyDataClass.id
        if not idKey:
            return ReturnModel(
                success=False, message="Id key is not provided", code=10000
            )
        if not idValue:
            return ReturnModel(
                success=False, message="Id value is not provided", code=10000
            )

        # Create a SQL object for the query and format it
        querySql = f"{_query} WHERE {self.makeIdentifier(emptyDataClass.tableAlias, idKey)} = %s"

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, (idValue,))

        # Load data
        await newCursor.execute(querySql, (idValue,))
        dbData = await newCursor.fetchone()
        if not dbData:
            return ReturnModel(success=False, message="Data not found", code=10001)

        return ReturnModel(success=True, result=dbData)

    async def getByKey(
        self,
        emptyDataClass: T,
        idKey: str,
        idValue: Any,
        customQuery: Any = None,
    ) -> ReturnModel[T | None]:
        """
        Retrieves a single record from the database using the given key.

        Args:
            emptyDataClass (T): The data model to use for the query.
            idKey (str): The name of the key to use for the query.
            idValue (Any): The value of the key to use for the query.

        Returns:
            ReturnModel[T | None]: The result of the query.
        """
        # Query
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )

        # Create a SQL object for the query and format it
        querySql = f"{_query} WHERE {self.makeIdentifier(emptyDataClass.tableAlias, idKey)} = %s"

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, (idValue,))

        # Load data
        await newCursor.execute(querySql, (idValue,))
        dbData = await newCursor.fetchone()
        if not dbData:
            return ReturnModel(success=False, message="Data not found", code=10001)

        return ReturnModel(success=True, result=dbData)

    async def getAll(
        self,
        emptyDataClass: T,
        idKey: str | None = None,
        idValue: Any | None = None,
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> ReturnModel[list[T] | None]:
        """
        Retrieves all records from the database.

        Args:
            emptyDataClass (T): The data model to use for the query.
            idKey (str | None, optional): The name of the key to use for filtering. Defaults to None.
            idValue (Any | None, optional): The value of the key to use for filtering. Defaults to None.
            orderBy (OrderByItem | None, optional): The order by item to use for sorting. Defaults to None.
            offset (int, optional): The number of results to skip. Defaults to 0.
            limit (int, optional): The maximum number of results to return. Defaults to 100.

        Returns:
            ReturnModel[list[T] | None]: The result of the query.
        """
        # Query
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        _params: tuple[Any, ...] = ()

        # Filter
        if idKey and idValue:
            _query = f"{_query} WHERE {self.makeIdentifier(emptyDataClass.tableAlias, idKey)} = %s"
            _params = (idValue,)

        # Limits
        _order = ""
        _limit = ""

        if orderBy:
            orderList = [
                f"{item[0]} {item[1] if len(item) > 1 and item[1] != None else 'ASC'}"
                for item in orderBy
            ]
            _order = "ORDER BY %s" % ", ".join(orderList)
        if offset or limit:
            _limit = f"{self.limitQuery(offset, limit)}"

        # Create a SQL object for the query and format it
        querySql = f"{_query} {_order} {_limit}"

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, _params)

        # Load data
        await newCursor.execute(querySql, _params)
        dbData = await newCursor.fetchall()
        if not dbData:
            return ReturnModel(success=False, message="Data not found", code=10001)

        return ReturnModel(success=True, result=dbData)

    def formatFilter(self, key: str, filter: Any) -> tuple[Any, ...]:
        if type(filter) is dict:
            if "$contains" in filter:
                return (
                    f"{key} LIKE %s",
                    f"%{filter['$contains']}%",
                )
            elif "$starts_with" in filter:
                return (f"{key} LIKE %s", f"{filter['$starts_with']}%")
            elif "$ends_with" in filter:
                return (f"{key} LIKE %s", f"%{filter['$ends_with']}")
            elif "$min" in filter and "$max" not in filter:
                return (f"{key} >= %s", filter["$min"])  # type: ignore
            elif "$max" in filter and "$min" not in filter:
                return (f"{key} <= %s", filter["$max"])  # type: ignore
            elif "$min" in filter and "$max" in filter:
                return (f"{key} BETWEEN %s AND %s", filter["$min"], filter["$max"])  # type: ignore
            elif "$in" in filter:
                inFilter1: list[Any] = cast(list[Any], filter["$in"])
                return (f"{key} IN (%s)" % ",".join(["%s"] * len(inFilter1)),) + tuple(
                    inFilter1
                )
            elif "$not_in" in filter:
                inFilter2: list[Any] = cast(list[Any], filter["$in"])
                return (
                    f"{key} NOT IN (%s)" % ",".join(["%s"] * len(inFilter2)),
                ) + tuple(inFilter2)
            elif "$not" in filter:
                return (f"{key} != %s", filter["$not"])  # type: ignore

            elif "$gt" in filter:
                return (f"{key} > %s", filter["$gt"])  # type: ignore
            elif "$gte" in filter:
                return (f"{key} >= %s", filter["$gte"])  # type: ignore
            elif "$lt" in filter:
                return (f"{key} < %s", filter["$lt"])  # type: ignore
            elif "$lte" in filter:
                return (f"{key} <= %s", filter["$lte"])  # type: ignore
            elif "$is_null" in filter:
                return (f"{key} IS NULL",)  # type: ignore
            elif "$is_not_null" in filter:
                return (f"{key} IS NOT NULL",)  # type: ignore

            raise NotImplementedError("Filter type not supported")
        elif type(filter) is str or type(filter) is int or type(filter) is float:
            return (f"{key} = %s", filter)
        elif type(filter) is bool:
            return (
                f"{key} = TRUE" if filter else f"{key} = FALSE",
                NoParam,
            )
        else:
            raise NotImplementedError(
                f"Filter type not supported: {key} = {type(filter)}"
            )

    def createFilter(
        self, filter: dict[str, Any] | None
    ) -> tuple[str, tuple[Any, ...]]:
        if filter is None or len(filter) == 0:
            return ("", tuple())

        raw = [self.formatFilter(key, filter[key]) for key in filter]
        _query = " AND ".join([tup[0] for tup in raw])
        _query = f"WHERE {_query}"
        _params = tuple([val for tup in raw for val in tup[1:] if val is not NoParam])

        return (_query, _params)

    async def getFiltered(
        self,
        emptyDataClass: T,
        filter: dict[str, Any],
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> ReturnModel[list[T] | None]:
        # Filter
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        (_filter, _params) = self.createFilter(filter)
        _filter = _filter

        # Limits
        _order = ""
        _limit = ""

        if orderBy:
            orderList = [
                f"{item[0]} {item[1] if len(item) > 1 and item[1] != None else 'ASC'}"
                for item in orderBy
            ]
            _order = "ORDER BY %s" % ", ".join(orderList)
        if offset or limit:
            _limit = f"{self.limitQuery(offset, limit)}"

        # Create a SQL object for the query and format it
        querySql = f"{_query} {_filter} {_order} {_limit}"

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, _params)

        # Load data
        await newCursor.execute(querySql, _params)
        dbData = await newCursor.fetchall()
        if not dbData:
            return ReturnModel(success=False, message="Data not found", code=10001)

        return ReturnModel(success=True, result=dbData)

    async def _store(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        storeData: dict[str, Any],
        idKey: str,
    ) -> ReturnModel[tuple[int, int]]:
        keys = storeData.keys()
        values = list(storeData.values())

        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        returnKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)

        columns = ", ".join(keys)
        valuesPlaceholder = ", ".join(["%s"] * len(values))
        insertQuery = (
            f"INSERT INTO {tableIdentifier} "
            f"({columns}) "
            f"VALUES ({valuesPlaceholder}) "
            f"RETURNING {returnKey}"
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, insertQuery, tuple(values))

        # Insert
        await newCursor.execute(insertQuery, tuple(values))
        affectedRows = newCursor.rowcount
        result = await newCursor.fetchone()

        return ReturnModel(
            success=True,
            result=(
                result.id if result and hasattr(result, "id") else 0,
                affectedRows,
            ),
        )

    @overload
    async def store(self, records: T) -> ReturnModel[tuple[int, int]]:  # type: ignore
        ...

    @overload
    async def store(self, records: list[T]) -> list[ReturnModel[tuple[int, int]]]: ...

    async def store(
        self, records: T | list[T]
    ) -> ReturnModel[tuple[int, int]] | list[ReturnModel[tuple[int, int]]]:
        status: list[ReturnModel[tuple[int, int]]] = []

        oneRecord = False
        if not isinstance(records, list):
            oneRecord = True
            records = [records]

        for row in records:
            storeIdKey = row.idKey
            storeData = row.storeData()
            if not storeIdKey or not storeData:
                continue

            res = await self._store(
                row,
                row.schemaName,
                row.tableName,
                storeData,
                storeIdKey,
            )
            if res.result:
                row.id = res.result[0]  # update the id of the row

            status.append(res)

        if len(status) == 0:
            return ReturnModel(success=False, message="No data to store", code=10002)

        if oneRecord:
            return status[0]

        return status

    async def _update(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        updateData: dict[str, Any],
        updateId: tuple[str, Any],
    ) -> ReturnModel[int]:
        """
        Updates a record in the database.

        Schema name and table name are parameters to allow for the updating of records in different tables.
        """
        (idKey, idValue) = updateId
        keys = updateData.keys()
        values = list(updateData.values())
        values.append(idValue)

        set_clause = ", ".join(f"{key} = %s" for key in keys)

        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        updateKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        updateQuery = (
            f"UPDATE {tableIdentifier} SET {set_clause} WHERE {updateKey} = %s"
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, updateQuery, tuple(values))

        # Update
        await newCursor.execute(updateQuery, tuple(values))
        affectedRows = newCursor.rowcount

        return ReturnModel(success=True, result=affectedRows)

    @overload
    async def update(self, records: T) -> ReturnModel[int]:  # type: ignore
        ...

    @overload
    async def update(self, records: list[T]) -> list[ReturnModel[int]]: ...

    async def update(
        self, records: T | list[T]
    ) -> ReturnModel[int] | list[ReturnModel[int]]:
        status: list[ReturnModel[int]] = []

        oneRecord = False
        if not isinstance(records, list):
            oneRecord = True
            records = [records]

        for row in records:
            updateData = row.updateData()
            updateIdKey = row.idKey
            updateIdValue = row.id
            if not updateData or not updateIdKey or not updateIdValue:
                continue

            status.append(
                await self._update(
                    row,
                    row.schemaName,
                    row.tableName,
                    updateData,
                    (
                        updateIdKey,
                        updateIdValue,
                    ),
                )
            )

        if len(status) == 0:
            return ReturnModel(success=False, message="No data to update", code=10002)

        if oneRecord:
            return status[0]

        return status

    async def updateData(
        self,
        record: DBDataModel,
        updateData: dict[str, Any],
        updateIdKey: str | None = None,
        updateIdValue: Any = None,
    ) -> ReturnModel[int]:
        updateIdKey = updateIdKey or record.idKey
        updateIdValue = updateIdValue or record.id
        status = await self._update(
            record,
            record.schemaName,
            record.tableName,
            updateData,
            (
                updateIdKey,
                updateIdValue,
            ),
        )

        return status

    async def _delete(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        deleteId: tuple[str, Any],
    ) -> ReturnModel[int]:
        """
        Deletes a record from the database.

        Schema name and table name are parameters to allow for the deletion of records from different tables.
        """
        (idKey, idValue) = deleteId

        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        deleteKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        delete_query = f"DELETE FROM {tableIdentifier} WHERE {deleteKey} = %s"

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, delete_query, (idValue,))

        # Delete
        await newCursor.execute(delete_query, (idValue,))
        affected_rows = newCursor.rowcount

        return ReturnModel(success=True, result=affected_rows)

    @overload
    async def delete(self, records: T) -> ReturnModel[int]:  # type: ignore
        ...

    @overload
    async def delete(self, records: list[T]) -> list[ReturnModel[int]]: ...

    async def delete(
        self, records: T | list[T]
    ) -> ReturnModel[int] | list[ReturnModel[int]]:
        status: list[ReturnModel[int]] = []

        oneRecord = False
        if not isinstance(records, list):
            oneRecord = True
            records = [records]

        for row in records:
            deleteIdKey = row.idKey
            deleteIdValue = row.id
            if not deleteIdKey or not deleteIdValue:
                continue

            status.append(
                await self._delete(
                    row,
                    row.schemaName,
                    row.tableName,
                    (
                        deleteIdKey,
                        deleteIdValue,
                    ),
                )
            )

        if len(status) == 0:
            return ReturnModel(success=False, message="No data to delete", code=10003)

        if oneRecord:
            return status[0]

        return status
