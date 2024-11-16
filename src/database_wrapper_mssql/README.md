# database_wrapper_mssql

_Part of the `database_wrapper` package._

This python package is a database wrapper for [MSSQL](https://www.microsoft.com/en-us/sql-server/sql-server-downloads) database.

## Installation

```bash
pip install database_wrapper[mssql]
```

## Usage

```python
from database_wrapper_mssql import MSSQL, DBWrapperMSSQL

db = MSSQL({
    "hostname": "localhost",
    "port": "1433",
    "username": "sa",
    "password": "your_password",
    "database": "master"
})
db.open()
dbWrapper = DBWrapperMSSQL(dbCursor=db.cursor)

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
