from typing import TypedDict

from pymssql import (
    connect as MssqlConnect,
    Connection as MssqlConnection,
    Cursor as MssqlCursor,
)

from db_wrap import DatabaseBackend


class MsConfig(TypedDict):
    hostname: str
    port: str | None
    username: str
    password: str
    database: str


class MSSQL(DatabaseBackend):
    """MSSQL database backend"""

    config: MsConfig

    connection: MssqlConnection
    cursor: MssqlCursor

    def open(self):
        self.logger.debug("Connecting to DB")

        # Set default port
        if "port" not in self.config or not self.config["port"]:
            self.config["port"] = "1433"

        self.connection = MssqlConnect(
            server=self.config["hostname"],
            user=self.config["username"],
            password=self.config["password"],
            database=self.config["database"],
            port=self.config["port"],
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
