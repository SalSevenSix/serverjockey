#!/bin/bash

if [ "$(whoami)" != "root" ]; then
  echo "Script needs to run with root privileges."
  exit 1
fi
if [ $# -ne 2 ]; then
  echo "User name and port required."
  echo "> new_user.sh [username] [port]"
  exit 1
fi

SJGMS_USER=$1
PORT=$2
HOME_DIR="/home/$SJGMS_USER"
SERVERLINK_DIR="$HOME_DIR/serverlink"

id -u $SJGMS_USER > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "User $SJGMS_USER already exists."
  exit 1
fi
if [ -d "$HOME_DIR" ]; then
  echo "Directory $HOME_DIR already exists."
  exit 1
fi

echo "1. Creating $SJGMS_USER.service file"
{
  echo "[Unit]"
  echo "Description=ServerJockey game server management system ($SJGMS_USER)"
  echo "Requires=network.target"
  echo "After=network.target"
  echo
  echo "[Service]"
  echo "Type=simple"
  echo "User=$SJGMS_USER"
  echo "ExecStart=/usr/local/bin/serverjockey.pyz --home \"/home/$SJGMS_USER\" --logfile \"serverjockey.log\" --port $PORT"
  echo "KillMode=mixed"
  echo "TimeoutStopSec=90"
  echo "OOMScoreAdjust=-800"
  echo
  echo "[Install]"
  echo "WantedBy=multi-user.target"
} > /etc/systemd/system/$SJGMS_USER.service

echo "2. Creating user $SJGMS_USER"
adduser --system $SJGMS_USER
[ $? -eq 0 ] || exit 1

echo "3. Setup home directory"
mkdir -p $SERVERLINK_DIR
echo "{ \"module\": \"serverlink\", \"auto\": \"daemon\", \"hidden\": true }" > $SERVERLINK_DIR/instance.json
{
  echo "{"
  echo "  \"CMD_PREFIX\": \"!\","
  echo "  \"ADMIN_ROLE\": \"pzadmin\","
  echo "  \"BOT_TOKEN\": null,"
  echo "  \"EVENTS_CHANNEL_ID\": null,"
  echo "  \"WHITELIST_DM\": \"Welcome to our server.\nYour login is \${user} and password is \${pass}\""
  echo "}"
} > $SERVERLINK_DIR/serverlink.json

echo "4. Applying file attributes"
find $HOME_DIR -type d -exec chmod 755 {} +
find $HOME_DIR -type f -exec chmod 600 {} +
chown -R $SJGMS_USER $HOME_DIR
chgrp -R nogroup $HOME_DIR

echo "5. Installing SteamCMD for user"
runuser - $SJGMS_USER -s /bin/bash -c "steamcmd +quit"
[ -d "$HOME_DIR/.steam" ] || exit 1

echo "6. Starting $SJGMS_USER service"
systemctl daemon-reload
systemctl enable $SJGMS_USER
systemctl start $SJGMS_USER

exit 0
