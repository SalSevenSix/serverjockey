#!/bin/bash

NPM_COMMAND="${1-install}"
cd "$(dirname $0)" || exit 1
rm -rf build > /dev/null 2>&1
rm -rf ../../web > /dev/null 2>&1
echo "running npm $NPM_COMMAND"
npm $NPM_COMMAND || exit 1
npm run build || exit 1
touch build/__init__.py
mv build ../../web || exit 1
[ -d ../../web ] || exit 1

exit 0
