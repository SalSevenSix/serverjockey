#!/bin/bash

echo "Initialising webapp build"
which npm > /dev/null || exit 1
cd "$(dirname $0)" || exit 1
rm -rf build > /dev/null 2>&1
rm -rf ../../web > /dev/null 2>&1

INSTALL_COMMAND="${1}"
if [ ! -z $INSTALL_COMMAND ]; then
  echo "webapp npm $INSTALL_COMMAND"
  npm $INSTALL_COMMAND || exit 1
fi

echo "webapp npm build"
npm run build || exit 1
touch build/__init__.py
mv build ../../web || exit 1

echo "Done webapp build"
exit 0
