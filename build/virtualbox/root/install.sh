#!/bin/bash

echo "Initialising install process"
[ "$(whoami)" = "root" ] || exit 1
which wget > /dev/null || exit 1
DEB_URL="https://serverjockey.net/downloads/${1}"
DEB_FILE="sjgms.deb"
SJGMS_LOG="serverjockey.log"
SJGMS_HOME="/home/sjgms"
[ -d $SJGMS_HOME ] && exit 1
[ -f /usr/local/bin/serverjockey.pyz ] && exit 1
id -u sjgms > /dev/null 2>&1 && exit 1

echo "Download and install deb package"
cd /tmp || exit 1
rm $DEB_FILE > /dev/null 2>&1
wget -q -O $DEB_FILE $DEB_URL || exit 1
apt -y install ./$DEB_FILE || exit 1
cd $SJGMS_HOME || exit 1

echo "Waiting for ServerJockey log file"
LOOP_RETRY=3
until [ -f $SJGMS_LOG ]; do
  echo " retry $LOOP_RETRY"
  [ $LOOP_RETRY -eq 0 ] && exit 1
  sleep 10 && ((LOOP_RETRY = LOOP_RETRY - 1))
done

echo "Waiting for SteamCMD install complete"
LOOP_RETRY=6
until grep "SteamCMD install completed" $SJGMS_LOG > /dev/null; do
  echo " retry $LOOP_RETRY"
  [ $LOOP_RETRY -eq 0 ] && exit 1
  sleep 10 && ((LOOP_RETRY = LOOP_RETRY - 1))
done

echo "Waiting for UPnP discovery completed"
LOOP_RETRY=15
until grep -E "No IGD port mapping service found|Found port mapping service" $SJGMS_LOG > /dev/null; do
  echo " retry $LOOP_RETRY"
  [ $LOOP_RETRY -eq 0 ] && exit 1
  sleep 10 && ((LOOP_RETRY = LOOP_RETRY - 1))
done

echo "Shutdown ServerJockey service"
systemctl stop serverjockey || exit 1
sleep 1

echo "Cleanup"
rm /tmp/$DEB_FILE
rm -rf .tmp .pid serverjockey*
rm -rf serverlink/serverlink.*
apt clean
apt autoclean
apt -y autoremove --purge
journalctl --rotate && journalctl --vacuum-time=1s

echo "Done"
echo " now reboot"
echo " then esc esc esc, recovery root terminal, zerofree"
exit 0
