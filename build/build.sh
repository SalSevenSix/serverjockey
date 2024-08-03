#!/bin/bash

echo "Initialising build process"
PYTHON_LIBDIR="python3.12"
[ $(python3 --version | grep "Python 3\.12\." | wc -l) -eq 0 ] && exit 1
python3 -m pipenv --version > /dev/null || exit 1
which wget > /dev/null || exit 1
which unzip > /dev/null || exit 1
cd "$(dirname $0)" || exit 1
BRANCH="${1-local}"
BUILD_DIR="$(pwd)"
TIMESTAMP=$(date '+%Y%m%d%H%M')
DIST_DIR="$BUILD_DIR/dist"
[ -d "$DIST_DIR" ] || mkdir $DIST_DIR
SERVERJOCKEY="serverjockey"
SERVERJOCKEY_DIR="$DIST_DIR/$SERVERJOCKEY"
TARGET_DIR="$DIST_DIR/sjgms"
TARGET_BIN_DIR="$TARGET_DIR/usr/local/bin"
export PIPENV_VENV_IN_PROJECT=1
rm -rf "$SERVERJOCKEY_DIR" "$TARGET_DIR" > /dev/null 2>&1

cd $DIST_DIR || exit 1
if [ "$BRANCH" = "local" ]; then
  echo "Copying local source files to build"
  cd ../.. || exit 1
  [ -d "build" ] || exit 1
  mkdir -p "$SERVERJOCKEY_DIR/build" || exit 1
  find . -maxdepth 1 | while read file; do
    [[ $file == "." || $file == "./build" || $file == "./venv" ]] || cp -r "$file" "$SERVERJOCKEY_DIR"
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
  echo "Updating build scripts"
  if [ $(diff "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh" | wc -l) -ne 0 ]; then
    cp "$SERVERJOCKEY_DIR/build/build.sh" "$BUILD_DIR/build.sh"
    echo "Build script updated. Please run again."
    exit 1
  fi
  if which apt > /dev/null; then
    cp "$SERVERJOCKEY_DIR/build/deb.sh" "$BUILD_DIR/deb.sh"
    chmod 755 $BUILD_DIR/deb.sh || exit 1
  fi
  if which yum > /dev/null; then
    cp "$SERVERJOCKEY_DIR/build/rpm.sh" "$BUILD_DIR/rpm.sh"
    chmod 755 $BUILD_DIR/rpm.sh || exit 1
  fi
fi
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

echo "Download ServerJockey dependencies"
cd $SERVERJOCKEY_DIR || exit 1
python3 -m pipenv sync || exit 1
for VENV_LIBDIR in lib lib64; do
  LIBDIR="$SERVERJOCKEY_DIR/.venv/$VENV_LIBDIR/$PYTHON_LIBDIR/site-packages"
  if [ -d "$LIBDIR" ]; then
    rm -rf $LIBDIR/pip* $LIBDIR/test* $LIBDIR/wheel* $LIBDIR/greenlet* > /dev/null 2>&1
    rm -rf $LIBDIR/setuptools* $LIBDIR/pkg_resources* $LIBDIR/_distutils_hack > /dev/null 2>&1
    echo "Merging $LIBDIR"
    cp -r $LIBDIR/* "$SERVERJOCKEY_DIR" || exit 1
  fi
done

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

echo "Done build process"
exit 0
