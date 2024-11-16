# database_wrapper_sqlite

_Part of the `database_wrapper` package._

This python package is a database wrapper for [sqlite](https://www.sqlite.org/) database.

## !!! IMPORTANT !!!

This package is not yet implemented. The README is a placeholder for future implementation.

## Installation

```bash
pip install database_wrapper[sqlite]
```

## Usage

```python
from database_wrapper_sqlite import Sqlite, DBWrapperSqlite

db = Sqlite({
    "database": "my_database.db",
})
db.open()
dbWrapper = DBWrapperSqlite(dbCursor=db.cursor)

# Simple query
aModel = MyModel()
res = await dbWrapper.getByKey(
    aModel,
    "id",
    3005,
)
if res:
    print(f"getByKey: {res.toDict()}")
else:
    print("No results")

# Raw query
res = await dbWrapper.getAll(
    aModel,
    customQuery="""
        SELECT t1.*, t2.name AS other_name
        FROM my_table AS t1
        LEFT JOIN other_table AS t2 ON t1.other_id = t2.id
    """
)
async for record in res:
    print(f"getAll: {record.toDict()}")
else:
    print("No results")

db.close()
```
