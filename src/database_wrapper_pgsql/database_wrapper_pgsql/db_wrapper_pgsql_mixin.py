from typing import Any

from psycopg import sql
from database_wrapper import OrderByItem, NoParam


class DBWrapperPgSQLMixin:
    """
    Mixin for providing methods that can be used by both sync and async versions of the DBWrapperPgSQL class.
    """

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

    def orderQuery(
        self,
        orderBy: OrderByItem | None = None,
    ) -> sql.SQL | sql.Composed | None:
        """
        Creates a SQL query to order the results by the given column.

        Args:
            orderBy (OrderByItem | None, optional): The column to order the results by. Defaults to None.

        Returns:
            Any: The created SQL query object.

        TODO: Fix return type
        """
        if orderBy is None:
            return None

        orderList = [
            f"{item[0]} {item[1] if len(item) > 1 and item[1] != None else 'ASC'}"
            for item in orderBy
        ]
        return sql.SQL("ORDER BY %s" % ", ".join(orderList))  # type: ignore

    def limitQuery(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> sql.Composed | sql.SQL | None:
        if limit == 0:
            return None

        return sql.SQL("LIMIT {} OFFSET {}").format(limit, offset)

    def formatFilter(self, key: str, filter: Any) -> tuple[Any, ...]:
        # TODO: For now we assume that we have that method from DBWrapperMixin
        # TODO: Its 5am and I am tired, I will fix this later
        return super().formatFilter(key, filter)  # type: ignore

    def createFilter(
        self, filter: dict[str, Any] | None
    ) -> tuple[sql.Composed | None, tuple[Any, ...]]:
        if filter is None or len(filter) == 0:
            return (None, tuple())

        raw = [self.formatFilter(key, filter[key]) for key in filter]

        _queryItems = sql.SQL(" AND ").join([sql.SQL(tup[0]) for tup in raw])
        _query = sql.SQL("WHERE {queryItems}").format(queryItems=_queryItems)
        _params = tuple([val for tup in raw for val in tup[1:] if val is not NoParam])

        return (_query, _params)

    def _formatFilterQuery(
        self,
        query: sql.SQL | sql.Composed | str,
        qFilter: sql.SQL | sql.Composed | None,
        order: sql.SQL | sql.Composed | None,
        limit: sql.SQL | sql.Composed | None,
    ) -> sql.Composed:

        if isinstance(query, str):
            query = sql.SQL(query)  # type: ignore

        queryParts: list[sql.Composable] = [query]
        if qFilter is not None:
            # if isinstance(qFilter, str):
            #     qFilter = sql.SQL(qFilter)
            queryParts.append(qFilter)
        if order is not None:
            queryParts.append(order)
        if limit is not None:
            queryParts.append(limit)

        return sql.SQL(" ").join(queryParts)

    def _formatInsertQuery(
        self,
        tableIdentifier: sql.Identifier | str,
        storeData: dict[str, Any],
        returnKey: sql.Identifier | str,
    ) -> sql.Composed:
        keys = storeData.keys()
        values = list(storeData.values())

        return sql.SQL(
            "INSERT INTO {table} ({columns}) VALUES ({values}) RETURNING {id_key}"
        ).format(
            table=tableIdentifier,
            columns=sql.SQL(", ").join(map(sql.Identifier, keys)),
            values=sql.SQL(", ").join(sql.Placeholder() * len(values)),
            id_key=returnKey,
        )

    def _formatUpdateQuery(
        self,
        tableIdentifier: sql.Identifier | str,
        updateKey: sql.Identifier | str,
        updateData: dict[str, Any],
    ) -> sql.Composed:
        keys = updateData.keys()
        set_clause = sql.SQL(", ").join(
            sql.Identifier(key) + sql.SQL(" = %s") for key in keys
        )
        return sql.SQL("UPDATE {table} SET {set_clause} WHERE {id_key} = %s").format(
            table=tableIdentifier,
            set_clause=set_clause,
            id_key=updateKey,
        )

    def _formatDeleteQuery(
        self,
        tableIdentifier: sql.Identifier | str,
        deleteKey: sql.Identifier | str,
    ) -> sql.Composed:
        return sql.SQL("DELETE FROM {table} WHERE {id_key} = %s").format(
            table=tableIdentifier, id_key=deleteKey
        )
