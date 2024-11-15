import logging
from typing import Any

from database_wrapper import DBWrapper

from .connector import MySqlConnection, MySqlDictCursor


class DBWrapperMysql(DBWrapper):
    """Wrapper for MySQL database"""

    dbConn: MySqlConnection
    """ MySQL connection object """

    dbCursor: MySqlDictCursor
    """ MySQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbConn: MySqlConnection,
        dbCursor: MySqlDictCursor,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The MySQL connector.
            dbConn (MySqlConnection, optional): The MySQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbConn, dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbConn(self, dbConn: MySqlConnection | None) -> None:
        """
        Updates the database connection object.

        Args:
            dbConn (MySqlConnection | None): The new database connection object.
        """
        super().setDbConn(dbConn)

    ######################
    ### Helper methods ###
    ######################

    def logQuery(
        self,
        cursor: MySqlDictCursor,
        query: Any,
        params: tuple[Any, ...],
    ) -> None:
        """
        Logs the given query and parameters.

        Args:
            cursor (MySqlDictCursor): The cursor used to execute the query.
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        queryString = cursor.mogrify(query, params)
        logging.getLogger().debug(f"Query: {queryString}")

    #####################
    ### Query methods ###
    #####################

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str | None:
        if limit == 0:
            return None
        return f"LIMIT {offset},{limit}"
