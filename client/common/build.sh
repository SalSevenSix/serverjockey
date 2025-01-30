#!/bin/bash

echo "Initialising common lib build"
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
if [ "$INSTALL_COMMAND" != "skip" ]; then
  echo "Installing dependencies"
  $JS_PKGMGR $INSTALL_COMMAND || exit 1
fi

echo "Common lib lint"
$JS_PKGMGR run lint || exit 1

echo "Done common lib build"
exit 0
