from pymssql import (
    Connection as MssqlConnection,
    Cursor as MssqlCursor,
)

from db_wrapper import DBWrapper
from db_wrapper.db_data_model import DBDataModel


# TODO: Possibly don't need to override any methods here as base class is based on postgres
class DBWrapperMSSQL(DBWrapper):
    """Database wrapper for mssql database"""

    # Override db instance
    db: MssqlConnection

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str:
        return f"""
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
        """

    def createCursor(
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
        return self.db.cursor(as_dict=True)
