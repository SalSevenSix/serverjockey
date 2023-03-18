#!/bin/bash

HOME_DIR="$(pwd)"
RPMBUILD_DIR="$HOME/rpmbuild"
[ -d $RPMBUILD_DIR ] || exit 1
VERSION="$(grep 'Version:' $RPMBUILD_DIR/SPECS/sjgms.spec | awk {'print$2'})"
TARGET_DIR="$HOME_DIR/sjgms"
[ -d $TARGET_DIR ] || exit 1
OSVER="fc$(cat /etc/fedora-release | awk {'print$3'})"
RPM_FILE="$RPMBUILD_DIR/RPMS/x86_64/sjgms-$VERSION-1.$OSVER.x86_64.rpm"
TAR_DIR="$TARGET_DIR-$VERSION"
rm -rf $TAR_DIR > /dev/null 2>&1

mkdir $TAR_DIR
mv $TARGET_DIR/usr/local/bin/* $TAR_DIR
mv $TARGET_DIR/etc/systemd/system/* $TAR_DIR
rm -rf $TARGET_DIR > /dev/null 2>&1

find $TAR_DIR -type d -exec chmod 755 {} +
find $TAR_DIR -type f -exec chmod 644 {} +
chmod 755 $TAR_DIR/serverjockey.pyz
chmod 755 $TAR_DIR/serverlink

tar --create --file sjgms-$VERSION.tar.gz sjgms-$VERSION
[ $? -eq 0 ] || exit 1
[ -f "$HOME_DIR/sjgms-$VERSION.tar.gz" ] || exit 1

rm -rf $RPMBUILD_DIR/SOURCES/*
mv $HOME_DIR/sjgms-$VERSION.tar.gz $RPMBUILD_DIR/SOURCES
rpmbuild -bb $RPMBUILD_DIR/SPECS/sjgms.spec
[ $? -eq 0 ] || exit 1
[ -f "$RPM_FILE" ] || exit 1

mv $RPM_FILE $HOME_DIR
rm -rf $TAR_DIR > /dev/null 2>&1

exit 0
