#!/bin/bash

BRANCH="${1-local}"
cd "$(dirname $0)" || exit 1
TIMESTAMP=$(date '+%Y%m%d%H%M')
BUILD_DIR="$(pwd)"
DIST_DIR="$BUILD_DIR/dist"
[ -d "$DIST_DIR" ] || mkdir $DIST_DIR
SERVERJOCKEY="serverjockey"
SERVERLINK="serverlink"
SERVERJOCKEY_DIR="$DIST_DIR/$SERVERJOCKEY"
SERVERLINK_DIR="$DIST_DIR/discord"
SERVERJOCKEY_CMD_DIR="$DIST_DIR/cli"
HAX_DIR="$DIST_DIR/hax"
TARGET_DIR="$DIST_DIR/sjgms"
LIB32_DIR="$SERVERJOCKEY_DIR/.venv/lib/python3.10/site-packages"
LIB64_DIR="$SERVERJOCKEY_DIR/.venv/lib64/python3.10/site-packages"
export PIPENV_VENV_IN_PROJECT=1
rm -rf "$SERVERJOCKEY_DIR" "$SERVERJOCKEY_CMD_DIR" "$SERVERLINK_DIR" "$HAX_DIR" "$TARGET_DIR" > /dev/null 2>&1

cd $DIST_DIR || exit 1
if [ "$BRANCH" == "local" ]; then
  echo "Copying local source files to build"
  cd ../.. || exit 1
  [ -d "build" ] || exit 1
  mkdir -p "$SERVERJOCKEY_DIR/build"
  find . -maxdepth 1 | while read file; do
    [[ $file == "." || $file == "./build" ]] || cp -r "$file" "$SERVERJOCKEY_DIR"
  done
  cd "build" || exit 1
  find . -maxdepth 1 | while read file; do
    [[ $file == "." || $file == "./dist" ]] || cp -r "$file" "$SERVERJOCKEY_DIR/build"
  done
  find "$SERVERJOCKEY_DIR" -type d -name "__pycache__" | while read file; do
    rm -rf $file
  done
else
  if [ ! -f "$BRANCH.zip" ]; then
    echo "Downloading zip from github"
    wget "https://github.com/SalSevenSix/$SERVERJOCKEY/archive/refs/heads/$BRANCH.zip"
    [ $? -eq 0 ] || exit 1
  fi
  [ -f "$BRANCH.zip" ] || exit 1
  echo "Unpacking zip"
  unzip "$BRANCH.zip" > /dev/null 2>&1
  [ $? -eq 0 ] || exit 1
  [ -d "${SERVERJOCKEY}-${BRANCH}" ] || exit 1
  mv "${SERVERJOCKEY}-${BRANCH}" "$SERVERJOCKEY"
  [ $? -eq 0 ] || exit 1
fi

cd $DIST_DIR || exit 1
if which yum > /dev/null; then
  echo "Updating RPM scripts"
  if [ $(diff "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh" | wc -l) -ne 0 ]; then
    cp "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh"
    echo "Build script updated. Please run again."
    exit 1
  fi
  cp "$SERVERJOCKEY_DIR/build/rpm.sh" "$BUILD_DIR/rpm.sh"
  chmod 755 $BUILD_DIR/rpm.sh
fi
rm "$BRANCH.zip" > /dev/null 2>&1

echo "Applying build timestamp"
sed -i -e "s/{timestamp}/${TIMESTAMP}/g" $SERVERJOCKEY_DIR/core/util/sysutil.py || exit 1
sed -i -e "s/{timestamp}/${TIMESTAMP}/g" $SERVERJOCKEY_DIR/client/discord/index.js || exit 1

echo "Copying target directory into build directory"
cp -r "$SERVERJOCKEY_DIR/build/packaging/sjgms" "$DIST_DIR"
[ $? -eq 0 ] || exit 1
[ -d "$TARGET_DIR" ] || exit 1
mkdir -p $TARGET_DIR/usr/local/bin
[ -d "$TARGET_DIR/usr/local/bin" ] || exit 1
mkdir -p $TARGET_DIR/etc/systemd/system
[ -d "$TARGET_DIR/etc/systemd/system" ] || exit 1

