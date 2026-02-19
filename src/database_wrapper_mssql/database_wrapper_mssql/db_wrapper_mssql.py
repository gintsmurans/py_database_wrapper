import logging
from typing import Any

from database_wrapper import DataModelType, DBWrapper

from .connector import MssqlCursor


class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    dbCursor: MssqlCursor | None
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

    def setDbCursor(self, dbCursor: MssqlCursor | None) -> None:
        """
        Updates the database cursor object.

        Args:
            dbCursor (MssqlCursor): The new database cursor object.
        """
        super().setDbCursor(dbCursor)

    #####################
    ### Query methods ###
    #####################

    def getByKey(
        self,
        emptyDataClass: DataModelType,
        idKey: str,
        idValue: Any,
        customQuery: Any = None,
    ) -> DataModelType | None:
        """
        Retrieves a single record from the database using the given key.

        Args:
            emptyDataClass (DataModelType): The data model to use for the query.
            idKey (str): The name of the key to use for the query.
            idValue (Any): The value of the key to use for the query.
            customQuery (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            DataModelType | None: The result of the query.
        """
        # Get the record
        res = self.getAll(
            emptyDataClass,
            idKey,
            idValue,
            # MSSQL needs to have order by if offset and limit are used
            orderBy=[(idKey, "ASC")],
            limit=1,
            customQuery=customQuery,
        )
        for row in res:
            return row
        else:
            return None

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str | None:
        if limit == 0:
            return None
        return f"""
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
        """
