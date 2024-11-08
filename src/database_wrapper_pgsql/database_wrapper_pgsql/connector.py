import asyncio
from contextvars import ContextVar
from typing import Any, TypedDict, cast

from psycopg import (
    # Async
    AsyncConnection as PgAsyncConnection,
    AsyncCursor as PgAsyncCursor,
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

PgAsyncConnectionType = PgAsyncConnection[PgDictRow]
PgAsyncCursorType = PgAsyncCursor[PgDictRow]


class PgConfig(TypedDict):
    hostname: str
    port: int
    username: str
    password: str
    database: str
    ssl: str
    maxconnections: int


class AsyncPostgreSQLWithPooling(DatabaseBackend):
    """PostgreSQL database implementation"""

    config: PgConfig

    asyncPool: AsyncConnectionPool[PgAsyncConnectionType]
    contextAsyncConnection: ContextVar[
        tuple[PgAsyncConnectionType, PgAsyncCursorType] | None
    ]

    def __init__(
        self,
        dbConfig: PgConfig,
        connectionTimeout: int = 5,
        instanceName: str = "async_postgresql",
    ) -> None:
        """
        Main concept here is that in init we do not connect to database,
        so that class instances can be safely made regardless of connection statuss.

        Remember to call open() after creating instance to actually open the pool to the database
        and also close() to close the pool.
        """

        super().__init__(dbConfig, connectionTimeout, instanceName)

        if not "port" in self.config:
            self.config["port"] = 5432

        connStr = (
            f"postgresql://{self.config['username']}:{self.config['password']}@{self.config['hostname']}:{self.config['port']}"
            f"/{self.config['database']}?connect_timeout={self.connectionTimeout}&application_name={self.name}"
            f"&sslmode={self.config.get('ssl', 'prefer')}"
        )
        self.asyncPool = AsyncConnectionPool(
            connStr,
            open=False,
            min_size=2,
            max_size=self.config.get("maxconnections", 5),
            max_lifetime=20 * 60,
            max_idle=400,
            timeout=self.connectionTimeout,
            reconnect_timeout=0,
            num_workers=4,
            connection_class=PgAsyncConnectionType,
            kwargs={
                "autocommit": True,
            },
        )

    async def openAsync(self) -> None:
        await self.asyncPool.open(wait=True, timeout=self.connectionTimeout)

    async def newConnection(
        self,
    ) -> tuple[PgAsyncConnectionType, PgAsyncCursorType] | None:
        timer = self.timer.get()
        assert self.asyncPool, "Async pool is not initialized"

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
                connection = await self.asyncPool.getconn(
                    timeout=self.connectionTimeout
                )
                cursor = connection.cursor(row_factory=PgDictRowFactory)

                # Lets do some socket magic
                self.fixSocketTimeouts(connection.fileno())

                async with timer.aenter(
                    "sql_conn.PostgreSQLWithPooling.__aenter__.ping"
                ):
                    async with connection.transaction():
                        await cursor.execute("SELECT 1")
                        await cursor.fetchone()

                return (connection, cursor)

            except Exception as e:
                if connection:
                    await connection.close()
                    await self.asyncPool.putconn(connection)

                self.logger.error(f"Error while getting connection from the pool: {e}")
                self.shutdownRequested.wait(self.slowDownTimeout)
                tries += 1
                if tries >= 3:
                    break
                continue

        return None

    async def returnConnection(self, connection: PgAsyncConnectionType) -> None:
        """Return connection to the pool"""
        timer = self.timer.get()
        assert self.asyncPool, "Async pool is not initialized"

        # Create dummy timer
        if timer is None:
            timer = Timer("db")

        # Log
        self.logger.debug("Putting connection back to the pool")

        # Put connection back to the pool
        await self.asyncPool.putconn(connection)

        # Debug
        self.logger.debug(self.asyncPool.get_stats())
        timer.printTimerStats()
        timer.resetTimers()

    async def __aenter__(
        self,
    ) -> tuple[PgAsyncConnectionType | None, PgAsyncCursorType | None]:
        """Context manager"""

        # Init timer
        timer = Timer("db")
        self.timer.set(timer)

        # Lets set the context var so that it is set even if we fail to get connection
        self.contextAsyncConnection.set(None)

        res = await self.newConnection()
        if res:
            self.contextAsyncConnection.set(res)
            return res

        return (
            None,
            None,
        )

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager"""

        testData = self.contextAsyncConnection.get()
        if testData:
            await self.returnConnection(testData[0])

        # Reset context
        self.contextAsyncConnection.set(None)
        self.timer.set(None)

    def close(self) -> None:
        """Close connections"""

        if self.shutdownRequested.is_set():
            return

        self.logger.debug("Closing connection pool")

        # Shutdown
        self.shutdownRequested.set()

        # Close async pool
        if hasattr(self, "asyncPool") and self.asyncPool.closed is False:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.asyncPool.close())
                else:
                    loop.run_until_complete(self.asyncPool.close())

            except RuntimeError as e:
                ...  # Ignore, as it is expected
            except Exception as e:
                self.logger.debug(f"Error while closing async pool: {e}", exc_info=True)


class PostgreSQL(DatabaseBackend):
    """PostgreSQL database implementation"""

    config: PgConfig

    connection: PgConnectionType | None
    cursor: PgCursorType | None

    def open(self):
        # Free resources
        if hasattr(self, "connection") and self.connection:
            self.close()

        self.logger.debug("Connecting to DB")
        self.connection = cast(
            PgConnectionType,
            PgConnect(
                host=self.config["hostname"],
                port=self.config["port"],
                sslmode=self.config.get("ssl", "prefer"),
                user=self.config["username"],
                password=self.config["password"],
                dbname=self.config["database"],
                connect_timeout=self.connectionTimeout,
                row_factory=PgDictRowFactory,  # type: ignore
            ),
        )
        self.cursor = self.connection.cursor(row_factory=PgDictRowFactory)

        # Lets do some socket magic
        self.fixSocketTimeouts(self.connection.fileno())

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
