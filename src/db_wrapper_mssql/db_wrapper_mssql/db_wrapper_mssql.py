from pymssql import (
    Cursor as MssqlCursor,
)

from db_wrapper import DBWrapper
from db_wrapper.db_data_model import DBDataModel

from .connector import MSSQL


# TODO: Possibly don't need to override any methods here as base class is based on postgres
class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    # Override db instance
    db: MSSQL

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str:
        return f"""
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
        """

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
