from typing import TypedDict

from pymssql import (
    connect as MssqlConnect,
    Connection as MssqlConnection,
    Cursor as MssqlCursor,
)

from db_wrapper import DatabaseBackend


class MsConfig(TypedDict):
    hostname: str
    port: int
    username: str
    password: str
    database: str


class MSSQL(DatabaseBackend):
    """MSSQL database backend"""

    config: MsConfig

    connection: MssqlConnection
    cursor: MssqlCursor

    def connect(self):
        self.logger.debug("Connecting to DB")
        self.connection = MssqlConnect(
            self.config["hostname"],
            self.config["username"],
            self.config["password"],
            self.config["database"],
            tds_version="7.0",
            timeout=self.connectionTimeout,
            login_timeout=self.connectionTimeout,
        )
        self.cursor = self.connection.cursor(as_dict=True)

    def lastInsertId(self) -> int:
        assert self.cursor, "Cursor is not initialized"
        return self.cursor.lastrowid

    def affectedRows(self) -> int:
        assert self.cursor, "Cursor is not initialized"
        return self.cursor.rowcount

    def commit(self) -> None:
        """Commit DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug(f"Commit DB queries")
        self.connection.commit()

    def rollback(self) -> None:
        """Rollback DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug(f"Rollback DB queries")
        self.connection.rollback()
