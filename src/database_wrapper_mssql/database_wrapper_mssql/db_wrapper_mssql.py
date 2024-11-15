import logging
from pymssql import (
    Connection as MssqlConnection,
    Cursor as MssqlCursor,
)

from database_wrapper import DBWrapper, DBDataModel

from .connector import MSSQL


class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    # Override db instance
    db: MSSQL
    """ MSSQL database connector """

    dbConn: MssqlConnection | None = None
    """ MsSQL connection object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        db: MSSQL | None = None,
        dbConn: MssqlConnection | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MSSQL): The MSSQL connector.
            dbConn (MssqlConnection, optional): The MSSQL connection object. Defaults to None.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db, dbConn, logger)

    ###############
    ### Setters ###
    ###############

    def setDb(self, db: MSSQL | None) -> None:
        """
        Updates the database backend object.

        Args:
            db (MSSQL | None): The new database backend object.
        """
        super().setDb(db)

    def setDbConn(self, dbConn: MssqlConnection | None) -> None:
        """
        Updates the database connection object.

        Args:
            dbConn (MssqlConnection | None): The new database connection object.
        """
        super().setDbConn(dbConn)

    ######################
    ### Helper methods ###
    ######################

    def createCursor(
        self,
        emptyDataClass: DBDataModel | None = None,
    ) -> MssqlCursor:
        """
        Creates a new cursor object.

        Args:
            emptyDataClass (DBDataModel | None, optional): The data model to use for the cursor. Defaults to None.

        Returns:
            MssqlCursor: The created cursor object.
        """
        return self.db.connection.cursor(as_dict=True)

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
