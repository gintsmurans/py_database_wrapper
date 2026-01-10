import os
import unittest
from unittest import IsolatedAsyncioTestCase

from database_wrapper_redis import RedisDbAsync, RedisDefaultConfig

REDIS_CONFIG: RedisDefaultConfig = {
    "hostname": "localhost",
    "port": 6379,
    "username": "",
    "password": "",
    "database": 0,
    # 'ssl': False, 'maxconnections': 10
}


class TestRedisAsync(IsolatedAsyncioTestCase):
    def test_init(self):
        """Test basic initialization"""
        db = RedisDbAsync(config=REDIS_CONFIG)
        self.assertIsInstance(db, RedisDbAsync)

    @unittest.skipUnless(
        os.environ.get("TEST_CONNECTIONS", "").lower() in ("1", "true", "yes"),
        "Skipping connection test. Set TEST_CONNECTIONS=1 to run.",
    )
    async def test_connection(self):
        """Test actual connection"""
        try:
            db = RedisDbAsync(config=REDIS_CONFIG)
            await db.open()

            conn = await db.new_connection()
            self.assertIsNotNone(conn)
            await conn.close()
            await db.close()

        except Exception as e:
            self.fail(f"Redis test failed with error: {e}")
