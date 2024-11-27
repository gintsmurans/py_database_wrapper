import logging
from typing import Any

from psycopg import sql
from database_wrapper import DBWrapperAsync

from .db_wrapper_pgsql_mixin import DBWrapperPgSQLMixin
from .connector import PgCursorTypeAsync


class DBWrapperPgSQLAsync(DBWrapperPgSQLMixin, DBWrapperAsync):
    """
    Async database wrapper for postgres

    This is meant to be used in async environments.
    """

    dbCursor: PgCursorTypeAsync
    """ Async PostgreSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbCursor: PgCursorTypeAsync | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            dbCursor (PgCursorTypeAsync): The PostgreSQL database cursor object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbCursor(self, dbCursor: PgCursorTypeAsync) -> None:
        """
        Updates the database cursor object.

        Args:
            dbCursor (PgCursorTypeAsync): The new database cursor object.
        """
        super().setDbCursor(dbCursor)

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
        queryString = query.as_string(self.dbCursor)
        logging.getLogger().debug(f"Query: {queryString}")
