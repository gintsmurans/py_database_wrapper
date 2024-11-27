import logging

from typing import Type, cast, Any

from .common import OrderByItem, NoParam, DataModelType


class DBWrapperMixin:
    """
    Mixin class for the DBWrapper class to provide methods that can be
    used by both sync and async versions of the DBWrapper class.

    :property dbCursor: Database cursor object.
    :property logger: Logger object
    """

    ###########################
    ### Instance properties ###
    ###########################

    dbCursor: Any
    """
    Database cursor object.
    """

    # logger
    logger: Any
    """Logger object"""

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    def __init__(
        self,
        dbCursor: Any = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (DatabaseBackend): The DatabaseBackend object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        self.dbCursor = dbCursor

        if logger is None:
            loggerName = f"{__name__}.{self.__class__.__name__}"
            self.logger = logging.getLogger(loggerName)
        else:
            self.logger = logger

    def __del__(self) -> None:
        """
        Deallocates the instance of the DBWrapper class.
        """
        self.logger.debug("Dealloc")

        # Force remove instances so that there are no circular references
        if hasattr(self, "dbCursor") and self.dbCursor:
            del self.dbCursor

    ###############
    ### Setters ###
    ###############

    def setDbCursor(self, dbCursor: Any) -> None:
        """
        Updates the database cursor object.

        Args:
            dbCursor (Any): The new database cursor object.
        """

        if dbCursor is None:
            del self.dbCursor
            return

        self.dbCursor = dbCursor

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

    def logQuery(self, cursor: Any, query: Any, params: tuple[Any, ...]) -> None:
        """
        Logs the given query and parameters.

        Args:
            cursor (Any): The database cursor.
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        logging.getLogger().debug(f"Query: {query} with params: {params}")

    def turnDataIntoModel(
        self,
        emptyDataClass: Type[DataModelType],
        dbData: dict[str, Any],
    ) -> DataModelType:
        """
        Turns the given data into a data model.
        By default we are pretty sure that there is no factory in the cursor,
        So we need to create a new instance of the data model and fill it with data

        Args:
            emptyDataClass (DataModelType): The data model to use.
            dbData (dict[str, Any]): The data to turn into a model.

        Returns:
            DataModelType: The data model filled with data.
        """

        result = emptyDataClass()
        result.fillDataFromDict(dbData)
        result.raw_data = dbData

        # If the id key is not "id", we set it manually so that its filled correctly
        if result.idKey != "id":
            result.id = dbData.get(result.idKey, None)

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

    def orderQuery(self, orderBy: OrderByItem | None = None) -> Any | None:
        """
        Creates a SQL query to order the results by the given column.

        Args:
            orderBy (OrderByItem | None, optional): The column to order the results by. Defaults to None.

        Returns:
            Any: The created SQL query object.
        """
        if orderBy is None:
            return None

        orderList = [
            f"{item[0]} {item[1] if len(item) > 1 and item[1] != None else 'ASC'}"
            for item in orderBy
        ]
        return "ORDER BY %s" % ", ".join(orderList)

    def limitQuery(self, offset: int = 0, limit: int = 100) -> Any | None:
        """
        Creates a SQL query to limit the number of results returned.

        Args:
            offset (int, optional): The number of results to skip. Defaults to 0.
            limit (int, optional): The maximum number of results to return. Defaults to 100.

        Returns:
            Any: The created SQL query object.
        """
        if limit == 0:
            return None

        return f"LIMIT {limit} OFFSET {offset}"

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
    ) -> tuple[Any, tuple[Any, ...]]:
        if filter is None or len(filter) == 0:
            return ("", tuple())

        raw = [self.formatFilter(key, filter[key]) for key in filter]
        _query = " AND ".join([tup[0] for tup in raw])
        _query = f"WHERE {_query}"
        _params = tuple([val for tup in raw for val in tup[1:] if val is not NoParam])

        return (_query, _params)

    def _formatFilterQuery(
        self,
        query: Any,
        qFilter: Any,
        order: Any,
        limit: Any,
    ) -> Any:
        if qFilter is None:
            qFilter = ""
        if order is None:
            order = ""
        if limit is None:
            limit = ""
        return f"{query} {qFilter} {order} {limit}"

    def _formatInsertQuery(
        self,
        tableIdentifier: Any,
        storeData: dict[str, Any],
        returnKey: Any,
    ) -> Any:
        keys = storeData.keys()
        values = list(storeData.values())

        columns = ", ".join(keys)
        valuesPlaceholder = ", ".join(["%s"] * len(values))
        return (
            f"INSERT INTO {tableIdentifier} "
            f"({columns}) "
            f"VALUES ({valuesPlaceholder}) "
            f"RETURNING {returnKey}"
        )

    def _formatUpdateQuery(
        self,
        tableIdentifier: Any,
        updateKey: Any,
        updateData: dict[str, Any],
    ) -> Any:
        keys = updateData.keys()
        set_clause = ", ".join(f"{key} = %s" for key in keys)
        return f"UPDATE {tableIdentifier} SET {set_clause} WHERE {updateKey} = %s"

    def _formatDeleteQuery(
        self,
        tableIdentifier: Any,
        deleteKey: Any,
    ) -> Any:
        return f"DELETE FROM {tableIdentifier} WHERE {deleteKey} = %s"
