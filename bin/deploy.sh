#!/bin/bash

PACKAGE="$1"
TARGET="steam@10.1.1.28"

scp $PACKAGE $TARGET:$PACKAGE
ssh $TARGET << EOF
cd /home/steam
rm -rf tmp
mkdir tmp
cd tmp
unzip ../$PACKAGE
rm /home/steam/$PACKAGE
cd /home/steam/serverjockey/serverlink
rm serverlink *.json *.log
mv /home/steam/tmp/serverlink/instance.json .
mv /home/steam/tmp/serverlink/serverlink .
cd ..
rm serverjockey.pyz *.sh *.log *.ok
mv /home/steam/tmp/start.sh .
mv /home/steam/tmp/serverjockey.pyz .
./start.sh
cd /home/steam
rm -rf tmp
EOF

exit 0
