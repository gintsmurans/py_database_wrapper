import logging
from pymssql import (
    Cursor as MssqlCursor,
)

from db_wrapper import DBWrapper, DBDataModel

from .connector import MSSQL


class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    # Override db instance
    db: MSSQL

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    def __init__(
        self,
        db: MSSQL,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db (MSSQL): The MSSQL object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db, logger)

    ######################
    ### Helper methods ###
    ######################

    async def createCursor(
        self,
        emptyDataClass: DBDataModel | None = None,
    ) -> MssqlCursor:
        """
        Creates a new cursor object.

        Args:
            emptyDataClass (DBDataModel | None, optional): The data model to use for the cursor. Defaults to None.

        Returns:
            PgAsyncCursorType | AsyncCursor[DBDataModel]: The created cursor object.
        """
        return self.db.connection.cursor(as_dict=True)

    #####################
    ### Query methods ###
    #####################

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str:
        return f"""
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
        """
