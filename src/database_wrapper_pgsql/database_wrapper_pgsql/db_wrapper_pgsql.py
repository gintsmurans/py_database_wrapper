import logging
from typing import Any

from psycopg import Cursor, sql
from database_wrapper import DBWrapper

from .db_wrapper_pgsql_mixin import DBWrapperPgSQLMixin
from .connector import PgConnectionType, PgCursorType


class DBWrapperPgSQL(DBWrapperPgSQLMixin, DBWrapper):
    """
    Sync database wrapper for postgres
    """

    dbConn: PgConnectionType
    """ PostgreSQL connection object """

    dbCursor: PgCursorType
    """ PostgreSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbConn: PgConnectionType,
        dbCursor: PgCursorType,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The PostgreSQL connector.
            dbConn (MySqlConnection, optional): The PostgreSQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbConn, dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbConn(self, dbConn: PgConnectionType | None) -> None:
        """
        Updates the database connection object.

        Args:
            dbConn (PgConnectionType | None): The new database connection object.
        """
        super().setDbConn(dbConn)

    ######################
    ### Helper methods ###
    ######################

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
