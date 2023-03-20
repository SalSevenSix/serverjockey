#!/bin/bash

BRANCH="${1-local}"
HOME_DIR="$(pwd)"
[ -f "start.sh" ] && echo "Not building here!" && exit 1
SERVERJOCKEY="serverjockey"
[ -d $SERVERJOCKEY ] && echo "Not building here!" && exit 1
TARGET_DIR="$HOME_DIR/sjgms"
SERVERLINK="serverlink"
SERVERJOCKEY_DIR="$HOME_DIR/$SERVERJOCKEY"
SERVERLINK_DIR="$HOME_DIR/discord"
LIB32_DIR="$SERVERJOCKEY_DIR/.venv/lib/python3.10/site-packages"
LIB64_DIR="$SERVERJOCKEY_DIR/.venv/lib64/python3.10/site-packages"
export PIPENV_VENV_IN_PROJECT=1

cd $HOME_DIR || exit 1
if [ "$BRANCH" == "local" ]; then
  echo "Copying local source files to build"
  cp -r ~/projects/$SERVERJOCKEY $SERVERJOCKEY
  [ -d "$SERVERJOCKEY" ] || exit 1
else
  echo "Downloading zip from github"
  wget "https://github.com/SalSevenSix/$SERVERJOCKEY/archive/refs/heads/$BRANCH.zip"
  [ $? -eq 0 ] || exit 1
  echo "Unpacking zip"
  unzip "$BRANCH.zip" > /dev/null 2>&1
  [ $? -eq 0 ] || exit 1
  mv "$SERVERJOCKEY-$BRANCH" "$SERVERJOCKEY"
  [ $? -eq 0 ] || exit 1
  rm "$BRANCH.zip" > /dev/null 2>&1
fi

if [ -d "$HOME/rpmbuild" ]; then
  echo "Updating Fedora scripts and spec file"
  if [ $(diff $SERVERJOCKEY_DIR/bin/build.sh $HOME_DIR/build.sh | wc -l) -ne 0 ]; then
    cp "$SERVERJOCKEY_DIR/bin/build.sh" "$HOME_DIR/build.sh"
    rm -rf $SERVERJOCKEY_DIR > /dev/null 2>&1
    echo "Build script updated. Please run again."
    exit 1
  fi
  cp "$SERVERJOCKEY_DIR/bin/rpm.sh" "$HOME_DIR/rpm.sh"
  cp "$SERVERJOCKEY_DIR/bin/packaging/rpmbuild/SPECS/sjgms.spec" "$HOME/rpmbuild/SPECS/sjgms.spec"
fi

echo "Copying target directory into build directory"
cp -r "$SERVERJOCKEY_DIR/bin/packaging/sjgms" "$HOME_DIR"
[ $? -eq 0 ] || exit 1
[ -d "$TARGET_DIR" ] || exit 1
find $TARGET_DIR -type f -name ".deleteme" -delete
[ $? -eq 0 ] || exit 1

echo "Copying ServerLink into build directory"
cp -r "$SERVERJOCKEY_DIR/client/discord" "$SERVERLINK_DIR"
[ $? -eq 0 ] || exit 1
[ -d "$SERVERLINK_DIR" ] || exit 1

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
  cp -r $LIB32_DIR/* "$SERVERJOCKEY_DIR" || exit 1
fi
if [ -d "$LIB64_DIR" ]; then
  cp -r $LIB64_DIR/* "$SERVERJOCKEY_DIR" || exit 1
fi

echo "Running tests"
python3.10 -m test > /dev/null
[ $? -eq 0 ] || exit 1

echo "Removing ServerJockey junk"
rm -rf .venv venv bin client test *.sh *.text .git .gitignore .idea > /dev/null 2>&1

echo "Building ServerJockey zipapp"
cd $HOME_DIR || exit 1
python3.10 -m zipapp $SERVERJOCKEY -p "/usr/bin/env python3.10" -m "core.system.bootstrap:main" -c -o "$TARGET_DIR/usr/local/bin/$SERVERJOCKEY.pyz"
[ $? -eq 0 ] || exit 1
[ -f "$TARGET_DIR/usr/local/bin/$SERVERJOCKEY.pyz" ] || exit 1

echo "Downloading ServerLink dependencies"
cd $SERVERLINK_DIR || exit 1
rm -rf test* > /dev/null 2>&1
npm ci
[ $? -eq 0 ] || exit 1
[ -d "$SERVERLINK_DIR/node_modules" ] || exit 1

echo "Building Serverlink nexe"
nexe index.js --output "$TARGET_DIR/usr/local/bin/$SERVERLINK" --build --python=$(which python3.10)
[ $? -eq 0 ] || exit 1
[ -f "$TARGET_DIR/usr/local/bin/$SERVERLINK" ] || exit 1

echo "Cleanup"
rm -rf $SERVERLINK_DIR $SERVERJOCKEY_DIR > /dev/null 2>&1

echo "Done"
exit 0
