#!/usr/bin/env bash
set -Eeuo pipefail

export PYTHONWARNINGS=error

source /srv/meta/scripts/console.bash || true

# Go to app source
cd /srv/app

# Strict byte-compile (syntax check)
echo_process "Byte-compiling Python sources... "
if ! python -W error -m compileall -q -f -j0 src/; then
  echo_fail "!!! ERROR: Python compile failed!"
  exit 1
fi
echo_ok ""

# Style check with ruff
echo_process "Running ruff style checks... "
ruff check src/
echo_ok ""

# Unit tests
echo_process "Running unit tests... "
python3 -m unittest discover -v src/tests
echo_ok ""

# Dependency graph sanity
echo_process "Checking installed package dependencies... "
pip check > /dev/null
echo_ok ""


echo_success "All fast tests passed."
