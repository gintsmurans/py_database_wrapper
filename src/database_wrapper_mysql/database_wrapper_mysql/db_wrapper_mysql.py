import logging
from typing import Any

from MySQLdb.connections import Connection as MySqlConnection
from MySQLdb.cursors import DictCursor as MySqlDictCursor

from database_wrapper import DBWrapper

from .connector import MySQL


class DBWrapperMysql(DBWrapper):
    """Base model for all RV4 models"""

    # Override db instance
    db: MySQL

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    def __init__(
        self,
        db: MySQL,
        dbConn: MySqlConnection | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The MySQL object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db, dbConn, logger)

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
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        queryString = cursor.mogrify(query, params)
        self.logger.debug(f"Query: {queryString}")

    #####################
    ### Query methods ###
    #####################

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str:
        return f"LIMIT {offset},{limit}"

    def createCursor(self, emptyDataClass: Any | None = None) -> MySqlDictCursor:
        return self.db.connection.cursor(MySqlDictCursor)
