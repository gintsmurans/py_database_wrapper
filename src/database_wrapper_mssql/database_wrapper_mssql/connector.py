import os
import stat
from typing import Any, NotRequired, TypedDict, cast

from pymssql import Connection as MssqlConnection
from pymssql import Cursor as MssqlCursor
from pymssql import connect as MssqlConnect

from database_wrapper import DatabaseBackend


class MssqlConfig(TypedDict):
    hostname: str
    port: NotRequired[str]
    username: str
    password: str
    database: str
    tds_version: NotRequired[str]
    kwargs: NotRequired[dict[str, Any]]


class MssqlTypedDictCursor(MssqlCursor):
    def fetchone(self) -> dict[str, Any] | None:
        return super().fetchone()  # type: ignore

    def fetchall(self) -> list[dict[str, Any]]:
        return super().fetchall()  # type: ignore

    def __iter__(self) -> "MssqlTypedDictCursor":
        return self

    def __next__(self) -> dict[str, Any]:
        return super().__next__()  # type: ignore


class Mssql(DatabaseBackend):
    """
    Mssql database backend

    :param config: Configuration for Mssql
    :type config: MssqlConfig

    Defaults:
        port = 1433
        tds_version = 7.0
    """

    config: MssqlConfig

    connection: MssqlConnection
    cursor: MssqlTypedDictCursor

    # FDs created by the connection, used to detect leaks from pymssql/FreeTDS
    _connection_fds: set[int]

    ##################
    ### Connection ###
    ##################

    def _snapshot_fds(self) -> set[int]:
        """Snapshot current open file descriptors (Linux only)."""
        try:
            return set(int(fd) for fd in os.listdir("/proc/self/fd"))
        except OSError:
            return set()

    def open(self) -> None:
        # Free resources
        if hasattr(self, "connection") and self.connection:
            self.close()

        self.logger.debug("Connecting to DB")

        # Set defaults
        if "port" not in self.config or not self.config["port"]:
            self.config["port"] = "1433"

        if "tds_version" not in self.config or not self.config["tds_version"]:
            self.config["tds_version"] = "7.0"

        if "kwargs" not in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        fds_before = self._snapshot_fds()
        self.connection = MssqlConnect(
            server=self.config["hostname"],
            user=self.config["username"],
            password=self.config["password"],
            database=self.config["database"],
            port=self.config["port"],
            tds_version=self.config["tds_version"],
            as_dict=True,
            timeout=self.connection_timeout,
            login_timeout=self.connection_timeout,
            **self.config["kwargs"],
        )
        self._connection_fds = self._snapshot_fds() - fds_before
        self.cursor = cast(MssqlTypedDictCursor, self.connection.cursor(as_dict=True))

    def close(self) -> Any:
        """Close connections, force-closing any FDs leaked by pymssql/FreeTDS."""
        try:
            if self.cursor:
                self.logger.debug("Closing cursor")
                self.cursor.close()
        except Exception as e:
            self.logger.debug(f"Error while closing cursor: {e}")
        finally:
            self.cursor = None

        try:
            if self.connection:
                self.logger.debug("Closing connection")
                self.connection.close()
        except Exception as e:
            self.logger.debug(f"Error while closing connection: {e}")
        finally:
            self.connection = None

        # Workaround for pymssql/FreeTDS bug: dbclose() on a dead DBPROCESS
        # doesn't release the wakeup eventfd. Force-close any leaked FDs.
        # See: https://github.com/pymssql/pymssql/issues/1002
        if hasattr(self, "_connection_fds"):
            for fd in self._connection_fds:
                try:
                    fd_stat = os.fstat(fd)
                    if stat.S_ISSOCK(fd_stat.st_mode) or stat.S_ISFIFO(fd_stat.st_mode):
                        os.close(fd)
                        self.logger.warning(f"Force-closed leaked FD {fd} from pymssql")
                except OSError:
                    pass
            self._connection_fds = set()

    def ping(self) -> bool:
        try:
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
        except Exception as e:
            self.logger.debug(f"Error while pinging the database: {e}")
            return False

        return True

    ############
    ### Data ###
    ############

    def last_insert_id(self) -> int:
        assert self.cursor, "Cursor is not initialized"
        return self.cursor.lastrowid

    def affected_rows(self) -> int:
        assert self.cursor, "Cursor is not initialized"
        return self.cursor.rowcount

    def commit(self) -> None:
        """Commit DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug("Commit DB queries")
        self.connection.commit()

    def rollback(self) -> None:
        """Rollback DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug("Rollback DB queries")
        self.connection.rollback()
