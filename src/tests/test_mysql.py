import os
import unittest

from database_wrapper_mysql import DBWrapperMysql, Mysql, MysqlConfig

MYSQL_CONFIG: MysqlConfig = {
    "hostname": "localhost",
    "port": 3306,
    "username": "root",
    "password": "password",
    "database": "mysql",
}


class TestMysql(unittest.TestCase):
    def test_init(self):
        """Test basic initialization without connecting"""
        db = Mysql(MYSQL_CONFIG)
        self.assertIsInstance(db, Mysql)
        self.assertEqual(db.config["hostname"], "localhost")

    @unittest.skipUnless(
        os.environ.get("TEST_CONNECTIONS", "").lower() in ("1", "true", "yes"),
        "Skipping connection test. Set TEST_CONNECTIONS=1 to run.",
    )
    def test_connection_and_query(self):
        """Test actual connection and query execution"""
        try:
            db = Mysql(MYSQL_CONFIG)
            db.open()
            self.assertIsNotNone(db.connection)
            self.assertIsNotNone(db.cursor)

            db.cursor.execute("SELECT 1 as val")
            row = db.cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["val"], 1)

            wrapper = DBWrapperMysql(db_cursor=db.cursor)
            self.assertIsInstance(wrapper, DBWrapperMysql)

            db.close()
        except Exception as e:
            self.fail(f"MySQL test failed with error: {e}")
