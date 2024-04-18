#!/bin/bash

cd "$(dirname $0)" || exit 1
SOURCE_DIR="$(pwd)"
TARGET_FILE="${1}"
WORK_DIR="/tmp/cli${$}"
CMD_NAME="serverjockey_cmd"
FILE_NAME="$CMD_NAME.pyz"

cd $SOURCE_DIR || exit 1
rm -rf build > /dev/null 2>&1
rm -rf $WORK_DIR > /dev/null 2>&1
mkdir -p $WORK_DIR/cli || exit 1
cp -r . $WORK_DIR/cli || exit 1

cd $WORK_DIR || exit 1
rm cli/build.sh || exit 1
find cli -name "__pycache__" -type d | while read file; do
  rm -rf $file > /dev/null 2>&1
done

python3 -m zipapp "cli" -p "/usr/bin/env python3" -m "$CMD_NAME:main" -c -o $FILE_NAME || exit 1

cd $SOURCE_DIR || exit 1
mkdir build || exit 1
mv $WORK_DIR/$FILE_NAME build/$FILE_NAME
rm -rf $WORK_DIR > /dev/null 2>&1

if [ ! -z $TARGET_FILE ]; then
  rm $TARGET_FILE > /dev/null 2>&1
  cp build/$FILE_NAME $TARGET_FILE || exit 1
fi

exit 0
