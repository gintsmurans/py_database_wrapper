import logging

from typing import AsyncGenerator, TypeVar, cast, Any, overload

from .db_backend import DatabaseBackend
from .db_data_model import DBDataModel

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
        dbConn: Any = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (DatabaseBackend): The DatabaseBackend object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        self.db = db
        self.dbConn = dbConn

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
            schema (str | None): The schema to create the identifier from.
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
            cursor (Any): The database cursor.
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        self.logger.debug(f"Query: {query} with params: {params}")

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

        result = emptyDataClass.__class__()
        result.fillDataFromDict(dbData)
        result.raw_data = dbData
        return result

    #####################
    ### Query methods ###
    #####################

    def filterQuery(self, schemaName: str | None, tableName: str) -> Any:
        """
        Creates a SQL query to filter data from the given table.

        Args:
            schemaName (str | None): The name of the schema to filter data from.
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
    ) -> T | None:
        """
        Retrieves a single record from the database.

        Args:
            emptyDataClass (T): The data model to use for the query.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            T | None: The result of the query.
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
            raise ValueError("Id key is not set")
        if not idValue:
            raise ValueError("Id value is not set")

        # Create a SQL object for the query and format it
        querySql = f"{_query} WHERE {self.makeIdentifier(emptyDataClass.tableAlias, idKey)} = %s"

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, (idValue,))

        # Load data
        try:
            newCursor.execute(querySql, (idValue,))

            # Fetch one row
            row = await newCursor.fetchone()
            if row is None:
                return

            # Turn data into model
            return self.turnDataIntoModel(emptyDataClass, row)
        finally:
            # Close the cursor
            await newCursor.close()

    async def getByKey(
        self,
        emptyDataClass: T,
        idKey: str,
        idValue: Any,
        customQuery: Any = None,
    ) -> T | None:
        """
        Retrieves a single record from the database using the given key.

        Args:
            emptyDataClass (T): The data model to use for the query.
            idKey (str): The name of the key to use for the query.
            idValue (Any): The value of the key to use for the query.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            T | None: The result of the query.
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
        try:
            newCursor.execute(querySql, (idValue,))

            # Fetch one row
            row = await newCursor.fetchone()
            if row is None:
                return

            # Turn data into model
            return self.turnDataIntoModel(emptyDataClass, row)

        finally:
            # Close the cursor
            await newCursor.close()

    async def getAll(
        self,
        emptyDataClass: T,
        idKey: str | None = None,
        idValue: Any | None = None,
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> AsyncGenerator[T, None]:
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
            AsyncGenerator[T, None]: The result of the query.
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
        try:
            # Execute the query
            await newCursor.execute(querySql, _params)

            # Instead of fetchall(), we'll use a generator to yield results one by one
            while True:
                row = await newCursor.fetchone()
                if row is None:
                    break
                yield self.turnDataIntoModel(emptyDataClass, row)

        finally:
            # Ensure the cursor is closed after the generator is exhausted or an error occurs
            await newCursor.close()

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
    ) -> AsyncGenerator[T, None]:
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
        try:
            # Execute the query
            await newCursor.execute(querySql, _params)

            # Instead of fetchall(), we'll use a generator to yield results one by one
            while True:
                row = await newCursor.fetchone()
                if row is None:
                    break
                yield self.turnDataIntoModel(emptyDataClass, row)

        finally:
            # Ensure the cursor is closed after the generator is exhausted or an error occurs
            await newCursor.close()

    async def _store(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        storeData: dict[str, Any],
        idKey: str,
    ) -> tuple[int, int]:
        """
        Stores a record in the database.

        Args:
            emptyDataClass (DBDataModel): The data model to use for the query.
            schemaName (str | None): The name of the schema to store the record in.
            tableName (str): The name of the table to store the record in.
            storeData (dict[str, Any]): The data to store.
            idKey (str): The name of the key to use for the query.

        Returns:
            tuple[int, int]: The id of the record and the number of affected rows.
        """
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
        try:
            newCursor.execute(insertQuery, tuple(values))
            affectedRows = newCursor.rowcount
            result = newCursor.fetchone()

            return (
                result.id if result and hasattr(result, "id") else 0,
                affectedRows,
            )

        finally:
            # Close the cursor
            await newCursor.close()

    @overload
    async def store(self, records: T) -> tuple[int, int]:  # type: ignore
        ...

    @overload
    async def store(self, records: list[T]) -> list[tuple[int, int]]: ...

    async def store(
        self, records: T | list[T]
    ) -> tuple[int, int] | list[tuple[int, int]]:
        """
        Stores a record or a list of records in the database.

        Args:
            records (T | list[T]): The record or records to store.

        Returns:
            tuple[int, int] | list[tuple[int, int]]: The id of the record and
                the number of affected rows for a single record or a list of
                ids and the number of affected rows for a list of records.
        """
        status: list[tuple[int, int]] = []

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
            if res:
                row.id = res[0]  # update the id of the row

            status.append(res)

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
    ) -> int:
        """
        Updates a record in the database.

        Args:
            emptyDataClass (DBDataModel): The data model to use for the query.
            schemaName (str | None): The name of the schema to update the record in.
            tableName (str): The name of the table to update the record in.
            updateData (dict[str, Any]): The data to update.
            updateId (tuple[str, Any]): The id of the record to update.

        Returns:
            int: The number of affected rows.
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
        try:
            newCursor.execute(updateQuery, tuple(values))
            affectedRows = newCursor.rowcount

            return affectedRows

        finally:
            # Close the cursor
            await newCursor.close()

    @overload
    async def update(self, records: T) -> int:  # type: ignore
        ...

    @overload
    async def update(self, records: list[T]) -> list[int]: ...

    async def update(self, records: T | list[T]) -> int | list[int]:
        """
        Updates a record or a list of records in the database.

        Args:
            records (T | list[T]): The record or records to update.

        Returns:
            int | list[int]: The number of affected rows for a single record or a list of
                affected rows for a list of records.
        """
        status: list[int] = []

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

        if oneRecord:
            return status[0]

        return status

    async def updateData(
        self,
        record: DBDataModel,
        updateData: dict[str, Any],
        updateIdKey: str | None = None,
        updateIdValue: Any = None,
    ) -> int:
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
    ) -> int:
        """
        Deletes a record from the database.

        Args:
            emptyDataClass (DBDataModel): The data model to use for the query.
            schemaName (str | None): The name of the schema to delete the record from.
            tableName (str): The name of the table to delete the record from.
            deleteId (tuple[str, Any]): The id of the record to delete.

        Returns:
            int: The number of affected rows.
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
        try:
            newCursor.execute(delete_query, (idValue,))
            affected_rows = newCursor.rowcount

            return affected_rows

        finally:
            # Close the cursor
            await newCursor.close()

    @overload
    async def delete(self, records: T) -> int:  # type: ignore
        ...

    @overload
    async def delete(self, records: list[T]) -> list[int]: ...

    async def delete(self, records: T | list[T]) -> int | list[int]:
        """
        Deletes a record or a list of records from the database.

        Args:
            records (T | list[T]): The record or records to delete.

        Returns:
            int | list[int]: The number of affected rows for a single record or a list of
                affected rows for a list of records.
        """
        status: list[int] = []

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

        if oneRecord:
            return status[0]

        return status
