import logging

from database_wrapper import DBWrapper

from .connector import MssqlCursor


class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    dbCursor: MssqlCursor
    """ MsSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        dbCursor: MssqlCursor | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            dbCursor (MssqlCursor): The MsSQL database cursor object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(dbCursor, logger)

    ###############
    ### Setters ###
    ###############

    def setDbCursor(self, dbCursor: MssqlCursor) -> None:
        """
        Updates the database cursor object.

        Args:
            dbCursor (MssqlCursor): The new database cursor object.
        """
        super().setDbCursor(dbCursor)

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
