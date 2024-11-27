from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from typing import Any, AsyncIterator, Iterator, NotRequired, TypedDict, cast

from psycopg import (
    # Async
    AsyncConnection as PgConnectionAsync,
    AsyncCursor as PgCursorAsync,
    AsyncTransaction,
    # Sync
    Connection as PgConnection,
    Cursor as PgCursor,
    Transaction,
)
from psycopg.rows import (
    DictRow as PgDictRow,
    dict_row as PgDictRowFactory,
)
from psycopg_pool import ConnectionPool, AsyncConnectionPool

from database_wrapper import DatabaseBackend

PgConnectionType = PgConnection[PgDictRow]
PgCursorType = PgCursor[PgDictRow]

PgConnectionTypeAsync = PgConnectionAsync[PgDictRow]
PgCursorTypeAsync = PgCursorAsync[PgDictRow]


class PgConfig(TypedDict):
    hostname: str
    port: NotRequired[int]
    username: str
    password: str
    database: str
    ssl: NotRequired[str]
    kwargs: NotRequired[dict[str, Any]]

    # Connection Pooling
    maxconnections: int
    pool_kwargs: NotRequired[dict[str, Any]]


class PgSQL(DatabaseBackend):
    """
    PostgreSQL database implementation.

    Instance is created without actually connecting to the database.
    When you are ready to connect, call open() method.

    Close is called automatically when class is destroyed.

    :param config: Configuration for PostgreSQL
    :type config: PgConfig

    Defaults:
        port = 5432
        ssl = prefer

    """

    config: PgConfig

    connection: PgConnectionType
    cursor: PgCursorType

    def open(self) -> None:
        # Free resources
        if hasattr(self, "connection") and self.connection:
            self.close()

        # Set defaults
        if "port" not in self.config or not self.config["port"]:
            self.config["port"] = 5432

        if "ssl" not in self.config or not self.config["ssl"]:
            self.config["ssl"] = "prefer"

        if "kwargs" not in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        if "autocommit" not in self.config["kwargs"]:
            self.config["kwargs"]["autocommit"] = True

        self.logger.debug("Connecting to DB")
        self.connection = cast(
            PgConnectionType,
            PgConnection.connect(
                host=self.config["hostname"],
                port=self.config["port"],
                sslmode=self.config["ssl"],
                user=self.config["username"],
                password=self.config["password"],
                dbname=self.config["database"],
                connect_timeout=self.connectionTimeout,
                row_factory=PgDictRowFactory,  # type: ignore
                **self.config["kwargs"],
            ),
        )
        self.cursor = self.connection.cursor(row_factory=PgDictRowFactory)

        # Lets do some socket magic
        self.fixSocketTimeouts(self.connection.fileno())

    ####################
    ### Transactions ###
    ####################

    @contextmanager
    def transaction(
        self,
        dbConn: PgConnectionType | None = None,
    ) -> Iterator[Transaction]:
        """Transaction context manager"""
        if dbConn:
            with dbConn.transaction() as trans:
                yield trans

        assert self.connection, "Connection is not initialized"
        with self.connection.transaction() as trans:
            yield trans

    ############
    ### Data ###
    ############

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


