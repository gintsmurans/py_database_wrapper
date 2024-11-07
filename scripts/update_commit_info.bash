#!/bin/bash

#############################################
### Update commit info in specified files ###
#############################################

FILES_TO_UPDATE=(
    "src/db_wrapper/db_wrapper/config.py"
)

# Find base path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
BASE_PATH="$(cd "$SCRIPT_DIR" && pwd)"

# Set variables the we need
COMMIT_INFO=$(git log -1 --pretty="%H%n%cd" --date=format:"%d.%m.%Y %H:%M")
COMMIT_HASH=$(echo "$COMMIT_INFO" | head -1)
COMMIT_DATE=$(echo "$COMMIT_INFO" | head -2 | tail -1)

for FILE in "${FILES_TO_UPDATE[@]}"; do
    if [ -f "$FILE" ]; then
        echo "Updating commit info in $FILE"
        sed -E "s/(git_commit_hash('\] = '|: '|\": \")).*(['\"];?)/\1$COMMIT_HASH\3/" $FILE > $FILE.bak \
            && mv $FILE.bak $FILE
        sed -E "s/(git_commit_date('\] = '|: '|\": \")).*(['\"];?)/\1$COMMIT_DATE\3/" $FILE > $FILE.bak \
            && mv $FILE.bak $FILE
        git add $FILE
    else
        echo "Warning: $FILE not found!"
    fi
done

echo "Done"
