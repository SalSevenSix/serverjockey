#!/bin/bash

echo "Initialising PAC packaging"
cd "$(dirname $0)" || exit 1
[ -f "build.ok" ] || exit 1
rm build.ok > /dev/null 2>&1

echo "Building PAC file"
cd bin || exit 1
cp ../pac/* . || exit 1
makepkg || exit 1
PKG_FILE="$(ls sjgms-*.pkg.tar.zst)"
VERSION="$(grep 'pkgver=' PKGBUILD | tr '=' ' ' | awk '{print $2}')"
cd ../.. || exit 1
mv sjgms/bin/$PKG_FILE sjgms-${VERSION}.x86_64.pkg.tar.zst || exit 1
rm -rf sjgms > /dev/null 2>&1

echo "Done PAC packaging"
exit 0
