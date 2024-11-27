from typing import Any, NotRequired, TypedDict

from pymssql import (
    connect as MssqlConnect,
    Connection as MssqlConnection,
    Cursor as MssqlCursor,
)

from database_wrapper import DatabaseBackend


class MsConfig(TypedDict):
    hostname: str
    port: NotRequired[str]
    username: str
    password: str
    database: str
    tds_version: NotRequired[str]
    kwargs: NotRequired[dict[str, Any]]


class MSSQL(DatabaseBackend):
    """
    MSSQL database backend

    :param config: Configuration for MSSQL
    :type config: MsConfig

    Defaults:
        port = 1433
        tds_version = 7.0
    """

    config: MsConfig

    connection: MssqlConnection
    cursor: MssqlCursor

    def open(self) -> None:
        self.logger.debug("Connecting to DB")

        # Set defaults
        if "port" not in self.config or not self.config["port"]:
            self.config["port"] = "1433"

        if "tds_version" not in self.config or not self.config["tds_version"]:
            self.config["tds_version"] = "7.0"

        if "kwargs" not in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        self.connection = MssqlConnect(
            server=self.config["hostname"],
            user=self.config["username"],
            password=self.config["password"],
            database=self.config["database"],
            port=self.config["port"],
            tds_version="7.0",
            as_dict=True,
            timeout=self.connectionTimeout,
            login_timeout=self.connectionTimeout,
            **self.config["kwargs"],
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
