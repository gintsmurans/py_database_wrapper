#!/bin/bash

source /root/meta/scripts/console.bash


#####################
### Configuration ###
#####################
if [ -f /run/secrets/user_ssh_key ]; then
    echo_info "Fix ssh key permissions"
    mkdir /root/.ssh && \
    cp /run/secrets/user_ssh_key /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa
fi

# Go to app directory
cd /srv/app

# Setup precommit link
echo_info "Setup precommit link"
ln -sf /srv/app/scripts/git_pre_commit.bash /srv/app/.git/hooks/pre-commit

# Install project requirements
python3 -m pip install -e ./src/database_wrapper/[dev]


########################
### Run main process ###
########################
# Define a function to handle the SIGTERM signal
function handle_sigterm {
  echo "Received SIGTERM signal. Stopping long running process..."

  # Gracefully close the main process
  kill -SIGTERM $pid

  # Exit with the SIGTERM received code
  exit 143; # 128 + 15 -- SIGTERM
}

echo_info "Set the trap to catch the SIGTERM signal"
trap 'handle_sigterm' SIGTERM

echo_info "Run bash as infinite process"
/bin/bash -c "while true; do sleep 1; done" &
pid=$!

echo_info "Wait for the process $pid to finish"
wait $pid
