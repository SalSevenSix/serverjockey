#!/bin/bash

echo "Initialising extension build"
which zip > /dev/null || exit 1
INSTALL_COMMAND="${1-skip}"
JS_PKGMGR="npm"
if ~/.bun/bin/bun --version > /dev/null 2>&1; then
  JS_PKGMGR=~/.bun/bin/bun
  [ "$INSTALL_COMMAND" = "ci" ] && INSTALL_COMMAND="install --frozen-lockfile"
  echo "bun version $(~/.bun/bin/bun --version)"
else
  which npm > /dev/null || exit 1
  echo "npm version $(npm --version)"
fi

cd "$(dirname $0)" || exit 1
rm -rf build chrome-extension.zip > /dev/null 2>&1
if [ "$INSTALL_COMMAND" != "skip" ]; then
  echo "Installing dependencies"
  $JS_PKGMGR $INSTALL_COMMAND || exit 1
fi

echo "Extension build"
$JS_PKGMGR lint || exit 1
$JS_PKGMGR run build || exit 1

if [ -d ../../web ]; then
  echo "Extension zip"
  rm -rf ../../web/assets/extensions > /dev/null 2>&1
  mkdir -p ../../web/assets/extensions || exit 1
  cd build || exit 1
  zip -r9 ../chrome-extension.zip * > /dev/null || exit 1
  cd .. || exit 1
  mv chrome-extension.zip ../../web/assets/extensions || exit 1
fi

echo "Done extension build"
exit 0
