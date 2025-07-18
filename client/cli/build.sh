#!/bin/bash

echo "Initialising cli build"
cd "$(dirname $0)" || exit 1
TARGET_FILE="${1}"
CMD_NAME="serverjockey_cmd"
FILE_NAME="$CMD_NAME.pyz"

rm -rf build > /dev/null 2>&1
mkdir -p build/cli || exit 1
cp -r lib rsc *.py build/cli || exit 1

cd build || exit 1
find cli -name "__pycache__" -type d | while read file; do
  rm -rf $file > /dev/null 2>&1
done

python3 -m zipapp "cli" -p "/usr/bin/env python3" -m "$CMD_NAME:main" -c -o $FILE_NAME || exit 1
rm -rf cli > /dev/null 2>&1

if [ ! -z $TARGET_FILE ]; then
  rm $TARGET_FILE > /dev/null 2>&1
  cp $FILE_NAME $TARGET_FILE || exit 1
fi

echo "Done cli build"
exit 0
