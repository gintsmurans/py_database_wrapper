import unittest

from database_wrapper_sqlite import DBWrapperSqlite, Sqlite, SqliteConfig


class TestSqlite(unittest.TestCase):
    def test_connection_and_query(self):
        # SQLite should always work as it can be in-memory
        config: SqliteConfig = {"database": ":memory:", "timeout": 5.0}

        db = Sqlite(config)
        db.open()

        self.assertIsNotNone(db.connection)
        self.assertIsNotNone(db.cursor)

        # Test 1: Basic Select
        db.cursor.execute("SELECT 1 as val")
        row = db.cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["val"], 1)

        # Test 2: Wrapper Init
        wrapper = DBWrapperSqlite(db_cursor=db.cursor)
        self.assertIsInstance(wrapper, DBWrapperSqlite)

        # Test 3: Create Table and Insert
        db.cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        db.cursor.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        db.commit()

        last_id = db.last_insert_id()
        self.assertEqual(last_id, 1)

        # Test 4: Select with Dict check
        db.cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
        user = db.cursor.fetchone()
        self.assertIsInstance(user, dict)
        self.assertEqual(user["name"], "Alice")

        db.close()


if __name__ == "__main__":
    unittest.main()
