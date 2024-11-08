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

_needs to be updated_


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
