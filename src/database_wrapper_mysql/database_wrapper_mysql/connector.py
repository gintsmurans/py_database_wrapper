from typing import Any, NotRequired, TypedDict

from MySQLdb.connections import Connection as MySqlConnection
from MySQLdb.cursors import DictCursor as MySqlDictCursor

from database_wrapper import DatabaseBackend


class MyConfig(TypedDict):
    hostname: str
    port: NotRequired[int]
    username: str
    password: str
    database: str
    charset: NotRequired[str]
    collation: NotRequired[str]
    kwargs: NotRequired[dict[str, Any]]


class MySQL(DatabaseBackend):
    """
    MySQL database backend

    :param config: Configuration for MySQL
    :type config: MyConfig

    Defaults:
        port = 0 - See comment below
        charset = utf8
        collation = utf8_general_ci
    """

    config: MyConfig

    connection: MySqlConnection
    cursor: MySqlDictCursor

    def open(self) -> None:
        # Free resources
        if hasattr(self, "connection") and self.connection:
            self.close()

        # Set defaults
        if "port" not in self.config or not self.config["port"]:
            self.config["port"] = 0

        if "charset" not in self.config or not self.config["charset"]:
            self.config["charset"] = "utf8"

        if "collation" not in self.config or not self.config["collation"]:
            self.config["collation"] = "utf8_general_ci"

        if "kwargs" not in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        self.logger.debug("Connecting to DB")
        self.connection = MySqlConnection(
            host=self.config["hostname"],
            user=self.config["username"],
            passwd=self.config["password"],
            db=self.config["database"],
            # By default, when port is not specified, Python library passes 0 to
            # MySQL C API function mysql_real_connect as port number.
            #
            # At https://dev.mysql.com/doc/c-api/8.0/en/mysql-real-connect.html
            # is written "If port is not 0, the value is used as the port number
            # for the TCP/IP connection."
            #
            # We keep the same behavior not to break services that have port
            # number unspecified.
            port=self.config.get("port", 0),
            connect_timeout=self.connectionTimeout,
            use_unicode=True,
            charset=self.config["charset"],
            collation=self.config["collation"],
            cursorclass=MySqlDictCursor,
            **self.config["kwargs"],
        )
        # TODO: Typings issue
        self.cursor = self.connection.cursor(MySqlDictCursor)  # type: ignore

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
        # TODO: Typings issue
        self.connection.commit()  # type: ignore

    def rollback(self) -> None:
        """Rollback DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug("Rollback DB queries..")
        # TODO: Typings issue
        self.connection.rollback()  # type: ignore
