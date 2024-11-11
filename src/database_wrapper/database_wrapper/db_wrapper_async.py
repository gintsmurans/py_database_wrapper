from typing import AsyncGenerator, Any, overload

from .common import OrderByItem, DataModelType
from .db_data_model import DBDataModel
from .db_wrapper_mixin import DBWrapperMixin


class DBWrapperAsync(DBWrapperMixin):
    """
    Async Database wrapper class.

    Note: In async environment we cannot call close method from __del__ method.
        It means you will need to call close method manually from async context.
    """

    #######################
    ### Class lifecycle ###
    #######################

    async def close(self) -> None:
        """
        Async method for closing async resources.
        """
        raise NotImplementedError("Method not implemented")

    ######################
    ### Helper methods ###
    ######################

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
            The created cursor object.
        """
        assert self.db is not None, "Database connection is not set"
        return self.db.cursor

    #####################
    ### Query methods ###
    #####################

    # Action methods
    async def getOne(
        self,
        emptyDataClass: DataModelType,
        customQuery: Any = None,
    ) -> DataModelType | None:
        """
        Retrieves a single record from the database by class defined id.

        Args:
            emptyDataClass (DataModelType): The data model to use for the query.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            DataModelType | None: The result of the query.
        """
        # Query and filter
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

        _filter = f"WHERE {self.makeIdentifier(emptyDataClass.tableAlias, idKey)} = %s"
        _params = (idValue,)

        # Create a SQL object for the query and format it
        querySql = self._formatFilterQuery(_query, _filter, None, None)

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, _params)

        # Load data
        try:
            await newCursor.execute(querySql, _params)

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
        emptyDataClass: DataModelType,
        idKey: str,
        idValue: Any,
        customQuery: Any = None,
    ) -> DataModelType | None:
        """
        Retrieves a single record from the database using the given key.

        Args:
            emptyDataClass (DataModelType): The data model to use for the query.
            idKey (str): The name of the key to use for the query.
            idValue (Any): The value of the key to use for the query.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            DataModelType | None: The result of the query.
        """
        # Query and filter
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        _filter = f"WHERE {self.makeIdentifier(emptyDataClass.tableAlias, idKey)} = %s"
        _params = (idValue,)

        # Create a SQL object for the query and format it
        querySql = self._formatFilterQuery(_query, _filter, None, None)

        # Create a new cursor
        newCursor = await self.createCursor(emptyDataClass)

        # Log
        self.logQuery(newCursor, querySql, _params)

        # Load data
        try:
            await newCursor.execute(querySql, _params)

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
        emptyDataClass: DataModelType,
        idKey: str | None = None,
        idValue: Any | None = None,
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> AsyncGenerator[DataModelType, None]:
        """
        Retrieves all records from the database.

        Args:
            emptyDataClass (DataModelType): The data model to use for the query.
            idKey (str | None, optional): The name of the key to use for filtering. Defaults to None.
            idValue (Any | None, optional): The value of the key to use for filtering. Defaults to None.
            orderBy (OrderByItem | None, optional): The order by item to use for sorting. Defaults to None.
            offset (int, optional): The number of results to skip. Defaults to 0.
            limit (int, optional): The maximum number of results to return. Defaults to 100.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            AsyncGenerator[DataModelType, None]: The result of the query.
        """
        # Query and filter
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        _params: tuple[Any, ...] = ()
        _filter = None
        if idKey and idValue:
            _filter = (
                f"WHERE {self.makeIdentifier(emptyDataClass.tableAlias, idKey)} = %s"
            )
            _params = (idValue,)

        # Order and limit
        _order = self.orderQuery(orderBy)
        _limit = self.limitQuery(offset, limit)

        # Create a SQL object for the query and format it
        querySql = self._formatFilterQuery(_query, _filter, _order, _limit)

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

    async def getFiltered(
        self,
        emptyDataClass: DataModelType,
        filter: dict[str, Any],
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> AsyncGenerator[DataModelType, None]:
        # Query and filter
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        (_filter, _params) = self.createFilter(filter)

        # Order and limit
        _order = self.orderQuery(orderBy)
        _limit = self.limitQuery(offset, limit)

        # Create SQL query
        querySql = self._formatFilterQuery(_query, _filter, _order, _limit)

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
        values = list(storeData.values())
        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        returnKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        insertQuery = self._formatInsertQuery(tableIdentifier, storeData, returnKey)

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

    @overload
    async def store(self, records: DataModelType) -> tuple[int, int]:  # type: ignore
        ...

    @overload
    async def store(self, records: list[DataModelType]) -> list[tuple[int, int]]: ...

    async def store(
        self,
        records: DataModelType | list[DataModelType],
    ) -> tuple[int, int] | list[tuple[int, int]]:
        """
        Stores a record or a list of records in the database.

        Args:
            records (DataModelType | list[DataModelType]): The record or records to store.

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
        values = list(updateData.values())
        values.append(idValue)

        tableIdentifier = self.makeIdentifier(schemaName, tableName)
        updateKey = self.makeIdentifier(emptyDataClass.tableAlias, idKey)
        updateQuery = self._formatUpdateQuery(tableIdentifier, updateKey, updateData)

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

    @overload
    async def update(self, records: DataModelType) -> int:  # type: ignore
        ...

    @overload
    async def update(self, records: list[DataModelType]) -> list[int]: ...

    async def update(
        self, records: DataModelType | list[DataModelType]
    ) -> int | list[int]:
        """
        Updates a record or a list of records in the database.

        Args:
            records (DataModelType | list[DataModelType]): The record or records to update.

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
        delete_query = self._formatDeleteQuery(tableIdentifier, deleteKey)

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

    @overload
    async def delete(self, records: DataModelType) -> int:  # type: ignore
        ...

    @overload
    async def delete(self, records: list[DataModelType]) -> list[int]: ...

    async def delete(
        self, records: DataModelType | list[DataModelType]
    ) -> int | list[int]:
        """
        Deletes a record or a list of records from the database.

        Args:
            records (DataModelType | list[DataModelType]): The record or records to delete.

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