class PgSQLAsync(DatabaseBackend):
    """
    PostgreSQL database async implementation.

    Instance is created without actually connecting to the database.
    When you are ready to connect, call await open() method.

    ! Note: Close is not called automatically when class is destroyed.
    ! You need to call it manually in async environment.

    :param config: Configuration for PostgreSQL
    :type config: PgConfig

    Defaults:
        port = 5432
        ssl = prefer

    """

    config: PgConfig

    connection: PgConnectionTypeAsync
    cursor: PgCursorTypeAsync

    def __del__(self) -> None:
        """Destructor"""

        # Just to be sure as async does not have __del__
        del self.cursor
        del self.connection

    async def open(self) -> None:
        # Free resources
        if hasattr(self, "connection") and self.connection:
            await self.close()

        # Set defaults
        if "port" not in self.config or not self.config["port"]:
            self.config["port"] = 5432

        if "ssl" not in self.config or not self.config["ssl"]:
            self.config["ssl"] = "prefer"

        if "kwargs" not in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        if "autocommit" not in self.config["kwargs"]:
            self.config["kwargs"]["autocommit"] = True

        self.logger.debug("Connecting to DB")
        self.connection = await PgConnectionAsync.connect(
            host=self.config["hostname"],
            port=self.config["port"],
            sslmode=self.config["ssl"],
            user=self.config["username"],
            password=self.config["password"],
            dbname=self.config["database"],
            connect_timeout=self.connectionTimeout,
            row_factory=PgDictRowFactory,  # type: ignore
            **self.config["kwargs"],
        )
        self.cursor = self.connection.cursor(row_factory=PgDictRowFactory)

        # Lets do some socket magic
        self.fixSocketTimeouts(self.connection.fileno())

    async def close(self) -> Any:
        """Close connections"""
        if self.cursor:
            self.logger.debug("Closing cursor")
            await self.cursor.close()

        if self.connection:
            self.logger.debug("Closing connection")
            await self.connection.close()

    ####################
    ### Transactions ###
    ####################

    @asynccontextmanager
    async def transaction(
        self,
        dbConn: PgConnectionTypeAsync | None = None,
    ) -> AsyncIterator[AsyncTransaction]:
        """Transaction context manager"""
        if dbConn:
            async with dbConn.transaction() as trans:
                yield trans

        assert self.connection, "Connection is not initialized"
        async with self.connection.transaction() as trans:
            yield trans

    ############
    ### Data ###
    ############

    def affectedRows(self) -> int:
        assert self.cursor, "Cursor is not initialized"

        return self.cursor.rowcount

    async def commit(self) -> None:
        """Commit DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug(f"Commit DB queries")
        await self.connection.commit()

    async def rollback(self) -> None:
        """Rollback DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug(f"Rollback DB queries")
        await self.connection.rollback()


