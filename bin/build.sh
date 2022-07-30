#!/bin/bash

BRANCH="${1-master}"
HOME_DIR="$(pwd)"
START_SH="start.sh"
NATIVES_ZIP="natives.zip"
[ -f $START_SH ] && echo "Not building here!" && exit 1
SERVERJOCKEY="serverjockey"
[ -d $SERVERJOCKEY ] && echo "Not building here!" && exit 1
SERVERLINK="serverlink"
SERVERJOCKEY_DIR="$HOME_DIR/$SERVERJOCKEY"
SERVERLINK_DIR="$HOME_DIR/discord"
SERVERLINK_TRG="$HOME_DIR/$SERVERLINK"
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

echo "Copying start script into build directory"
cp "$SERVERJOCKEY_DIR/$START_SH" "$HOME_DIR/$START_SH"
[ $? -eq 0 ] || exit 1

echo "Copying Serverlink into build directory"
cp -r "$SERVERJOCKEY_DIR/client/discord" "$SERVERLINK_DIR"
[ $? -eq 0 ] || exit 1
[ -d "$SERVERLINK_DIR" ] || exit 1

echo "Building web client"
$SERVERJOCKEY_DIR/client/web/build.sh
[ $? -eq 0 ] || exit 1

echo "Downloading ServerJockey dependencies"
cd $SERVERJOCKEY_DIR || exit 1
pipenv install
[ $? -eq 0 ] || exit 1
[ -d ".venv" ] || exit 1

echo "Merging ServerJockey dependencies"
cp -r $SERVERJOCKEY_DIR/.venv/lib/python3.10/site-packages/* "$SERVERJOCKEY_DIR"
[ $? -eq 0 ] || exit 1

echo "Building natives zip"
mkdir $HOME_DIR/natives
mv psutil* $HOME_DIR/natives
cd $HOME_DIR/natives || exit 1
zip -r "$HOME_DIR/$NATIVES_ZIP" * > /dev/null 2>&1
cd $SERVERJOCKEY_DIR || exit 1
rm -rf $HOME_DIR/natives > /dev/null 2>&1

echo "Removing ServerJockey junk"
rm -rf .venv venv bin client test *.sh README.md .gitignore > /dev/null 2>&1

echo "Building ServerJockey zipapp"
cd $HOME_DIR || exit 1
python3 -m zipapp $SERVERJOCKEY -p "/usr/bin/env python3" -m "core.system.bootstrap:main" -c -o $SERVERJOCKEY.pyz
[ $? -eq 0 ] || exit 1

echo "Preparing ServerLink target"
mkdir $SERVERLINK_TRG || exit 1
echo "{ \"module\": \"serverlink\", \"auto\": \"daemon\", \"hidden\": true }" > $SERVERLINK_TRG/instance.json

echo "Downloading Serverlink dependencies"
cd $SERVERLINK_DIR || exit 1
rm -rf test* > /dev/null 2>&1
npm ci
[ $? -eq 0 ] || exit 1
[ -d "$SERVERLINK_DIR/node_modules" ] || exit 1

echo "Building Serverlink nexe"
nexe index.js --output "$SERVERLINK_TRG/$SERVERLINK" --build --python=$(which python3)
[ $? -eq 0 ] || exit 1

echo "Packaging"
cd $HOME_DIR || exit 1
chmod 744 $HOME_DIR/$SERVERJOCKEY.pyz $SERVERLINK_TRG/$SERVERLINK $HOME_DIR/$START_SH
[ $? -eq 0 ] || exit 1
zip -r "sjms-$BRANCH-$(date +%Y%m%d%H%M%S).zip" $SERVERJOCKEY.pyz $NATIVES_ZIP $SERVERLINK $START_SH > /dev/null 2>&1
[ $? -eq 0 ] || exit 1

echo "Cleanup"
rm -rf $SERVERLINK_DIR $SERVERJOCKEY_DIR $SERVERLINK_TRG $SERVERJOCKEY.pyz $NATIVES_ZIP $START_SH > /dev/null 2>&1

echo "Done"
exit 0
