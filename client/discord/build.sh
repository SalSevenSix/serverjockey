#!/bin/bash

echo "Initialising discord bot build"
INSTALL_COMMAND="${1-skip}"
TARGET_FILE="${2}"
JS_RUNTIME="node"
if ~/.bun/bin/bun --version > /dev/null 2>&1; then
  JS_RUNTIME=~/.bun/bin/bun
  echo "bun version $(~/.bun/bin/bun --version)"
else
  which node > /dev/null || exit 1
  echo "node version $(node --version)"
  which npm > /dev/null || exit 1
  echo "npm version $(npm --version)"
  which nexe > /dev/null || exit
fi

cd "$(dirname $0)" || exit 1
rm -rf build > /dev/null 2>&1
mkdir build || exit 1
if [ "$INSTALL_COMMAND" != "skip" ]; then
  echo "Installing dependencies"
  if [ "$JS_RUNTIME" = "node" ]; then
    npm $INSTALL_COMMAND || exit 1
  else  # bun
    [ "$INSTALL_COMMAND" = "ci" ] && INSTALL_COMMAND="install --frozen-lockfile"
    $JS_RUNTIME $INSTALL_COMMAND || exit 1
  fi
fi

echo "Discord bot build"
if [ "$JS_RUNTIME" = "node" ]; then
  PYTHON_EXE=$(which python3)
  NODE_OUT_DIR=~/.nexe/$(node --version | cut -c2-)/out/Release
  nexe index.js --output build/serverlink --build --python=$PYTHON_EXE || exit 1
  [ -d $NODE_OUT_DIR ] || exit 1
  if [ ! -f $NODE_OUT_DIR/node_unstripped ]; then
    echo "stripping node executable and rebuilding"
    rm build/serverlink > /dev/null 2>&1
    cp $NODE_OUT_DIR/node $NODE_OUT_DIR/node_unstripped || exit 1
    strip $NODE_OUT_DIR/node || exit 1
    nexe index.js --output build/serverlink --build --python=$PYTHON_EXE || exit 1
  fi
else  # bun
  $JS_RUNTIME build ./index.js --compile --outfile=build/serverlink || exit 1
fi

if [ ! -z $TARGET_FILE ]; then
  echo "Exporting serverlink executable"
  rm $TARGET_FILE > /dev/null 2>&1
  cp build/serverlink $TARGET_FILE || exit 1
fi

echo "Done discord bot build"
exit 0