class PgSQLWithPooling(DatabaseBackend):
    """
    PostgreSQL database implementation with connection pooling.

    Instance is created without actually connecting to the database.
    When you are ready to connect, call openPool() method.

    Then you can use newConnection() to get connection from the pool and
    returnConnection() to return it back.
    Or use context manager to get connection and return it back automatically,
    for example:

        pool = PgSQLWithPooling(config)
        pool.openPool()
        with pool as (connection, cursor):
            cursor.execute("SELECT 1")

    :param config: Configuration for PostgreSQL
    :type config: PgConfig
    :param connectionTimeout: Connection timeout
    :type connectionTimeout: int
    :param instanceName: Name of the instance
    :type instanceName: str

    Defaults:
        port = 5432
        ssl = prefer
        maxconnections = 5
    """

    config: PgConfig
    """ Configuration """

    pool: ConnectionPool[PgConnectionType]
    """ Connection pool """

    connection: PgConnectionType | None
    """ Connection to database """

    cursor: PgCursorType | None
    """ Cursor to database """

    contextConnection: ContextVar[tuple[PgConnectionType, PgCursorType] | None]
    """ Connection used in context manager """

    ########################
    ### Class Life Cycle ###
    ########################

    def __init__(
        self,
        dbConfig: PgConfig,
        connectionTimeout: int = 5,
        instanceName: str = "postgresql_pool",
    ) -> None:
        """
        Main concept here is that in init we do not connect to database,
        so that class instances can be safely made regardless of connection statuss.

        Remember to call openPool() after creating instance to actually open the pool to the database
        and also closePool() to close the pool.
        """

        super().__init__(dbConfig, connectionTimeout, instanceName)

        # Set defaults
        if not "port" in self.config or not self.config["port"]:
            self.config["port"] = 5432

        if not "ssl" in self.config or not self.config["ssl"]:
            self.config["ssl"] = "prefer"

        if not "kwargs" in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        if not "autocommit" in self.config["kwargs"]:
            self.config["kwargs"]["autocommit"] = True

        # Connection pooling defaults
        if not "maxconnections" in self.config or not self.config["maxconnections"]:
            self.config["maxconnections"] = 5

        if not "pool_kwargs" in self.config or not self.config["pool_kwargs"]:
            self.config["pool_kwargs"] = {}

        connStr = (
            f"postgresql://{self.config['username']}:{self.config['password']}@{self.config['hostname']}:{self.config['port']}"
            f"/{self.config['database']}?connect_timeout={self.connectionTimeout}&application_name={self.name}"
            f"&sslmode={self.config['ssl']}"
        )
        self.pool = ConnectionPool(
            connStr,
            open=False,
            min_size=2,
            max_size=self.config["maxconnections"],
            max_lifetime=20 * 60,
            max_idle=400,
            timeout=self.connectionTimeout,
            reconnect_timeout=0,
            num_workers=4,
            connection_class=PgConnectionType,
            kwargs=self.config["kwargs"],
            **self.config["pool_kwargs"],
        )

    ##################
    ### Connection ###
    ##################

    def openPool(self) -> None:
        self.pool.open(wait=True, timeout=self.connectionTimeout)

    def closePool(self) -> None:
        """Close Pool"""

        if self.shutdownRequested.is_set():
            return
        self.shutdownRequested.set()

        # Close pool
        self.logger.debug("Closing connection pool")
        self.close()
        if hasattr(self, "pool") and self.pool.closed is False:
            self.pool.close()

    def open(self) -> None:
        """Get connection from the pool and keep it in the class"""
        if self.connection:
            self.close()

        # Create new connection
        res = self.newConnection()
        if res:
            (self.connection, self.cursor) = res

    def newConnection(
        self,
    ) -> tuple[PgConnectionType, PgCursorType] | None:
        assert self.pool, "Pool is not initialized"

        # Log
        self.logger.debug("Getting connection from the pool")

        # Get connection from the pool
        tries = 0
        while not self.shutdownRequested.is_set():
            connection = None
            try:
                connection = self.pool.getconn(timeout=self.connectionTimeout)
                cursor = connection.cursor(row_factory=PgDictRowFactory)

                # Lets do some socket magic
                self.fixSocketTimeouts(connection.fileno())

                with connection.transaction():
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

                return (connection, cursor)

            except Exception as e:
                if connection:
                    connection.close()
                    self.pool.putconn(connection)

                self.logger.error(f"Error while getting connection from the pool: {e}")
                self.shutdownRequested.wait(self.slowDownTimeout)
                tries += 1
                if tries >= 3:
                    break
                continue

        return None

    def returnConnection(self, connection: PgConnectionType) -> None:
        """Return connection to the pool"""
        assert self.pool, "Pool is not initialized"

        # Log
        self.logger.debug("Putting connection back to the pool")

        # Put connection back to the pool
        self.pool.putconn(connection)

        # Debug
        self.logger.debug(self.pool.get_stats())

    ###############
    ### Context ###
    ###############

    def __enter__(
        self,
    ) -> tuple[PgConnectionType | None, PgCursorType | None]:
        """Context manager"""

        # Lets set the context var so that it is set even if we fail to get connection
        self.contextConnection.set(None)

        res = self.newConnection()
        if res:
            self.contextConnection.set(res)
            return res

        return (
            None,
            None,
        )

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager"""

        testData = self.contextConnection.get()
        if testData:
            self.returnConnection(testData[0])

        # Reset context
        self.contextConnection.set(None)

    ####################
    ### Transactions ###
    ####################

    @contextmanager
    def transaction(
        self,
        dbConn: PgConnectionType | None = None,
    ) -> Iterator[Transaction]:
        """Transaction context manager"""
        if dbConn:
            with dbConn.transaction() as trans:
                yield trans

        assert self.connection, "Connection is not initialized"
        with self.connection.transaction() as trans:
            yield trans

    ############
    ### Data ###
    ############

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


class PgSQLWithPoolingAsync(DatabaseBackend):
    """
    PostgreSQL database implementation with async connection pooling.

    Instance is created without actually connecting to the database.
    When you are ready to connect, call await openPool() method.

    Then you can use newConnection() to get connection from the pool and
    returnConnection() to return it back.

    Or use context manager to get connection and return it back automatically,
    for example:

        pool = PgSQLWithPoolingAsync(config)
        await pool.openPool()
        async with pool as (connection, cursor):
            await cursor.execute("SELECT 1")


    ! Note: Close is not called automatically when class is destroyed.
    ! You need to call `await closePool()` manually in async environment.

    :param config: Configuration for PostgreSQL
    :type config: PgConfig
    :param connectionTimeout: Connection timeout
    :type connectionTimeout: int
    :param instanceName: Name of the instance
    :type instanceName: str

    Defaults:
        port = 5432
        ssl = prefer
        maxconnections = 5
    """

    config: PgConfig
    """ Configuration """

    poolAsync: AsyncConnectionPool[PgConnectionTypeAsync]
    """ Connection pool """

    connection: PgConnectionTypeAsync | None
    """ Connection to database """

    cursor: PgCursorTypeAsync | None
    """ Cursor to database """

    contextConnectionAsync: ContextVar[
        tuple[PgConnectionTypeAsync, PgCursorTypeAsync] | None
    ]
    """ Connection used in async context manager """

    ########################
    ### Class Life Cycle ###
    ########################

    def __init__(
        self,
        dbConfig: PgConfig,
        connectionTimeout: int = 5,
        instanceName: str = "async_postgresql",
    ) -> None:
        """
        Main concept here is that in init we do not connect to database,
        so that class instances can be safely made regardless of connection statuss.

        Remember to call await openPool() after creating instance to actually open the pool to the database
        and also await closePool() to close the pool.
        """

        super().__init__(dbConfig, connectionTimeout, instanceName)

        # Set defaults
        if not "port" in self.config or not self.config["port"]:
            self.config["port"] = 5432

        if not "ssl" in self.config or not self.config["ssl"]:
            self.config["ssl"] = "prefer"

        if not "kwargs" in self.config or not self.config["kwargs"]:
            self.config["kwargs"] = {}

        if not "autocommit" in self.config["kwargs"]:
            self.config["kwargs"]["autocommit"] = True

        # Connection pooling defaults
        if not "maxconnections" in self.config or not self.config["maxconnections"]:
            self.config["maxconnections"] = 5

        if not "pool_kwargs" in self.config or not self.config["pool_kwargs"]:
            self.config["pool_kwargs"] = {}

        connStr = (
            f"postgresql://{self.config['username']}:{self.config['password']}@{self.config['hostname']}:{self.config['port']}"
            f"/{self.config['database']}?connect_timeout={self.connectionTimeout}&application_name={self.name}"
            f"&sslmode={self.config['ssl']}"
        )
        self.poolAsync = AsyncConnectionPool(
            connStr,
            open=False,
            min_size=2,
            max_size=self.config["maxconnections"],
            max_lifetime=20 * 60,
            max_idle=400,
            timeout=self.connectionTimeout,
            reconnect_timeout=0,
            num_workers=4,
            connection_class=PgConnectionTypeAsync,
            kwargs=self.config["kwargs"],
            **self.config["pool_kwargs"],
        )

    def __del__(self) -> None:
        """Destructor"""
        del self.cursor
        del self.connection
        del self.poolAsync

    ##################
    ### Connection ###
    ##################

    async def openPool(self) -> None:
        await self.poolAsync.open(wait=True, timeout=self.connectionTimeout)

    async def closePool(self) -> None:
        """Close Pool"""

        if self.shutdownRequested.is_set():
            return
        self.shutdownRequested.set()

        # Close async pool
        self.logger.debug("Closing connection pool")
        await self.close()
        if hasattr(self, "poolAsync") and self.poolAsync.closed is False:
            await self.poolAsync.close()

    async def open(self) -> None:
        """Get connection from the pool and keep it in the class"""
        if self.connection:
            await self.close()

        # Create new connection
        res = await self.newConnection()
        if res:
            (self.connection, self.cursor) = res

    async def close(self) -> None:
        """Close connection by returning it to the pool"""

        if self.cursor:
            self.logger.debug("Closing cursor")
            await self.cursor.close()
            self.cursor = None

        if self.connection:
            await self.returnConnection(self.connection)
            self.connection = None

    async def newConnection(
        self,
    ) -> tuple[PgConnectionTypeAsync, PgCursorTypeAsync] | None:
        assert self.poolAsync, "Async pool is not initialized"

        # Log
        self.logger.debug("Getting connection from the pool")

        # Get connection from the pool
        tries = 0
        while not self.shutdownRequested.is_set():
            connection = None
            try:
                connection = await self.poolAsync.getconn(
                    timeout=self.connectionTimeout
                )
                cursor = connection.cursor(row_factory=PgDictRowFactory)

                # Lets do some socket magic
                self.fixSocketTimeouts(connection.fileno())

                async with connection.transaction():
                    await cursor.execute("SELECT 1")
                    await cursor.fetchone()

                return (connection, cursor)

            except Exception as e:
                if connection:
                    await connection.close()
                    await self.poolAsync.putconn(connection)

                self.logger.error(f"Error while getting connection from the pool: {e}")
                self.shutdownRequested.wait(self.slowDownTimeout)
                tries += 1
                if tries >= 3:
                    break
                continue

        return None

    async def returnConnection(self, connection: PgConnectionTypeAsync) -> None:
        """Return connection to the pool"""
        assert self.poolAsync, "Async pool is not initialized"

        # Log
        self.logger.debug("Putting connection back to the pool")

        # Put connection back to the pool
        await self.poolAsync.putconn(connection)

        # Debug
        self.logger.debug(self.poolAsync.get_stats())

    ###############
    ### Context ###
    ###############

    async def __aenter__(
        self,
    ) -> tuple[PgConnectionTypeAsync | None, PgCursorTypeAsync | None]:
        """Context manager"""

        # Lets set the context var so that it is set even if we fail to get connection
        self.contextConnectionAsync.set(None)

        res = await self.newConnection()
        if res:
            self.contextConnectionAsync.set(res)
            return res

        return (
            None,
            None,
        )

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager"""

        testData = self.contextConnectionAsync.get()
        if testData:
            await self.returnConnection(testData[0])

        # Reset context
        self.contextConnectionAsync.set(None)

    ####################
    ### Transactions ###
    ####################

    @asynccontextmanager
    async def transaction(
        self,
        dbConn: PgConnectionTypeAsync | None = None,
    ) -> AsyncIterator[AsyncTransaction]:
        """Transaction context manager"""
        if dbConn:
            async with dbConn.transaction() as trans:
                yield trans

        assert self.connection, "Connection is not initialized"
        async with self.connection.transaction() as trans:
            yield trans

    ############
    ### Data ###
    ############

    def affectedRows(self) -> int:
        assert self.cursor, "Cursor is not initialized"

        return self.cursor.rowcount

    async def commit(self) -> None:
        """Commit DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug(f"Commit DB queries")
        await self.connection.commit()

    async def rollback(self) -> None:
        """Rollback DB queries"""
        assert self.connection, "Connection is not initialized"

        self.logger.debug(f"Rollback DB queries")
        await self.connection.rollback()
