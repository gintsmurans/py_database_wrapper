#!/bin/bash

source /srv/meta/scripts/console.bash


#####################
### Configuration ###
#####################
if [ -f /run/secrets/user_ssh_key ]; then
    echo_info "Fix ssh key permissions"
    mkdir -p "$HOME/.ssh" && \
    cp /run/secrets/user_ssh_key "$HOME/.ssh/id_rsa" && \
    chmod 600 "$HOME/.ssh/id_rsa"
fi

# Go to app directory
cd /srv/app

# Setup precommit link
echo_info "Setup precommit link"
ln -sf ../../scripts/git_pre_commit.bash .git/hooks/pre-commit

# Install project requirements
python3 -m pip install -e ./src/database_wrapper/[dev]
python3 -m pip install -e ./src/database_wrapper_mssql/[dev]
python3 -m pip install -e ./src/database_wrapper_mysql/
python3 -m pip install -e ./src/database_wrapper_pgsql/
python3 -m pip install -e ./src/database_wrapper_sqlite/
python3 -m pip install -e ./src/database_wrapper_redis/


########################
### Run main process ###
########################
echo_info "Run sleep infinity as PID 1"
exec sleep infinity
