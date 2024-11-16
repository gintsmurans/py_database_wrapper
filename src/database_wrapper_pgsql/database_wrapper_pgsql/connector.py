from contextvars import ContextVar
from typing import Any, NotRequired, TypedDict, cast

from psycopg import (
    # Async
    AsyncConnection as PgConnectionAsync,
    AsyncCursor as PgCursorAsync,
    # Sync
    Connection as PgConnection,
    Cursor as PgCursor,
    connect as PgConnect,
)
from psycopg.rows import (
    DictRow as PgDictRow,
    dict_row as PgDictRowFactory,
)
from psycopg_pool import AsyncConnectionPool

from database_wrapper import DatabaseBackend
from database_wrapper.utils.timer import Timer


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
    PostgreSQL database implementation

    :param config: Configuration for PostgreSQL
    :type config: PgConfig

    Defaults:
        port = 5432
        ssl = prefer

    """

    config: PgConfig

    connection: PgConnectionType | None
    cursor: PgCursorType | None

    def open(self):
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
            PgConnect(
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
    PostgreSQL database implementation with async and connection pooling

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
        timer = self.timer.get()
        assert self.poolAsync, "Async pool is not initialized"

        # Create dummy timer
        if timer is None:
            timer = Timer("db")
            self.timer.set(timer)

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

                async with timer.aenter("PgSQLWithPoolingAsync.__aenter__.ping"):
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
        timer = self.timer.get()
        assert self.poolAsync, "Async pool is not initialized"

        # Create dummy timer
        if timer is None:
            timer = Timer("db")

        # Log
        self.logger.debug("Putting connection back to the pool")

        # Put connection back to the pool
        await self.poolAsync.putconn(connection)

        # Debug
        self.logger.debug(self.poolAsync.get_stats())
        timer.printTimerStats()
        timer.resetTimers()

    ###############
    ### Context ###
    ###############

    async def __aenter__(
        self,
    ) -> tuple[PgConnectionTypeAsync | None, PgCursorTypeAsync | None]:
        """Context manager"""

        # Init timer
        timer = Timer("db")
        self.timer.set(timer)

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
        self.timer.set(None)

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
