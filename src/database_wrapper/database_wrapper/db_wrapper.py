from typing import Generator, Any, overload

from .db_data_model import DBDataModel
from .db_wrapper_mixin import DBWrapperMixin
from .common import OrderByItem, DataModelType


class DBWrapper(DBWrapperMixin):
    """
    Database wrapper class.
    """

    #####################
    ### Query methods ###
    #####################

    # Action methods
    def getOne(
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
        # Figure out the id key and value
        idKey = emptyDataClass.idKey
        idValue = emptyDataClass.id
        if not idKey:
            raise ValueError("Id key is not set")
        if not idValue:
            raise ValueError("Id value is not set")

        # Get the record
        res = self.getAll(
            emptyDataClass, idKey, idValue, limit=1, customQuery=customQuery
        )
        for row in res:
            return row
        else:
            return None

    def getByKey(
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
        # Get the record
        res = self.getAll(
            emptyDataClass, idKey, idValue, limit=1, customQuery=customQuery
        )
        for row in res:
            return row
        else:
            return None

    def getAll(
        self,
        emptyDataClass: DataModelType,
        idKey: str | None = None,
        idValue: Any | None = None,
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> Generator[DataModelType, None, None]:
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
            Generator[DataModelType, None, None]: The result of the query.
        """
        # Query and filter
        _query = (
            customQuery
            or emptyDataClass.queryBase()
            or self.filterQuery(emptyDataClass.schemaName, emptyDataClass.tableName)
        )
        _params: tuple[Any, ...] = ()
        _filter = ""

        # TODO: Rewrite this so that filter method with loop is not used here
        if idKey and idValue:
            (_filter, _params) = self.createFilter({idKey: idValue})

        # Order and limit
        _order = self.orderQuery(orderBy)
        _limit = self.limitQuery(offset, limit)

        # Create a SQL object for the query and format it
        querySql = self._formatFilterQuery(_query, _filter, _order, _limit)

        # Log
        self.logQuery(self.dbCursor, querySql, _params)

        # Execute the query
        self.dbCursor.execute(querySql, _params)

        # Instead of fetchall(), we'll use a generator to yield results one by one
        while True:
            row = self.dbCursor.fetchone()
            if row is None:
                break

            yield self.turnDataIntoModel(emptyDataClass.__class__, row)

    def getFiltered(
        self,
        emptyDataClass: DataModelType,
        filter: dict[str, Any],
        orderBy: OrderByItem | None = None,
        offset: int = 0,
        limit: int = 100,
        customQuery: Any = None,
    ) -> Generator[DataModelType, None, None]:
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

        # Log
        self.logQuery(self.dbCursor, querySql, _params)

        # Execute the query
        self.dbCursor.execute(querySql, _params)

        # Instead of fetchall(), we'll use a generator to yield results one by one
        while True:
            row = self.dbCursor.fetchone()
            if row is None:
                break

            yield self.turnDataIntoModel(emptyDataClass.__class__, row)

    def _insert(
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

        # Log
        self.logQuery(self.dbCursor, insertQuery, tuple(values))

        # Insert
        self.dbCursor.execute(insertQuery, tuple(values))
        affectedRows = self.dbCursor.rowcount
        result = self.dbCursor.fetchone()

        return (
            result.id if result and hasattr(result, "id") else 0,
            affectedRows,
        )

    @overload
    def insert(self, records: DataModelType) -> tuple[int, int]:  # type: ignore
        ...

    @overload
    def insert(self, records: list[DataModelType]) -> list[tuple[int, int]]: ...

    def insert(
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

            res = self._insert(
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

    def _update(
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

        # Log
        self.logQuery(self.dbCursor, updateQuery, tuple(values))

        # Update
        self.dbCursor.execute(updateQuery, tuple(values))
        affectedRows = self.dbCursor.rowcount

        return affectedRows

    @overload
    def update(self, records: DataModelType) -> int:  # type: ignore
        ...

    @overload
    def update(self, records: list[DataModelType]) -> list[int]: ...

    def update(self, records: DataModelType | list[DataModelType]) -> int | list[int]:
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
                self._update(
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

    def updateData(
        self,
        record: DBDataModel,
        updateData: dict[str, Any],
        updateIdKey: str | None = None,
        updateIdValue: Any = None,
    ) -> int:
        updateIdKey = updateIdKey or record.idKey
        updateIdValue = updateIdValue or record.id
        status = self._update(
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

    def _delete(
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

        # Log
        self.logQuery(self.dbCursor, delete_query, (idValue,))

        # Delete
        self.dbCursor.execute(delete_query, (idValue,))
        affected_rows = self.dbCursor.rowcount

        return affected_rows

    @overload
    def delete(self, records: DataModelType) -> int:  # type: ignore
        ...

    @overload
    def delete(self, records: list[DataModelType]) -> list[int]: ...

    def delete(self, records: DataModelType | list[DataModelType]) -> int | list[int]:
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
                self._delete(
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
