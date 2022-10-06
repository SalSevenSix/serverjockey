#!/bin/bash

cd "$(dirname $0)" || exit 1
rm -rf build > /dev/null 2>&1
rm -rf ../../web > /dev/null 2>&1
npm install || exit 1
npm run build || exit 1
echo "__version__ = '0.0.3'" > build/__init__.py
mv build ../../web
[ -d ../../web ] || exit 1

exit 0
