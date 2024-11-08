import logging
from typing import Any, AsyncGenerator, overload

from psycopg import AsyncCursor, sql
from psycopg.rows import class_row

from database_wrapper import T, OrderByItem, DBWrapperAsync, DBDataModel

from .connector import (
    # Async
    PgAsyncConnectionType,
    PgAsyncCursorType,
    PgSQLWithPoolingAsync,
)


class DBWrapperPgSQLAsync(DBWrapperAsync):
    """
    Async database wrapper for postgres

    This is meant to be used in async environments.
    Also remember to call close() when done as we cannot do that in __del__.
    """

    # Override db instance
    db: PgSQLWithPoolingAsync
    dbConn: PgAsyncConnectionType | None = None

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    def __init__(
        self,
        db: PgSQLWithPoolingAsync,
        dbConn: PgAsyncConnectionType | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The MySQL object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db, dbConn, logger)

    async def close(self) -> None:
        if hasattr(self, "dbConn") and self.dbConn and hasattr(self, "db") and self.db:
            await self.db.returnConnection(self.dbConn)

        await super().close()

    ######################
    ### Helper methods ###
    ######################

    def makeIdentifier(self, schema: str | None, name: str) -> sql.Identifier | str:
        """
        Creates a SQL identifier object from the given name.

        Args:
            name (str): The name to create the identifier from.

        Returns:
            sql.Identifier: The created SQL identifier object.
        """
        if schema:
            return sql.Identifier(schema, name)

        return sql.Identifier(name)

    @overload
    async def createCursor(self) -> PgAsyncCursorType: ...

    @overload
    async def createCursor(
        self,
        emptyDataClass: T,
    ) -> AsyncCursor[T]: ...

    async def createCursor(
        self,
        emptyDataClass: T | None = None,
    ) -> AsyncCursor[T] | PgAsyncCursorType:
        """
        Creates a new cursor object.

        Args:
            emptyDataClass (DBDataModel | None, optional): The data model to use for the cursor.
                Defaults to None.

        Returns:
            PgAsyncCursorType | AsyncCursor[DBDataModel]: The created cursor object.
        """
        assert self.db is not None, "Database connection is not set"

        # First we need connection
        if self.dbConn is None:
            status = await self.db.newConnection()
            if not status:
                raise Exception("Failed to create new connection")

            (pgConn, _pgCur) = status
            self.dbConn = pgConn

        if emptyDataClass is None:
            return self.dbConn.cursor()

        return self.dbConn.cursor(row_factory=class_row(emptyDataClass.__class__))

    def logQuery(
        self,
        cursor: AsyncCursor[Any],
        query: sql.SQL | sql.Composed,
        params: tuple[Any, ...],
    ) -> None:
        """
        Logs the given query and parameters.

        Args:
            cursor (Any): The database cursor.
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        queryString = query.as_string(self.dbConn)
        self.logger.debug(f"Query: {queryString}")

    #####################
    ### Query methods ###
    #####################

    def filterQuery(
        self,
        schemaName: str | None,
        tableName: str,
    ) -> sql.SQL | sql.Composed | str:
        """
        Creates a SQL query to filter data from the given table.

        Args:
            schemaName (str): The name of the schema to filter data from.
            tableName (str): The name of the table to filter data from.

        Returns:
            sql.SQL | sql.Composed: The created SQL query object.
        """
        return sql.SQL("SELECT * FROM {table}").format(
            table=self.makeIdentifier(schemaName, tableName)
        )

    def limitQuery(self, offset: int = 0, limit: int = 100) -> sql.Composed | sql.SQL:
        return sql.SQL("LIMIT {} OFFSET {}").format(limit, offset)

    # Action methods
    async def getOne(
        self,
        emptyDataClass: T,
        customQuery: sql.SQL | sql.Composed | str | None = None,
    ) -> T | None:
        """
        Retrieves a single record from the database.

        Args:
            emptyDataClass (T): The data model to use for the query.
            customQuery (sql.SQL | sql.Composed | str | None, optional): The custom query to use.
                Defaults to None.

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
        querySql = sql.SQL("{query} WHERE {idkey} = %s").format(
            query=_query, idkey=self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, (idValue,))

        # Load data
        try:
            await newCursor.execute(querySql, (idValue,))
            dbData = await newCursor.fetchone()

            return dbData

        finally:
            # Close the cursor
            await newCursor.close()

    async def getByKey(
        self,
        emptyDataClass: T,
        idKey: str,
        idValue: Any,
        customQuery: sql.SQL | sql.Composed | str | None = None,
    ) -> T | None:
        """
        Retrieves a single record from the database using the given key.

        Args:
            emptyDataClass (T): The data model to use for the query.
            idKey (str): The name of the key to use for the query.
            idValue (Any): The value of the key to use for the query.
            customQuery (sql.SQL | sql.Composed | str | None, optional): The custom query to use.
                Defaults to None.

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
        querySql = sql.SQL("{} WHERE {} = %s").format(
            _query, self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, (idValue,))

        # Load data
        try:
            await newCursor.execute(querySql, (idValue,))
            dbData = await newCursor.fetchone()

            return dbData

        finally:
            # Ensure the cursor is closed after the generator is exhausted or an error occurs
            await newCursor.close()

    async def getAll(
        self,
        emptyDataClass: T,
        idKey: str | None = None,
        idValue: Any | None = None,
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: sql.SQL | sql.Composed | str | None = None,
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
            customQuery (sql.SQL | sql.Composed | str | None, optional): The custom query to use. Defaults to None.

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
            _query = sql.SQL("{} WHERE {} = %s").format(
                _query, self.makeIdentifier(emptyDataClass.tableAlias, idKey)
            )
            _params = (idValue,)

        # Limits
        _order: sql.Composable = sql.SQL("")
        _limit: sql.Composable = sql.SQL("")

        if orderBy:
            orderList = [
                f"{item[0]} {item[1] if len(item) > 1 and item[1] != None else 'ASC'}"
                for item in orderBy
            ]
            _order = sql.SQL("ORDER BY %s" % ", ".join(orderList))  # type: ignore
        if offset or limit:
            _limit = sql.SQL("{}").format(self.limitQuery(offset, limit))

        # Create a SQL object for the query and format it
        querySql = sql.SQL("{query} {order} {limit}").format(
            query=_query, order=_order, limit=_limit
        )

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
                yield row

        finally:
            # Ensure the cursor is closed after the generator is exhausted or an error occurs
            await newCursor.close()

    async def getFiltered(
        self,
        emptyDataClass: T,
        filter: dict[str, Any],
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: sql.SQL | sql.Composed | str | None = None,
    ) -> AsyncGenerator[T, None]:
        # Filter
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        (_filter, _params) = self.createFilter(filter)
        _filter = sql.SQL(_filter)  # type: ignore

        # Limits
        _order: sql.Composable = sql.SQL("")
        _limit: sql.Composable = sql.SQL("")

        if orderBy:
            orderList = [
                f"{item[0]} {item[1] if len(item) > 1 and item[1] != None else 'ASC'}"
                for item in orderBy
            ]
            _order = sql.SQL("ORDER BY %s" % ", ".join(orderList))  # type: ignore
        if offset or limit:
            _limit = sql.SQL("{}").format(self.limitQuery(offset, limit))

        # Create a SQL object for the query and format it
        querySql = sql.SQL("{query} {filter} {order} {limit}").format(
            query=_query, filter=_filter, order=_order, limit=_limit
        )

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
                yield row

        finally:
            # Close the cursor
            await newCursor.close()

    async def _store(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        storeData: dict[str, Any],
        idKey: str,
    ) -> tuple[int, int]:
        keys = storeData.keys()
        values = list(storeData.values())

        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        returnKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)

        insertQuery = sql.SQL(
            "INSERT INTO {table} ({columns}) VALUES ({values}) RETURNING {id_key}"
        ).format(
            table=tableIdentifier,
            columns=sql.SQL(", ").join(map(sql.Identifier, keys)),
            values=sql.SQL(", ").join(sql.Placeholder() * len(values)),
            id_key=returnKey,
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, insertQuery, tuple(values))

        # Insert
        try:
            await newCursor.execute(insertQuery, tuple(values))
            affectedRows = newCursor.rowcount
            result = await newCursor.fetchone()

            return (
                result.id if result and hasattr(result, "id") else 0,
                affectedRows,
            )

        finally:
            # Close the cursor
            await newCursor.close()

    async def _update(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        updateData: dict[str, Any],
        updateId: tuple[str, Any],
    ) -> int:
        (idKey, idValue) = updateId
        keys = updateData.keys()
        values = list(updateData.values())
        values.append(idValue)

        set_clause = sql.SQL(", ").join(
            sql.Identifier(key) + sql.SQL(" = %s") for key in keys
        )

        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        updateKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        updateQuery = sql.SQL(
            "UPDATE {table} SET {set_clause} WHERE {id_key} = %s"
        ).format(
            table=tableIdentifier,
            set_clause=set_clause,
            id_key=updateKey,
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, updateQuery, tuple(values))

        # Update
        try:
            await newCursor.execute(updateQuery, tuple(values))
            affectedRows = newCursor.rowcount

            return affectedRows

        finally:
            # Close the cursor
            await newCursor.close()

    async def _delete(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        deleteId: tuple[str, Any],
    ) -> int:
        (idKey, idValue) = deleteId

        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        deleteKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)

        delete_query = sql.SQL("DELETE FROM {table} WHERE {id_key} = %s").format(
            table=tableIdentifier, id_key=deleteKey
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, delete_query, (idValue,))

        # Delete
        try:
            await newCursor.execute(delete_query, (idValue,))
            affected_rows = newCursor.rowcount

            return affected_rows

        finally:
            # Close the cursor
            await newCursor.close()
