# database_wrapper_mysql

_Part of the `database_wrapper` package._

This python package is a database wrapper for [MySQL](https://www.mysql.com/) and [MariaDB](https://mariadb.org/) database.

## Installation

```bash
pip install database_wrapper[mysql]
```

## Usage

```python
from database_wrapper_mysql import MySQL, DBWrapperMySQL

db = MySQL({
    "hostname": "localhost",
    "port": 3306,
    "username": "root",
    "password": "your_password",
    "database": "my_database"
})
db.open()
dbWrapper = DBWrapperMySQL(dbCursor=db.cursor)

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
