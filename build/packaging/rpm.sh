#!/bin/bash

echo "Initialising RPM packaging"
cd "$(dirname $0)" || exit 1
[ -f "build.ok" ] || exit 1
TARGET_DIR="$(pwd)"
cd .. || exit 1
DIST_DIR="$(pwd)"
RPMBUILD_DIR="$DIST_DIR/rpmbuild"
VERSION=$(awk '/^Version:/{print $2}' "$TARGET_DIR/rpm/sjgms.spec")
OSVER="fc$(cat /etc/fedora-release | awk {'print$3'})"
RPM_FILE="$RPMBUILD_DIR/RPMS/x86_64/sjgms-${VERSION}-1.${OSVER}.x86_64.rpm"
TAR_DIR="${TARGET_DIR}-${VERSION}"
rm -rf $RPMBUILD_DIR $TAR_DIR $TARGET_DIR/build.ok > /dev/null 2>&1

echo "Preparing RPM structure"
mkdir $RPMBUILD_DIR || exit 1
mkdir $RPMBUILD_DIR/BUILD || exit 1
mkdir $RPMBUILD_DIR/BUILDROOT || exit 1
mkdir $RPMBUILD_DIR/RPMS || exit 1
mkdir $RPMBUILD_DIR/SOURCES || exit 1
mkdir $RPMBUILD_DIR/SRPMS || exit 1
mkdir $RPMBUILD_DIR/SPECS || exit 1
cp $TARGET_DIR/rpm/sjgms.spec $RPMBUILD_DIR/SPECS/sjgms.spec || exit 1
mv $TARGET_DIR/bin $TAR_DIR || exit 1
chmod -R 755 $TAR_DIR || exit 1

echo "Building RPM file"
tar --create --file "sjgms-${VERSION}.tar.gz" "sjgms-${VERSION}" || exit 1
mv $DIST_DIR/sjgms-${VERSION}.tar.gz $RPMBUILD_DIR/SOURCES || exit 1
rpmbuild --define "_topdir $RPMBUILD_DIR" -bb $RPMBUILD_DIR/SPECS/sjgms.spec || exit 1
mv $RPM_FILE $DIST_DIR || exit 1
rm -rf $RPMBUILD_DIR $TAR_DIR $TARGET_DIR > /dev/null 2>&1

echo "Done RPM packaging"
exit 0
