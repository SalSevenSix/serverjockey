#!/bin/bash

[ "$(whoami)" = "root" ] || exit 1
BRANCH="develop"
WEB_DIR="/var/www/html"
[ -d "$WEB_DIR" ] || exit 1
cd "$(dirname $0)" || exit 1
BUILD_DIR="$(pwd)"
BUILD_USER="$(pwd | tr '/' ' ' | awk '{print $2}')"
COMMIT_FILE="${BRANCH}-commit.url"
BRANCH_FILE="/tmp/${$}-${BRANCH}-info.json"

echo "CI Checking"
LAST_URL="none"
[ -f "$COMMIT_FILE" ] && LAST_URL="$(head -1 $COMMIT_FILE)"
echo "  last commit     $LAST_URL"
su - $BUILD_USER -c "gh api repos/SalSevenSix/serverjockey/branches/$BRANCH" > $BRANCH_FILE
[ $? -eq 0 ] || exit 1
CURRENT_URL="$(jq -r .commit.url $BRANCH_FILE)"
rm $BRANCH_FILE > /dev/null 2>&1
echo "  current commit  $CURRENT_URL"
if [ "$LAST_URL" = "$CURRENT_URL" ]; then
  echo "No new commit found NOT building"
  exit 0
fi
echo $CURRENT_URL > $COMMIT_FILE
chown $BUILD_USER $COMMIT_FILE || exit 1
chgrp $BUILD_USER $COMMIT_FILE || exit 1

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
TIMESTAMP="$(head -1 $BUILD_DIR/dist/sjgms/build.ok)"

echo "CI Packaging"
$BUILD_DIR/deb.sh || exit 1

echo "CI Publishing"
cd $BUILD_DIR/dist || exit 1
DEB_FILE="$(ls *.deb | tail -1)"
TARGET_FILE="sjgms-${BRANCH}-${TIMESTAMP}.deb"
chown root $DEB_FILE || exit 1
chgrp root $DEB_FILE || exit 1
mv $DEB_FILE $WEB_DIR/$TARGET_FILE || exit 1
cd $WEB_DIR || exit 1
ln -fs "$TARGET_FILE" "sjgms-${BRANCH}-latest.deb" || exit 1

echo "CI Cleanup"
rm -rf "$BUILD_DIR/dist" > /dev/null 2>&1
find . -type f -name "sjgms-${BRANCH}-*.deb" -mtime +7 -delete

echo "CI Upgrade"
systemctl stop serverjockey > /dev/null 2>&1
apt -y remove sjgms > /dev/null 2>&1
apt -y install ./$TARGET_FILE

echo "CI Done"
exit 0
