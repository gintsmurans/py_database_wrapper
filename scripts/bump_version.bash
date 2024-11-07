#!/bin/bash

####################
### Bump version ###
####################

# Define the files where the version should be replaced
FILES_TO_UPDATE=(
  "pyproject.toml"
  "src/db_wrapper/pyproject.toml"
  "src/db_wrapper_pgsql/pyproject.toml"
  "src/db_wrapper_mysql/pyproject.toml"
  "src/db_wrapper_mssql/pyproject.toml"
  "src/db_wrapper/db_wrapper/config.py"
)

# Fail if any command fails
set -e

# Define usage
usage() {
  echo "Usage: $0 {major|minor|patch}"
  exit 1
}

# Ensure an argument is passed
if [ -z "$1" ]; then
  usage
fi

# Load current version from .current_version file
VERSION_FILE=".current_version"
if [ ! -f "$VERSION_FILE" ]; then
  echo "Error: $VERSION_FILE file not found!"
  exit 1
fi

# Read the current version
CURRENT_VERSION=$(cat $VERSION_FILE)

# Split the version into components (major, minor, patch)
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

# Determine which part of the version to bump
case "$1" in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    usage
    ;;
esac

# New version after bumping
NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "Bumping version: $CURRENT_VERSION -> $NEW_VERSION"

# Replace the version in the specified files
for FILE in "${FILES_TO_UPDATE[@]}"; do
  if [ -f "$FILE" ]; then
    echo "Updating version in $FILE"
    sed -i "s/$CURRENT_VERSION/$NEW_VERSION/g" "$FILE"
    git add "$FILE"
  else
    echo "Warning: $FILE not found!"
  fi
done

# Update the version in .current_version file
echo "$NEW_VERSION" > "$VERSION_FILE"
git add "$VERSION_FILE"
echo "Version bumped to $NEW_VERSION"
