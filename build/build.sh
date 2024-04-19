#!/bin/bash

[ $(python3 --version | grep "Python 3\.10\." | wc -l) -eq 0 ] && exit 1
BRANCH="${1-local}"
TIMESTAMP=$(date '+%Y%m%d%H%M')
cd "$(dirname $0)" || exit 1
BUILD_DIR="$(pwd)"
DIST_DIR="$BUILD_DIR/dist"
[ -d "$DIST_DIR" ] || mkdir $DIST_DIR
SERVERJOCKEY="serverjockey"
SERVERJOCKEY_DIR="$DIST_DIR/$SERVERJOCKEY"
TARGET_DIR="$DIST_DIR/sjgms"
TARGET_BIN_DIR="$TARGET_DIR/usr/local/bin"
LIB32_DIR="$SERVERJOCKEY_DIR/.venv/lib/python3.10/site-packages"
LIB64_DIR="$SERVERJOCKEY_DIR/.venv/lib64/python3.10/site-packages"
export PIPENV_VENV_IN_PROJECT=1
rm -rf "$SERVERJOCKEY_DIR" "$TARGET_DIR" > /dev/null 2>&1

cd $DIST_DIR || exit 1
if [ "$BRANCH" = "local" ]; then
  echo "Copying local source files to build"
  cd ../.. || exit 1
  [ -d "build" ] || exit 1
  mkdir -p "$SERVERJOCKEY_DIR/build" || exit 1
  find . -maxdepth 1 | while read file; do
    [[ $file == "." || $file == "./build" ]] || cp -r "$file" "$SERVERJOCKEY_DIR"
  done
  cd "build" || exit 1
  find . -maxdepth 1 | while read file; do
    [[ $file == "." || $file == "./dist" ]] || cp -r "$file" "$SERVERJOCKEY_DIR/build"
  done
else
  if [ ! -f "$BRANCH.zip" ]; then
    echo "Downloading zip from github"
    wget "https://github.com/SalSevenSix/$SERVERJOCKEY/archive/refs/heads/$BRANCH.zip" || exit 1
  fi
  [ -f "$BRANCH.zip" ] || exit 1
  echo "Unpacking zip"
  unzip "$BRANCH.zip" > /dev/null || exit 1
  [ -d "${SERVERJOCKEY}-${BRANCH}" ] || exit 1
  mv "${SERVERJOCKEY}-${BRANCH}" "$SERVERJOCKEY" || exit 1
fi

cd $DIST_DIR || exit 1
if [ ! -d "../../.git" ]; then
  if which apt > /dev/null; then
    echo "Updating DEB scripts"
    if [ $(diff "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh" | wc -l) -ne 0 ]; then
      cp "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh"
      echo "Build script updated. Please run again."
      exit 1
    fi
    cp "$SERVERJOCKEY_DIR/build/deb.sh" "$BUILD_DIR/deb.sh"
    chmod 755 $BUILD_DIR/deb.sh || exit 1
  fi
  if which yum > /dev/null; then
    echo "Updating RPM scripts"
    if [ $(diff "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh" | wc -l) -ne 0 ]; then
      cp "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh"
      echo "Build script updated. Please run again."
      exit 1
    fi
    cp "$SERVERJOCKEY_DIR/build/rpm.sh" "$BUILD_DIR/rpm.sh"
    chmod 755 $BUILD_DIR/rpm.sh || exit 1
  fi
fi

echo "Delete source zip"
rm "$BRANCH.zip" > /dev/null 2>&1

echo "Applying build timestamp"
sed -i -e "s/{timestamp}/${TIMESTAMP}/g" $SERVERJOCKEY_DIR/core/util/sysutil.py || exit 1
sed -i -e "s/{timestamp}/${TIMESTAMP}/g" $SERVERJOCKEY_DIR/client/discord/index.js || exit 1

echo "Prepare build directory"
cp -r "$SERVERJOCKEY_DIR/build/packaging/sjgms" "$DIST_DIR" || exit 1
mkdir -p $TARGET_BIN_DIR || exit 1

echo "Building cli client"
$SERVERJOCKEY_DIR/client/cli/build.sh $TARGET_BIN_DIR/${SERVERJOCKEY}_cmd.pyz || exit 1

echo "Building discord client"
$SERVERJOCKEY_DIR/client/discord/build.sh ci $TARGET_BIN_DIR/serverlink || exit 1

echo "Building web client"
$SERVERJOCKEY_DIR/client/web/build.sh ci || exit 1

echo "Building extension client"
$SERVERJOCKEY_DIR/client/extension/build.sh ci || exit 1

echo "Download and merge ServerJockey dependencies"
cd $SERVERJOCKEY_DIR || exit 1
python3 -m pipenv sync || exit 1
[ -d ".venv" ] || exit 1
if [ -d "$LIB32_DIR" ]; then
  rm -rf $LIB32_DIR/pip* $LIB32_DIR/test* $LIB32_DIR/wheel* $LIB32_DIR/greenlet* > /dev/null 2>&1
  rm -rf $LIB32_DIR/setuptools* $LIB32_DIR/pkg_resources* $LIB32_DIR/_distutils_hack > /dev/null 2>&1
  cp -r $LIB32_DIR/* "$SERVERJOCKEY_DIR" || exit 1
fi
if [ -d "$LIB64_DIR" ]; then
  rm -rf $LIB64_DIR/pip* $LIB64_DIR/test* $LIB64_DIR/wheel* $LIB64_DIR/greenlet* > /dev/null 2>&1
  rm -rf $LIB64_DIR/setuptools* $LIB64_DIR/pkg_resources* $LIB64_DIR/_distutils_hack > /dev/null 2>&1
  cp -r $LIB64_DIR/* "$SERVERJOCKEY_DIR" || exit 1
fi

echo "Running tests"
python3 -m unittest discover -t . -s test -p "*.py" || exit 1

echo "Removing ServerJockey junk"
rm -rf .venv venv build client test *.sh *.text .git .gitignore .idea > /dev/null 2>&1
find . -name "__pycache__" -type d | while read file; do
  rm -rf $file > /dev/null 2>&1
done

echo "Building ServerJockey zipapp"
cd $DIST_DIR || exit 1
python3 -m zipapp $SERVERJOCKEY -p "/usr/bin/env python3" -m "core.system.__main__:main" -c -o "$TARGET_BIN_DIR/$SERVERJOCKEY.pyz" || exit 1

echo "Finishing"
rm -rf "$SERVERJOCKEY_DIR" > /dev/null 2>&1
echo $TIMESTAMP > "$TARGET_DIR/build.ok"

echo "Done"
exit 0
