#!/bin/bash

INSTALL_COMMAND="${1}"

cd "$(dirname $0)" || exit 1
rm -rf build > /dev/null 2>&1
rm -rf ../../web > /dev/null 2>&1
if [ ! -z $INSTALL_COMMAND ]; then
  echo "running npm $INSTALL_COMMAND"
  npm $INSTALL_COMMAND || exit 1
fi
npm run build || exit 1
touch build/__init__.py
mv build ../../web || exit 1
[ -d ../../web ] || exit 1

exit 0
