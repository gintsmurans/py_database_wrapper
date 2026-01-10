import os
import unittest

from database_wrapper_mssql import DBWrapperMssql, Mssql, MssqlConfig

MSSQL_CONFIG: MssqlConfig = {
    "hostname": "localhost",
    "port": "1433",
    "username": "sa",
    "password": "password",
    "database": "master",
}


class TestMssql(unittest.TestCase):
    def test_init(self):
        """Test basic initialization without connecting"""
        db = Mssql(MSSQL_CONFIG)
        self.assertIsInstance(db, Mssql)
        self.assertEqual(db.config["hostname"], "localhost")

    @unittest.skipUnless(
        os.environ.get("TEST_CONNECTIONS", "").lower() in ("1", "true", "yes"),
        "Skipping connection test. Set TEST_CONNECTIONS=1 to run.",
    )
    def test_connection_and_query(self):
        """Test actual connection and query execution"""
        try:
            db = Mssql(MSSQL_CONFIG)
            db.open()
            self.assertIsNotNone(db.connection)
            self.assertIsNotNone(db.cursor)

            db.cursor.execute("SELECT 1 as val")
            row = db.cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["val"], 1)

            wrapper = DBWrapperMssql(db_cursor=db.cursor)
            self.assertIsInstance(wrapper, DBWrapperMssql)

            db.close()
        except Exception as e:
            self.fail(f"MSSQL test failed with error: {e}")
