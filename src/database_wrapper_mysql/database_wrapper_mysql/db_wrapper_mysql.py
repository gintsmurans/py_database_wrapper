import logging
from typing import Any

from database_wrapper import DBWrapper

from .connector import MySqlDictCursor


class DBWrapperMysql(DBWrapper):
    """Wrapper for MySQL database"""

    dbCursor: MySqlDictCursor
    """ MySQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbCursor: MySqlDictCursor | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            dbCursor (MySqlDictCursor): The MySQL database cursor object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbCursor(self, dbCursor: MySqlDictCursor) -> None:
        """
        Updates the database cursor object.

        Args:
            dbCursor (MySqlDictCursor): The new database cursor object.
        """
        super().setDbCursor(dbCursor)

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
