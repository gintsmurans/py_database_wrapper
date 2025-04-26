import logging

from database_wrapper import DBWrapper

from .connector import MssqlCursor


class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    db_cursor: MssqlCursor | None
    """ MsSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        db_cursor: MssqlCursor | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db_cursor (MssqlCursor): The MsSQL database cursor object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db_cursor, logger)

    ###############
    ### Setters ###
    ###############

    def set_db_cursor(self, db_cursor: MssqlCursor | None) -> None:
        """
        Updates the database cursor object.

        Args:
            db_cursor (MssqlCursor): The new database cursor object.
        """
        super().set_db_cursor(db_cursor)

    #####################
    ### Query methods ###
    #####################

    def limit_query(self, offset: int = 0, limit: int = 100) -> str | None:
        if limit == 0:
            return None

        return f"""
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
        """
