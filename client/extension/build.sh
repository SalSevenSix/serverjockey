#!/bin/bash

echo "Initialising extension build"
which npm > /dev/null || exit 1
which zip > /dev/null || exit 1
cd "$(dirname $0)" || exit 1
rm -rf build chrome-extension.zip > /dev/null 2>&1

INSTALL_COMMAND="${1}"
if [ ! -z $INSTALL_COMMAND ]; then
  echo "extension npm $INSTALL_COMMAND"
  npm $INSTALL_COMMAND || exit 1
fi

echo "extension npm build"
npm run build || exit 1

if [ -d ../../web ]; then
  echo "extension zip"
  rm -rf ../../web/assets/extensions > /dev/null 2>&1
  mkdir -p ../../web/assets/extensions || exit 1
  cd build || exit 1
  zip -r9 ../chrome-extension.zip * > /dev/null || exit 1
  cd .. || exit 1
  mv chrome-extension.zip ../../web/assets/extensions || exit 1
fi

echo "Done extension build"
exit 0
