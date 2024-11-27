from typing import Any, NotRequired, TypedDict

from database_wrapper import DatabaseBackend


class SqliteConfig(TypedDict):
    database: str
    kwargs: NotRequired[dict[str, Any]]


# TODO: Needs to finish the implementation
class Sqlite(DatabaseBackend):
    """
    Sqlite database backend

    :param config: Configuration for Sqlite
    :type config: MyConfig

    Defaults:
        _no defaults_
    """

    config: SqliteConfig

    connection: Any
    cursor: Any

    def open(self) -> None:
        # Free resources
        if hasattr(self, "connection") and self.connection:
            self.close()

        # Set defaults
        if "kwargs" not in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        self.logger.debug("Connecting to DB")

        raise NotImplementedError(
            "Sqlite is not yet implemented. See here: https://github.com/gintsmurans/py_database_wrapper/"
        )

    def lastInsertId(self) -> int:
        assert self.cursor, "Cursor is not initialized"
        return self.cursor.lastrowid

    def affectedRows(self) -> int:
        assert self.cursor, "Cursor is not initialized"
        return self.cursor.rowcount

    def commit(self) -> None:
        """Commit DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug("Commit DB queries..")
        self.connection.commit()

    def rollback(self) -> None:
        """Rollback DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug("Rollback DB queries..")
        self.connection.rollback()
