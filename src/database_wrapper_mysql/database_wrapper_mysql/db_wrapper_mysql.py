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
    """ MySQL database connector """

    dbConn: MySqlConnection | None = None
    """ MySQL connection object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        db: MySQL | None = None,
        dbConn: MySqlConnection | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MySQL): The MySQL connector.
            dbConn (MySqlConnection, optional): The MySQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db, dbConn, logger)

    ###############
    ### Setters ###
    ###############

    def setDb(self, db: MySQL | None) -> None:
        """
        Updates the database backend object.

        Args:
            db (MySQL | None): The new database backend object.
        """
        super().setDb(db)

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

    def createCursor(self, emptyDataClass: Any | None = None) -> MySqlDictCursor:
        return self.db.connection.cursor(MySqlDictCursor)
