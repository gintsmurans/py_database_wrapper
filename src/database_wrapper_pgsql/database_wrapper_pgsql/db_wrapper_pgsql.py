import logging
from typing import Any, overload

from psycopg import Cursor, sql
from psycopg.rows import class_row

from database_wrapper import DataModelType, DBWrapper

from .db_wrapper_pgsql_mixin import DBWrapperPgSQLMixin
from .connector import (
    # Sync
    PgConnectionType,
    PgCursorType,
    PgSQL,
)


class DBWrapperPgSQL(DBWrapperPgSQLMixin, DBWrapper):
    """
    Sync database wrapper for postgres
    """

    # Override db instance
    db: PgSQL
    """ PostgreSQL database connector """

    dbConn: PgConnectionType | None = None
    """ PostgreSQL connection object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        db: PgSQL | None = None,
        dbConn: PgConnectionType | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The PostgreSQL connector.
            dbConn (MySqlConnection, optional): The PostgreSQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db, dbConn, logger)

    ###############
    ### Setters ###
    ###############

    def updateDb(self, db: PgSQL) -> None:
        """
        Updates the database backend object.

        Args:
            db (DatabaseBackend): The new database backend object.
        """
        self.db = db

    def updateDbConn(self, dbConn: PgConnectionType) -> None:
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
    def createCursor(self) -> PgCursorType: ...

    @overload
    def createCursor(
        self,
        emptyDataClass: DataModelType,
    ) -> Cursor[DataModelType]: ...

    def createCursor(
        self,
        emptyDataClass: DataModelType | None = None,
    ) -> Cursor[DataModelType] | PgCursorType:
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
            self.dbConn = self.db.connection

        # Lets make sure we have a connection
        if self.dbConn is None:
            raise Exception("Failed to get connection")

        if emptyDataClass is None:
            return self.dbConn.cursor()

        return self.dbConn.cursor(row_factory=class_row(emptyDataClass.__class__))

    def logQuery(
        self,
        cursor: Cursor[Any],
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
