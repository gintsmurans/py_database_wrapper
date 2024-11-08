from typing import Any, overload

from psycopg import Cursor, AsyncCursor, sql
from psycopg.rows import class_row

from db_wrapper import T, OrderByItem, DBWrapper, DBDataModel
from db_wrapper.utils import ReturnModel

from .connector import (
    # Sync
    PgConnectionType,
    PgCursorType,
    PostgreSQL,
    # Async
    PgAsyncConnectionType,
    PgAsyncCursorType,
    AsyncPostgreSQLWithPooling,
)


class DBWrapperPostgres(DBWrapper):
    """
    Database wrapper for postgres

    This is meant to be used in async environments. Also remember to call close() when done.

    """

    # Override db instance
    db: PostgreSQL | AsyncPostgreSQLWithPooling
    dbConn: PgConnectionType | PgAsyncConnectionType | None = None

    #######################
    ### Class lifecycle ###
    #######################

    async def close(self) -> None:
        if hasattr(self, "dbConn") and self.dbConn and hasattr(self, "db") and self.db:
            if isinstance(self.db, AsyncPostgreSQLWithPooling):
                await self.db.returnConnection(self.dbConn)  # type: ignore
            self.dbConn = None

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
    async def createCursor(self) -> PgCursorType | PgAsyncCursorType: ...

    @overload
    async def createCursor(
        self,
        emptyDataClass: T,
    ) -> Cursor[T] | AsyncCursor[T]: ...

    async def createCursor(
        self,
        emptyDataClass: T | None = None,
    ) -> Cursor[T] | PgCursorType | AsyncCursor[T] | PgAsyncCursorType:
        """
        Creates a new cursor object.

        Args:
            emptyDataClass (DBDataModel | None, optional): The data model to use for the cursor. Defaults to None.

        Returns:
            PgAsyncCursorType | AsyncCursor[DBDataModel]: The created cursor object.
        """
        assert self.db is not None, "Database connection is not set"

        # First we need connection
        if self.dbConn is None:
            if isinstance(self.db, PostgreSQL):
                self.dbConn = self.db.connection

            if isinstance(self.db, AsyncPostgreSQLWithPooling):
                status = await self.db.newConnection()
                if not status:
                    raise Exception("Failed to create new connection")

                (pgConn, _pgCur) = status
                self.dbConn = pgConn

        # Lets make sure we have a connection
        if self.dbConn is None:
            raise Exception("Failed to get connection")

        if emptyDataClass is None:
            return self.dbConn.cursor()

        return self.dbConn.cursor(row_factory=class_row(emptyDataClass.__class__))

    def logQuery(
        self,
        cursor: AsyncCursor[Any] | Cursor[Any],
        query: sql.SQL | sql.Composed,
        params: tuple[Any, ...],
    ) -> None:
        """
        Logs the given query and parameters.

        Args:
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
        querySql = sql.SQL("{query} WHERE {idkey} = %s").format(
            query=_query, idkey=self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, (idValue,))

        # Load data
        if isinstance(newCursor, AsyncCursor):
            await newCursor.execute(querySql, (idValue,))
            dbData = await newCursor.fetchone()
        else:
            newCursor.execute(querySql, (idValue,))
            dbData = newCursor.fetchone()
        if not dbData:
            return ReturnModel(success=False, message="Data not found", code=10001)

        return ReturnModel(success=True, result=dbData)

    async def getByKey(
        self,
        emptyDataClass: T,
        idKey: str,
        idValue: Any,
        customQuery: sql.SQL | sql.Composed | str | None = None,
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
        querySql = sql.SQL("{} WHERE {} = %s").format(
            _query, self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        )

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, (idValue,))

        # Load data
        if isinstance(newCursor, AsyncCursor):
            await newCursor.execute(querySql, (idValue,))
            dbData = await newCursor.fetchone()
        else:
            newCursor.execute(querySql, (idValue,))
            dbData = newCursor.fetchone()
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
        customQuery: sql.SQL | sql.Composed | str | None = None,
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
        if isinstance(newCursor, AsyncCursor):
            await newCursor.execute(querySql, _params)
            dbData = await newCursor.fetchall()
        else:
            newCursor.execute(querySql, _params)
            dbData = newCursor.fetchall()
        if not dbData:
            return ReturnModel(success=False, message="Data not found", code=10001)

        return ReturnModel(success=True, result=dbData)

    async def getFiltered(
        self,
        emptyDataClass: T,
        filter: dict[str, Any],
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: sql.SQL | sql.Composed | str | None = None,
    ) -> ReturnModel[list[T] | None]:
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
        if isinstance(newCursor, AsyncCursor):
            await newCursor.execute(querySql, _params)
            dbData = await newCursor.fetchall()
        else:
            newCursor.execute(querySql, _params)
            dbData = newCursor.fetchall()
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
        if isinstance(newCursor, AsyncCursor):
            await newCursor.execute(insertQuery, tuple(values))
            affectedRows = newCursor.rowcount
            result = await newCursor.fetchone()
        else:
            newCursor.execute(insertQuery, tuple(values))
            affectedRows = newCursor.rowcount
            result = newCursor.fetchone()

        return ReturnModel(
            success=True,
            result=(
                result.id if result and hasattr(result, "id") else 0,
                affectedRows,
            ),
        )

    async def _update(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        updateData: dict[str, Any],
        updateId: tuple[str, Any],
    ) -> ReturnModel[int]:
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
        if isinstance(newCursor, AsyncCursor):
            await newCursor.execute(updateQuery, tuple(values))
        else:
            newCursor.execute(updateQuery, tuple(values))
        affectedRows = newCursor.rowcount

        return ReturnModel(success=True, result=affectedRows)

    async def _delete(
        self,
        emptyDataClass: DBDataModel,
        schemaName: str | None,
        tableName: str,
        deleteId: tuple[str, Any],
    ) -> ReturnModel[int]:
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
        if isinstance(newCursor, AsyncCursor):
            await newCursor.execute(delete_query, (idValue,))
        else:
            newCursor.execute(delete_query, (idValue,))
        affected_rows = newCursor.rowcount

        return ReturnModel(success=True, result=affected_rows)
