#!/bin/bash

echo "Initialising statapp build"
INSTALL_COMMAND="${1-skip}"
JS_PKGMGR="npm"
if ~/.bun/bin/bun --version > /dev/null 2>&1; then
  JS_PKGMGR=~/.bun/bin/bun
  [ "$INSTALL_COMMAND" = "ci" ] && INSTALL_COMMAND="install --frozen-lockfile"
  echo "bun version $(~/.bun/bin/bun --version)"
else
  command -v npm > /dev/null || exit 1
  echo "npm version $(npm --version)"
fi

cd "$(dirname $0)" || exit 1
rm -rf build statapp.zip > /dev/null 2>&1
if [ "$INSTALL_COMMAND" != "skip" ]; then
  echo "Installing dependencies"
  $JS_PKGMGR $INSTALL_COMMAND || exit 1
fi

echo "Statapp build"
$JS_PKGMGR run lint || exit 1
$JS_PKGMGR run build || exit 1
rm -rf build/data > /dev/null 2>&1

if [ -d ../../web/assets/extensions ]; then
  echo "Statapp zip"
  cd build || exit 1
  zip -r9 ../statapp.zip * > /dev/null || exit 1
  cd .. || exit 1
  mv -f statapp.zip ../../web/assets/extensions || exit 1
fi

echo "Done statapp build"
exit 0
