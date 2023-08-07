#!/bin/bash

[ "$(whoami)" = "root" ] || exit 1
cd "$(dirname $0)/dist" || exit 1
TARGET_DIR="sjgms"
[ -f "$TARGET_DIR/build.ok" ] || exit 1
rm $TARGET_DIR/build.ok > /dev/null 2>&1
VERSION=$(awk '/^Version:/{print $2}' "$TARGET_DIR/DEBIAN/control")
DEB_FILE="sjgms.deb"
rm $DEB_FILE > /dev/null 2>&1
rm -rf $TARGET_DIR/SPECS > /dev/null 2>&1

echo "Preparing build directory"
find $TARGET_DIR -type d -exec chmod 755 {} +
find $TARGET_DIR -type f -exec chmod 644 {} +
find $TARGET_DIR/usr/local/bin -type f -exec chmod 755 {} +
chmod 755 $TARGET_DIR/DEBIAN/preinst
chmod 755 $TARGET_DIR/DEBIAN/postinst
chown -R root $TARGET_DIR
chgrp -R root $TARGET_DIR

dpkg-deb --build $TARGET_DIR || exit 1
[ -f $DEB_FILE ] || exit 1
if [ ! -z $SUDO_USER ]; then
  chown $SUDO_USER $DEB_FILE
  chgrp $SUDO_USER $DEB_FILE
fi
mv "$DEB_FILE" "sjgms-${VERSION}.x86_64.deb"

echo "Cleanup"
rm -rf $TARGET_DIR > /dev/null 2>&1

echo "Done"
exit 0
