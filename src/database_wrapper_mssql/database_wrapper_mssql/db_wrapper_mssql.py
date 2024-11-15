import logging

from database_wrapper import DBWrapper

from .connector import MssqlConnection, MssqlCursor


class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    dbConn: MssqlConnection
    """ MsSQL connection object """

    dbCursor: MssqlCursor
    """ MsSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbConn: MssqlConnection,
        dbCursor: MssqlCursor,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MSSQL): The MSSQL connector.
            dbConn (MssqlConnection, optional): The MSSQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbConn, dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbConn(self, dbConn: MssqlConnection | None) -> None:
        """
        Updates the database connection object.

        Args:
            dbConn (MssqlConnection | None): The new database connection object.
        """
        super().setDbConn(dbConn)

    #####################
    ### Query methods ###
    #####################

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str | None:
        if limit == 0:
            return None
        return f"""
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
        """
