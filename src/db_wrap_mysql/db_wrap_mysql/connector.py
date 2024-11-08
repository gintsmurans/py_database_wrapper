from typing import TypedDict

from MySQLdb.connections import Connection as MySqlConnection
from MySQLdb.cursors import DictCursor as MySqlDictCursor

from db_wrap import DatabaseBackend


class MyConfig(TypedDict):
    hostname: str
    port: int
    username: str
    password: str
    database: str


class MySQL(DatabaseBackend):
    """MySQL database implementation"""

    config: MyConfig

    connection: MySqlConnection
    cursor: MySqlDictCursor

    def open(self):
        # Free resources
        if hasattr(self, "connection") and self.connection:
            self.close()

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
            charset="utf8",
        )
        self.cursor = self.connection.cursor(MySqlDictCursor)

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
