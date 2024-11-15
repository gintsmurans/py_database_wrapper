import logging
from typing import Any, overload

from psycopg import AsyncCursor, sql
from psycopg.rows import class_row

from database_wrapper import DataModelType, DBWrapperAsync

from .db_wrapper_pgsql_mixin import DBWrapperPgSQLMixin
from .connector import (
    # Async
    PgAsyncConnectionType,
    PgAsyncCursorType,
    PgSQLWithPoolingAsync,
)


class DBWrapperPgSQLAsync(DBWrapperPgSQLMixin, DBWrapperAsync):
    """
    Async database wrapper for postgres

    This is meant to be used in async environments.
    Also remember to call close() when done as we cannot do that in __del__.
    """

    # Override db instance
    db: PgSQLWithPoolingAsync
    """ Async PostgreSQL database connector """

    dbConn: PgAsyncConnectionType | None = None
    """ Async PostgreSQL connection object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        db: PgSQLWithPoolingAsync | None = None,
        dbConn: PgAsyncConnectionType | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The PostgreSQL database connector.
            dbConn (MySqlConnection, optional): The PostgreSQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db, dbConn, logger)

    async def close(self) -> None:
        if hasattr(self, "dbConn") and self.dbConn and hasattr(self, "db") and self.db:
            await self.db.returnConnection(self.dbConn)

        await super().close()

    ###############
    ### Setters ###
    ###############

    def updateDb(self, db: PgSQLWithPoolingAsync) -> None:
        """
        Updates the database backend object.

        Args:
            db (DatabaseBackend): The new database backend object.
        """
        self.db = db

    def updateDbConn(self, dbConn: PgAsyncConnectionType) -> None:
        """
        Updates the database connection object.

        Args:
            dbConn (Any): The new database connection object.
        """
        self.dbConn = dbConn

    ######################
    ### Helper methods ###
    ######################

    @overload
    async def createCursor(self) -> PgAsyncCursorType: ...

    @overload
    async def createCursor(
        self,
        emptyDataClass: DataModelType,
    ) -> AsyncCursor[DataModelType]: ...

    async def createCursor(
        self,
        emptyDataClass: DataModelType | None = None,
    ) -> AsyncCursor[DataModelType] | PgAsyncCursorType:
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
        logging.getLogger().debug(f"Query: {queryString}")
