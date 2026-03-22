#!/bin/bash

echo "Initialising DEB packaging"
[ "$(whoami)" = "root" ] || exit 1
cd "$(dirname $0)/dist" || exit 1
TARGET_DIR="sjgms"
[ -f "$TARGET_DIR/build.ok" ] || exit 1
CONTROL_FILE="$TARGET_DIR/DEBIAN/control"
rm -rf $TARGET_DIR/build.ok $TARGET_DIR/SPECS sjgms.deb > /dev/null 2>&1

echo "Preparing build directory"
echo "Installed-Size: $(du -sk $TARGET_DIR | awk '{print $1}')" >> $CONTROL_FILE
mkdir -p $TARGET_DIR/usr/local || exit 1
mv $TARGET_DIR/bin $TARGET_DIR/usr/local/bin || exit 1
find $TARGET_DIR -type d -exec chmod 755 {} + || exit 1
find $TARGET_DIR -type f -exec chmod 644 {} + || exit 1
chmod 755 $TARGET_DIR/usr/local/bin/* || exit 1
chmod 755 $TARGET_DIR/DEBIAN/preinst $TARGET_DIR/DEBIAN/postinst || exit 1
chmod 755 $TARGET_DIR/DEBIAN/prerm $TARGET_DIR/DEBIAN/postrm || exit 1
chown -R root $TARGET_DIR || exit 1
chgrp -R root $TARGET_DIR || exit 1

dpkg-deb --build $TARGET_DIR || exit 1
if [ ! -z $SUDO_USER ]; then
  chown $SUDO_USER sjgms.deb || exit 1
  chgrp $SUDO_USER sjgms.deb || exit 1
fi
VERSION="$(awk '/^Version:/{print $2}' $CONTROL_FILE)"
OSVER="ub$(grep 'VERSION_ID=' /etc/os-release | tr '"' ' ' | tr '.' ' ' | awk '{print $2}')"
mv "sjgms.deb" "sjgms-${VERSION}.${OSVER}.x86_64.deb" || exit 1
rm -rf $TARGET_DIR > /dev/null 2>&1

echo "Done DEB packaging"
exit 0
