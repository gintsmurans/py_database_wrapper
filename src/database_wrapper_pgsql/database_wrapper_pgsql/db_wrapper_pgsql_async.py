import logging
from typing import Any

from psycopg import sql
from database_wrapper import DBWrapperAsync

from .db_wrapper_pgsql_mixin import DBWrapperPgSQLMixin
from .connector import PgConnectionTypeAsync, PgCursorTypeAsync


class DBWrapperPgSQLAsync(DBWrapperPgSQLMixin, DBWrapperAsync):
    """
    Async database wrapper for postgres

    This is meant to be used in async environments.
    """

    dbConn: PgConnectionTypeAsync
    """ Async PostgreSQL connection object """

    dbCursor: PgCursorTypeAsync
    """ Async PostgreSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbConn: PgConnectionTypeAsync,
        dbCursor: PgCursorTypeAsync,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The PostgreSQL database connector.
            dbConn (MySqlConnection, optional): The PostgreSQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbConn, dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbConn(self, dbConn: PgConnectionTypeAsync | None) -> None:
        """
        Updates the database connection object.

        Args:
            dbConn (PgConnectionTypeAsync | None): The new database connection object.
        """
        super().setDbConn(dbConn)

    ######################
    ### Helper methods ###
    ######################

    def logQuery(
        self,
        cursor: PgCursorTypeAsync,
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
