import logging
from typing import Any

from psycopg import Cursor, sql
from database_wrapper import DBWrapper

from .db_wrapper_pgsql_mixin import DBWrapperPgSQLMixin
from .connector import PgCursorType


class DBWrapperPgSQL(DBWrapperPgSQLMixin, DBWrapper):
    """
    Sync database wrapper for postgres
    """

    dbCursor: PgCursorType
    """ PostgreSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbCursor: PgCursorType | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            dbCursor (PgCursorType): The PostgreSQL database cursor object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbCursor(self, dbCursor: PgCursorType) -> None:
        """
        Updates the database cursor object.

        Args:
            dbCursor (PgCursorType): The new database cursor object.
        """
        super().setDbCursor(dbCursor)

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
        queryString = query.as_string(self.dbCursor)
        logging.getLogger().debug(f"Query: {queryString}")
