#!/bin/bash

HOME_DIR="$(pwd)"
cd "$(dirname $0)" || exit 1
[[ "$HOME_DIR" == "$(pwd)" ]] || exit 1

rm -rf build > /dev/null 2>&1
rm -rf ../../web > /dev/null 2>&1
npm run build
echo "__version__ = '0.0.0'" > build/__init__.py
mv build ../../web

exit 0
