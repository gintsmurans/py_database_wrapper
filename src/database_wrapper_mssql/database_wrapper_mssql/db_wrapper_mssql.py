import logging
from typing import Any

from database_wrapper import DataModelType, DBWrapper

from .connector import MssqlTypedDictCursor


class DBWrapperMssql(DBWrapper):
    """Database wrapper for mssql database"""

    db_cursor: MssqlTypedDictCursor | None
    """ MsSQL cursor object """

    #######################
    ### Class lifecycle ###
    #######################

    # Meta methods
    # We are overriding the __init__ method for the type hinting
    def __init__(
        self,
        db_cursor: MssqlTypedDictCursor | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initializes a new instance of the DBWrapper class.

        Args:
            db_cursor (MssqlTypedDictCursor): The MsSQL database cursor object.
            logger (logging.Logger, optional): The logger object. Defaults to None.
        """
        super().__init__(db_cursor, logger)

    ###############
    ### Setters ###
    ###############

    def set_db_cursor(self, db_cursor: MssqlTypedDictCursor | None) -> None:
        """
        Updates the database cursor object.

        Args:
            db_cursor (MssqlTypedDictCursor): The new database cursor object.
        """
        super().set_db_cursor(db_cursor)

    #####################
    ### Query methods ###
    #####################

    def get_by_key(
        self,
        empty_data_class: DataModelType,
        id_key: str,
        id_value: Any,
        custom_query: Any = None,
    ) -> DataModelType | None:
        """
        Retrieves a single record from the database using the given key.

        Args:
            empty_data_class (DataModelType): The data model to use for the query.
            id_key (str): The name of the key to use for the query.
            id_value (Any): The value of the key to use for the query.
            custom_query (Any, optional): The custom query to use for the query. Defaults to None.

        Returns:
            DataModelType | None: The result of the query.
        """
        # Get the record
        res = self.get_all(
            empty_data_class,
            id_key,
            id_value,
            # MSSQL needs to have order by if offset and limit are used
            order_by=[(id_key, "ASC")],
            limit=1,
            custom_query=custom_query,
        )
        for row in res:
            return row
        else:
            return None

    def limit_query(self, offset: int = 0, limit: int = 100) -> str | None:
        if limit == 0:
            return None

        return f"""
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
        """