echo "Copying CLI and ServerLink into build directory"
cp -r "$SERVERJOCKEY_DIR/client/cli" "$SERVERJOCKEY_CMD_DIR"
[ $? -eq 0 ] || exit 1
[ -d "$SERVERJOCKEY_CMD_DIR" ] || exit 1
cp -r "$SERVERJOCKEY_DIR/client/discord" "$SERVERLINK_DIR"
[ $? -eq 0 ] || exit 1
[ -d "$SERVERLINK_DIR" ] || exit 1
cp -r "$SERVERJOCKEY_DIR/build/hax" "$HAX_DIR"
[ $? -eq 0 ] || exit 1
[ -d "$HAX_DIR" ] || exit 1

echo "Building web client"
$SERVERJOCKEY_DIR/client/web/build.sh
[ $? -eq 0 ] || exit 1
[ -d "$SERVERJOCKEY_DIR/web" ] || exit 1

echo "Downloading ServerJockey dependencies"
cd $SERVERJOCKEY_DIR || exit 1
pipenv install
[ $? -eq 0 ] || exit 1
[ -d ".venv" ] || exit 1

echo "Merging ServerJockey dependencies"
if [ -d "$LIB32_DIR" ]; then
  rm -rf "$LIB32_DIR/pip"* > /dev/null 2>&1
  cp -r $LIB32_DIR/* "$SERVERJOCKEY_DIR" || exit 1
fi
if [ -d "$LIB64_DIR" ]; then
  rm -rf "$LIB64_DIR/pip"* > /dev/null 2>&1
  cp -r $LIB64_DIR/* "$SERVERJOCKEY_DIR" || exit 1
fi

echo "Running tests"
python3.10 -m unittest discover -t . -s test -p *.py
[ $? -eq 0 ] || exit 1

echo "Removing ServerJockey junk"
rm -rf .venv venv build client test *.sh *.text .git .gitignore .idea > /dev/null 2>&1

echo "Building ServerJockey zipapp"
cd $DIST_DIR || exit 1
python3.10 -m zipapp $SERVERJOCKEY -p "/usr/bin/env python3.10" -m "core.system.__main__:main" -c -o "$TARGET_DIR/usr/local/bin/$SERVERJOCKEY.pyz"
[ $? -eq 0 ] || exit 1
[ -f "$TARGET_DIR/usr/local/bin/$SERVERJOCKEY.pyz" ] || exit 1

echo "Building ServerJockey CLI zipapp"
python3.10 -m zipapp "cli" -p "/usr/bin/env python3.10" -m "serverjockey_cmd:main" -c -o "$TARGET_DIR/usr/local/bin/${SERVERJOCKEY}_cmd.pyz"
[ $? -eq 0 ] || exit 1
[ -f "$TARGET_DIR/usr/local/bin/${SERVERJOCKEY}_cmd.pyz" ] || exit 1

echo "Generating systemd service file"
$TARGET_DIR/usr/local/bin/${SERVERJOCKEY}_cmd.pyz -nt ctrld > $TARGET_DIR/etc/systemd/system/serverjockey.service
[ $? -eq 0 ] || exit 1
[ -f "$TARGET_DIR/etc/systemd/system/serverjockey.service" ] || exit 1

echo "Downloading ServerLink dependencies"
cd $SERVERLINK_DIR || exit 1
npm ci
[ $? -eq 0 ] || exit 1
[ -d "$SERVERLINK_DIR/node_modules" ] || exit 1
cp "$HAX_DIR/index.js" "$SERVERLINK_DIR/node_modules/@discordjs/rest/dist/index.js"

echo "Building ServerLink nexe"
nexe index.js --output "$TARGET_DIR/usr/local/bin/$SERVERLINK" --build --python=$(which python3.10)
[ $? -eq 0 ] || exit 1
[ -f "$TARGET_DIR/usr/local/bin/$SERVERLINK" ] || exit 1

echo "Cleanup"
rm -rf "$SERVERJOCKEY_DIR" "$SERVERJOCKEY_CMD_DIR" "$SERVERLINK_DIR" "$HAX_DIR" > /dev/null 2>&1

echo "Done"
exit 0
