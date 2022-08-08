#!/bin/bash

HOME_DIR="$(pwd)"
TARGET_DIR="$HOME_DIR/sjgms"
[ -d $TARGET_DIR ] || exit 1
rm sjgms.deb > /dev/null 2>&1

find $TARGET_DIR -type d -exec chmod 755 {} +
find $TARGET_DIR -type f -exec chmod 644 {} +
find $TARGET_DIR/usr/local/bin -type f -exec chmod 755 {} +
chmod 755 $TARGET_DIR/DEBIAN/preinst
chmod 755 $TARGET_DIR/DEBIAN/postinst
chown -R root $TARGET_DIR
chgrp -R root $TARGET_DIR

dpkg-deb --build sjgms
[ $? -eq 0 ] || exit 1
[ -f "sjgms.deb" ] || exit 1
chown bsalis sjgms.deb
chgrp bsalis sjgms.deb

rm -rf $TARGET_DIR > /dev/null 2>&1

exit 0
