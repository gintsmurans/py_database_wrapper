from typing import Any

from MySQLdb import Connection as MySqlConnection
from MySQLdb.cursors import DictCursor as MySqlDictCursor

from db_wrapper import DBWrapper


class DBWrapperMysql(DBWrapper):
    """Base model for all RV4 models"""

    # Override db instance
    db: MySqlConnection

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
            query (Any): The query to log.
            params (tuple[Any, ...]): The parameters to log.
        """
        queryString = cursor.mogrify(query, params)
        self.logger.debug(f"Query: {queryString}")

    #####################
    ### Query methods ###
    #####################

    def limitQuery(self, offset: int = 0, limit: int = 100) -> str:
        return f"LIMIT {offset},{limit}"

    def createCursor(self, emptyDataClass: Any | None = None) -> MySqlDictCursor:
        return self.db.cursor(MySqlDictCursor)  # type: ignore
