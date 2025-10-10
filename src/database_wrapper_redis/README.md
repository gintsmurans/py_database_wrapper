# database_wrapper_redis

_Part of the `database_wrapper` package._

This python package is a database wrapper for [Redis](https://redis.io/).

## Installation

```bash
pip install database_wrapper[redis]
```

## Usage

```python
from database_wrapper_redis import RedisDBWithPoolAsync, RedisDB

db = RedisDBWithPoolAsync({
    "hostname": "localhost",
    "port": 3306,
    "username": "root",
    "password": "your_password",
    "database": 0
})
await db.open()
try:
    async with db as redis_con:
        await redis_con.set("key", "value")
        value = await redis_con.get("key")
        print(value)  # Output: b'value'

finally:
    await db.close()
```

### Notes
No wrapper at this time, as redis is just a key-value store.
