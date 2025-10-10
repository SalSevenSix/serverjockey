#!/bin/bash

echo "Initialising RPM packaging"
[ "$(whoami)" = "root" ] || exit 1
cd "$(dirname $0)/dist" || exit 1
DIST_DIR="$(pwd)"
RPMBUILD_DIR="$DIST_DIR/rpmbuild"
TARGET_DIR="$DIST_DIR/sjgms"
[ -f "$TARGET_DIR/build.ok" ] || exit 1
VERSION=$(awk '/^Version:/{print $2}' "$TARGET_DIR/SPECS/sjgms.spec")
OSVER="fc$(cat /etc/fedora-release | awk {'print$3'})"
RPM_FILE="$RPMBUILD_DIR/RPMS/x86_64/sjgms-${VERSION}-1.${OSVER}.x86_64.rpm"
TAR_DIR="${TARGET_DIR}-${VERSION}"
rm -rf $RPMBUILD_DIR $TAR_DIR $TARGET_DIR/DEBIAN > /dev/null 2>&1

echo "Building rpmbuild directory"
[ -d "$RPMBUILD_DIR/BUILD" ] || mkdir -p $RPMBUILD_DIR/BUILD || exit 1
[ -d "$RPMBUILD_DIR/BUILDROOT" ] || mkdir -p $RPMBUILD_DIR/BUILDROOT || exit 1
[ -d "$RPMBUILD_DIR/RPMS" ] || mkdir -p $RPMBUILD_DIR/RPMS || exit 1
[ -d "$RPMBUILD_DIR/SOURCES" ] || mkdir -p $RPMBUILD_DIR/SOURCES || exit 1
[ -d "$RPMBUILD_DIR/SPECS" ] || mkdir -p $RPMBUILD_DIR/SPECS || exit 1
[ -d "$RPMBUILD_DIR/SRPMS" ] || mkdir -p $RPMBUILD_DIR/SRPMS || exit 1
cp "$TARGET_DIR/SPECS/sjgms.spec" "$RPMBUILD_DIR/SPECS/sjgms.spec" || exit 1

echo "Preparing files"
mkdir $TAR_DIR || exit 1
mv $TARGET_DIR/usr/local/bin/* $TAR_DIR || exit 1
find $TAR_DIR -type d -exec chmod 755 {} + || exit 1
find $TAR_DIR -type f -exec chmod 644 {} + || exit 1
chmod 755 $TAR_DIR/*.pyz || exit 1
chmod 755 $TAR_DIR/serverlink || exit 1

echo "Building RPM file"
tar --create --file "sjgms-${VERSION}.tar.gz" "sjgms-${VERSION}" || exit 1
mv $DIST_DIR/sjgms-$VERSION.tar.gz $RPMBUILD_DIR/SOURCES || exit 1
rpmbuild --define "_topdir $RPMBUILD_DIR" -bb $RPMBUILD_DIR/SPECS/sjgms.spec || exit 1
[ -f "$RPM_FILE" ] || exit 1
mv $RPM_FILE $DIST_DIR || exit 1

echo "Cleanup"
rm -rf $RPMBUILD_DIR $TAR_DIR $TARGET_DIR > /dev/null 2>&1

echo "Done RPM packaging"
exit 0
