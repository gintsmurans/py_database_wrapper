import logging
import socket

from typing import Any
from threading import Event
from contextvars import ContextVar


class DatabaseBackend:
    config: Any
    """ Database configuration """

    connectionTimeout: int
    """ Connection timeout """

    name: str
    """ Instance name """

    # TODO: This should be made to increase exponentially
    slowDownTimeout: int
    """ How long to wait before trying to reconnect """

    pool: Any
    """ Connection pool """

    poolAsync: Any
    """ Async connection pool """

    connection: Any
    """ Connection to database """

    cursor: Any
    """ Cursor to database """

    contextConnection: ContextVar[Any | None]
    """ Connection used in context manager """

    contextConnectionAsync: ContextVar[Any | None]
    """ Connection used in async context manager """

    loggerName: str
    """ Logger name """

    logger: logging.Logger
    """ Logger """

    shutdownRequested: Event
    """
    Event to signal shutdown
    Used to stop database pool from creating new connections
    """

    ########################
    ### Class Life Cycle ###
    ########################

    def __init__(
        self,
        dbConfig: Any,
        connectionTimeout: int = 5,
        instanceName: str = "database_backend",
        slowDownTimeout: int = 5,
    ) -> None:
        """
        Main concept here is that in init we do not connect to database,
        so that class instances can be safely made regardless of connection statuss.

        Remember to call open() or openPool() before using this class.
        Close will be called automatically when class is destroyed.

        Contexts are not implemented here, but in child classes should be used
        by using connection pooling.

        Async classes should be called manually and should override __del__ method,
        if not upon destroying the class, an error will be raised that method was not awaited.
        """

        self.config = dbConfig
        self.connectionTimeout = connectionTimeout
        self.name = instanceName
        self.slowDownTimeout = slowDownTimeout

        self.loggerName = f"{__name__}.{self.__class__.__name__}.{self.name}"
        self.logger = logging.getLogger(self.loggerName)

        self.pool = None
        self.poolAsync = None

        self.connection = None
        self.cursor = None
        self.shutdownRequested = Event()
        self.contextConnection = ContextVar(f"db_connection_{self.name}", default=None)
        self.contextConnectionAsync = ContextVar(
            f"db_connection_{self.name}_async", default=None
        )

    def __del__(self) -> None:
        """What to do when class is destroyed"""
        self.logger.debug("Dealloc")

        # Clean up connections
        self.close()
        self.closePool()

        # Clean just in case
        del self.connection
        del self.cursor

        del self.pool
        del self.poolAsync

    ###############
    ### Context ###
    ###############

    def __enter__(self) -> tuple[Any, Any]:
        """Context manager"""
        raise Exception("Not implemented")

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager"""
        raise Exception("Not implemented")

    async def __aenter__(self) -> tuple[Any, Any]:
        """Context manager"""
        raise Exception("Not implemented")

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager"""
        raise Exception("Not implemented")

    ##################
    ### Connection ###
    ##################

    def openPool(self) -> Any:
        """Open connection pool"""
        ...

    def closePool(self) -> Any:
        """Close connection pool"""
        ...

    def open(self) -> Any:
        """Connect to database"""
        ...

    def close(self) -> Any:
        """Close connections"""
        if self.cursor:
            self.logger.debug("Closing cursor")
            self.cursor.close()
            self.cursor = None

        if self.connection:
            self.logger.debug("Closing connection")
            self.connection.close()
            self.connection = None

    def newConnection(self) -> Any:
        """
        Create new connection

        Used for async context manager and async connection creation

        Returns:
            tuple[Any, Any] | None: Connection and cursor
        """
        raise Exception("Not implemented")

    def returnConnection(self, connection: Any) -> Any:
        """
        Return connection to pool

        Used for async context manager and async connections return.
        For example to return connection to a pool.

        Args:
            connection (Any): Connection to return to pool
        """
        raise Exception("Not implemented")

    ###############
    ### Helpers ###
    ###############

    def fixSocketTimeouts(self, fd: Any) -> None:
        # Lets do some socket magic
        s = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
        # Enable sending of keep-alive messages
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Time the connection needs to remain idle before start sending
        # keepalive probes
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, self.connectionTimeout)
        # Time between individual keepalive probes
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
        # The maximum number of keepalive probes should send before dropping
        # the connection
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        # To set timeout for an RTO you must set TCP_USER_TIMEOUT timeout
        # (in milliseconds) for socket.
        s.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_USER_TIMEOUT, self.connectionTimeout * 1000
        )

    ####################
    ### Transactions ###
    ####################

    def beginTransaction(self) -> Any:
        """Start transaction"""
        raise Exception("Not implemented")

    def commitTransaction(self) -> Any:
        """Commit transaction"""
        raise Exception("Not implemented")

    def rollbackTransaction(self) -> Any:
        """Rollback transaction"""
        raise Exception("Not implemented")

    # @contextmanager
    def transaction(self, dbConn: Any = None) -> Any:
        """
        Transaction context manager

        ! When overriding this method, remember to use context manager.
        ! Its not defined here, so that it can be used in both sync and async methods.
        """
        raise Exception("Not implemented")

    ############
    ### Data ###
    ############

    def lastInsertId(self) -> int:
        """Get last inserted row id generated by auto increment"""
        raise Exception("Not implemented")

    def affectedRows(self) -> int:
        """Get affected rows count"""
        raise Exception("Not implemented")

    def commit(self) -> Any:
        """Commit DB queries"""
        raise Exception("Not implemented")

    def rollback(self) -> Any:
        """Rollback DB queries"""
        raise Exception("Not implemented")
