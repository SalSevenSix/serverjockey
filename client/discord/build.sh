#!/bin/bash

INSTALL_COMMAND="${1}"
TARGET_FILE="${2}"
NODE_OUT_DIR=~/.nexe/$(node --version | cut -c2-)/out/Release
PYTHON_EXE=$(which python3.10)

cd "$(dirname $0)" || exit 1
rm -rf build > /dev/null 2>&1
mkdir build || exit 1
if [ ! -z $INSTALL_COMMAND ]; then
  echo "running npm $INSTALL_COMMAND"
  npm $INSTALL_COMMAND || exit 1
  cp hax/index.js node_modules/@discordjs/rest/dist/index.js || exit 1
fi

nexe index.js --output build/serverlink --build --python=$PYTHON_EXE || exit 1
[ -d $NODE_OUT_DIR ] || exit 1
if [ ! -f $NODE_OUT_DIR/node_unstripped ]; then
  echo "stripping node executable and rebuilding"
  rm build/serverlink > /dev/null 2>&1
  cp $NODE_OUT_DIR/node $NODE_OUT_DIR/node_unstripped || exit 1
  strip $NODE_OUT_DIR/node || exit 1
  nexe index.js --output build/serverlink --build --python=$PYTHON_EXE || exit 1
fi

if [ ! -z $TARGET_FILE ]; then
  rm $TARGET_FILE > /dev/null 2>&1
  cp build/serverlink $TARGET_FILE || exit 1
fi

exit 0
