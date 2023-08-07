#!/bin/bash

[ "$(whoami)" = "root" ] || exit 1
WEB_DIR="/var/www/html"
[ -d "$WEB_DIR" ] || exit 1
cd "$(dirname $0)" || exit 1
BUILD_DIR="$(pwd)"
BUILD_USER="$(pwd | tr '/' ' ' | awk '{print $2}')"
BRANCH="develop"

echo "CI Preparing"
[ -f "build.sh" ] || wget -O build.sh https://raw.githubusercontent.com/SalSevenSix/serverjockey/$BRANCH/build/build.sh
[ -f "build.sh" ] || exit 1
chmod 755 build.sh || exit 1
chown $BUILD_USER build.sh || exit 1
chgrp $BUILD_USER build.sh || exit 1

echo "CI Building"
su - $BUILD_USER -c "$BUILD_DIR/build.sh $BRANCH"
[ $? -eq 0 ] || su - $BUILD_USER -c "$BUILD_DIR/build.sh $BRANCH"
[ $? -eq 0 ] || exit 1
TIMESTAMP="$(cat $BUILD_DIR/dist/sjgms/build.ok)"

echo "CI Packaging"
$BUILD_DIR/deb.sh || exit 1

echo "CI Publishing"
cd $BUILD_DIR/dist || exit 1
DEB_FILE="$(ls *.deb | tail -1)"
TARGET_FILE="sjgms-{$BRANCH}-{$TIMESTAMP}.deb"
mv $DEB_FILE $WEB_DIR/$TARGET_FILE || exit 1
cd $WEB_DIR || exit 1
ln -fs "$TARGET_FILE" "sjgms-{$BRANCH}-latest.deb" || exit 1

echo "CI Cleanup"
rm -rf "$BUILD_DIR/dist" > /dev/null 2>&1
find . -type f -name "sjgms-{$BRANCH}-*.deb" -mtime +7 -delete

echo "CI Done"
exit 0
