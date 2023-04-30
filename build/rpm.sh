#!/bin/bash

cd "$(dirname $0)/dist" || exit 1
DIST_DIR="$(pwd)"
RPMBUILD_DIR="$HOME/rpmbuild"
TARGET_DIR="$DIST_DIR/sjgms"
[ -f "$TARGET_DIR/SPECS/sjgms.spec" ] || exit 1
VERSION=$(awk '/^Version:/{print $2}' "$TARGET_DIR/SPECS/sjgms.spec")
OSVER="fc$(cat /etc/fedora-release | awk {'print$3'})"
RPM_FILE="$RPMBUILD_DIR/RPMS/x86_64/sjgms-${VERSION}-1.${OSVER}.x86_64.rpm"
TAR_DIR="${TARGET_DIR}-${VERSION}"
rm -rf $TAR_DIR > /dev/null 2>&1

echo "Building rpmbuild directory as needed"
[ -d "$RPMBUILD_DIR/BUILD" ] || mkdir -p $RPMBUILD_DIR/BUILD
[ -d "$RPMBUILD_DIR/BUILDROOT" ] || mkdir -p $RPMBUILD_DIR/BUILDROOT
[ -d "$RPMBUILD_DIR/RPMS" ] || mkdir -p $RPMBUILD_DIR/RPMS
[ -d "$RPMBUILD_DIR/SOURCES" ] || mkdir -p $RPMBUILD_DIR/SOURCES
[ -d "$RPMBUILD_DIR/SPECS" ] || mkdir -p $RPMBUILD_DIR/SPECS
[ -d "$RPMBUILD_DIR/SRPMS" ] || mkdir -p $RPMBUILD_DIR/SRPMS
cp "$TARGET_DIR/SPECS/sjgms.spec" "$RPMBUILD_DIR/SPECS/sjgms.spec"

echo "Building directory for TAR file"
mkdir $TAR_DIR
mv $TARGET_DIR/usr/local/bin/* $TAR_DIR
mv $TARGET_DIR/etc/systemd/system/* $TAR_DIR

echo "Setting directory and file perms"
find $TAR_DIR -type d -exec chmod 755 {} +
find $TAR_DIR -type f -exec chmod 644 {} +
chmod 755 $TAR_DIR/*.pyz
chmod 755 $TAR_DIR/serverlink

echo "Creating TAR file"
tar --create --file "sjgms-${VERSION}.tar.gz" "sjgms-${VERSION}"
[ $? -eq 0 ] || exit 1
[ -f "$DIST_DIR/sjgms-${VERSION}.tar.gz" ] || exit 1

echo "Building RPM file"
rm -rf $RPMBUILD_DIR/SOURCES/*
mv $DIST_DIR/sjgms-$VERSION.tar.gz $RPMBUILD_DIR/SOURCES
rpmbuild -bb $RPMBUILD_DIR/SPECS/sjgms.spec
[ $? -eq 0 ] || exit 1
[ -f "$RPM_FILE" ] || exit 1
mv $RPM_FILE $DIST_DIR

echo "Cleanup"
rm -rf $TARGET_DIR $TAR_DIR > /dev/null 2>&1

echo "Done"
exit 0
