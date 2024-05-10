#!/bin/bash

echo "Initialising DEB packaging"
[ "$(whoami)" = "root" ] || exit 1
cd "$(dirname $0)/dist" || exit 1
TARGET_DIR="sjgms"
[ -f "$TARGET_DIR/build.ok" ] || exit 1
rm $TARGET_DIR/build.ok > /dev/null 2>&1
VERSION=$(awk '/^Version:/{print $2}' "$TARGET_DIR/DEBIAN/control")
OSVER="ub$(grep 'VERSION_ID=' /etc/os-release | tr '"' ' ' | tr '.' ' ' | awk '{print $2}')"
DEB_FILE="sjgms.deb"
rm $DEB_FILE > /dev/null 2>&1
rm -rf $TARGET_DIR/SPECS > /dev/null 2>&1

echo "Preparing build directory"
find $TARGET_DIR -type d -exec chmod 755 {} +
find $TARGET_DIR -type f -exec chmod 644 {} +
find $TARGET_DIR/usr/local/bin -type f -exec chmod 755 {} +
chmod 755 $TARGET_DIR/DEBIAN/prerm $TARGET_DIR/DEBIAN/postrm $TARGET_DIR/DEBIAN/preinst $TARGET_DIR/DEBIAN/postinst
chown -R root $TARGET_DIR
chgrp -R root $TARGET_DIR

dpkg-deb --build $TARGET_DIR || exit 1
[ -f $DEB_FILE ] || exit 1
if [ ! -z $SUDO_USER ]; then
  chown $SUDO_USER $DEB_FILE
  chgrp $SUDO_USER $DEB_FILE
fi
mv "$DEB_FILE" "sjgms-${VERSION}.${OSVER}.x86_64.deb"

echo "Cleanup"
rm -rf $TARGET_DIR > /dev/null 2>&1

echo "Done DEB packaging"
exit 0
