# py_database_wrapper

A Different Approach to Database Wrappers in Python

This project aims to create an alternative to the commonly used ORMs in Python, focusing on raw queries, models that represent returned results, and a straightforward base to make simple queries genuinely simple.

## Installation

```bash
pip install database_wrapper[pgsql] # for postgres
pip install database_wrapper[mysql] # for mysql
pip install database_wrapper[mssql] # for mssql
pip install database_wrapper[sqlite] # TODO: for sqlite
```

## Usage

General usage is the same for all databases. The only difference is the import statement and the class name.

#### Random notes:

* For now all databases are sync, except for PostgreSQL which can use both sync and async.
    * PgSQL connector for sync
    * AsyncPgSQLWithPooling for async
* We are assuming that there is no point of using tuple cursors, so behind the scenes all databases are using dict cursors.
* Wrapper methods that return multiple results are async generators.
* Wrapper methods that return a single result are still async methods, but returns without generator.


#### Specific database wrappers:

* [database_wrapper_pgsql](src/database_wrapper_pgsql)
* [database_wrapper_mysql](src/database_wrapper_mysql)
* [database_wrapper_mssql](src/database_wrapper_mssql)
* [database_wrapper_sqlite](src/database_wrapper_sqlite)


## Development

For develompent we are using docker. To start the development environment run the following command:

```bash
docker compose build develop && docker compose up -d --remove-orphans develop
```

Now when inside the container (how to do that is beyond the scope of this README) you should be able to install packages in editable mode:

```bash
pip install -e ./src/database_wrapper --config-settings editable_mode=strict
pip install -e ./src/database_wrapper_pgsql --config-settings editable_mode=strict
pip install -e ./src/database_wrapper_mysql --config-settings editable_mode=strict
pip install -e ./src/database_wrapper_mssql --config-settings editable_mode=strict
pip install -e ./src/database_wrapper_sqlite --config-settings editable_mode=strict
```

We are adding `--config-settings editable_mode=strict` for vscode to be able to use the packages in the development environment. See [#3473](https://github.com/microsoft/pylance-release/issues/3473)


## TODO

* Add sync wrappers that themselves are sync
* Add sqlite support
    * Would be nice to have also async support for sqlite
* Add more tests
* Add more usage examples
* Create a better documentation
* Add async support for MySQL and MSSQL - need to look into libraries that support this
* Do we need more database support? If so, which ones?
