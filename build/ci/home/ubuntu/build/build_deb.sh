#!/bin/bash

echo "Initialising CI build process"
[ "$(whoami)" = "root" ] || exit 1
which wget > /dev/null || exit 1
which jq > /dev/null || exit 1
which gh > /dev/null || exit 1
cd "$(dirname $0)" || exit 1
BUILD_DIR="$(pwd)"
BUILD_USER="$(pwd | tr '/' ' ' | awk '{print $2}')"
DIST_DIR="$BUILD_DIR/dist"
CI_OK_FILE="$BUILD_DIR/build_deb.ok"
WEB_DIR="/var/www/downloads"
[ -d "$WEB_DIR" ] || exit 1
BRANCH="develop"
REPO_URL="https://raw.githubusercontent.com/SalSevenSix/serverjockey/$BRANCH"
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

echo "CI Preparing"
rm $CI_OK_FILE > /dev/null 2>&1
echo $CURRENT_URL > $COMMIT_FILE
chown $BUILD_USER $COMMIT_FILE || exit 1
chgrp $BUILD_USER $COMMIT_FILE || exit 1

echo "CI Starting"
systemctl stop serverjockey > /dev/null 2>&1
rm build.sh > /dev/null 2>&1
wget -O build.sh $REPO_URL/build/build.sh || exit 1
chmod 755 build.sh || exit 1
chown $BUILD_USER build.sh || exit 1
chgrp $BUILD_USER build.sh || exit 1

echo "CI Building"
su - $BUILD_USER -c "$BUILD_DIR/build.sh $BRANCH"
BUILD_OK_FILE="$DIST_DIR/sjgms/build.ok"
[ -f "$BUILD_OK_FILE" ] || exit 1
TIMESTAMP="$(head -1 $BUILD_OK_FILE)"

echo "CI Packaging"
$BUILD_DIR/deb.sh || exit 1

echo "CI Publishing"
cd $DIST_DIR || exit 1
DEB_FILE="$(ls *.deb | tail -1)"
TARGET_FILE="sjgms-${BRANCH}-${TIMESTAMP}.deb"
chown root $DEB_FILE || exit 1
chgrp root $DEB_FILE || exit 1
mv $DEB_FILE $WEB_DIR/$TARGET_FILE || exit 1
cd $WEB_DIR || exit 1
ln -fs "$TARGET_FILE" "sjgms-${BRANCH}-latest.deb" || exit 1

echo "CI Cleanup"
rm -rf "$DIST_DIR" > /dev/null 2>&1
KEEP_COUNT=6
ls -t sjgms-${BRANCH}-*.deb | while read file; do
  [ $KEEP_COUNT -gt 0 ] || rm $file
  ((KEEP_COUNT = KEEP_COUNT - 1))
done

echo "CI Docker"
cd $BUILD_DIR || exit 1
rm -rf docker > /dev/null 2>&1
mkdir docker || exit 1
cd docker || exit 1
cp $WEB_DIR/$TARGET_FILE sjgms.deb || exit 1
wget -O Dockerfile $REPO_URL/build/docker/Dockerfile || exit 1
wget -O entrypoint.sh $REPO_URL/build/docker/entrypoint.sh || exit 1
wget -O build.sh $REPO_URL/build/docker/build.sh || exit 1
chmod 755 build.sh || exit 1
./build.sh $BRANCH || exit 1

echo "CI Upgrade"
cd $WEB_DIR || exit 1
apt -y remove sjgms || exit 1
apt -y install ./$TARGET_FILE || exit 1

echo "CI Finishing"
cd $BUILD_DIR || exit 1
echo $TIMESTAMP > $CI_OK_FILE
sleep 20
/usr/local/bin/serverjockey_cmd.pyz -c emailtoken

echo "CI Done build process"
exit 0
