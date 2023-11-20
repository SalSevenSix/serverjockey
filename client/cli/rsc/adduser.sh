SJGMS_USER_DEF="{userdef}"
SJGMS_USER="{user}"
SJGMS_PORT="{port}"
HOME_DIR="/home/$SJGMS_USER"
SERVERLINK_DIR="$HOME_DIR/serverlink"
SERVICE_NAME="$SJGMS_USER"
[ "$SJGMS_USER" = "$SJGMS_USER_DEF" ] && SERVICE_NAME="serverjockey"
id -u $SJGMS_USER_DEF > /dev/null 2>&1 || SERVICE_NAME="serverjockey"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

id -u $SJGMS_USER > /dev/null 2>&1
if [ $? -ne 0 ]; then
  rm -rf $HOME_DIR > /dev/null 2>&1
  adduser --system $SJGMS_USER || exit 1
  mkdir -p $SERVERLINK_DIR
  echo '{ "module": "serverlink", "hidden": true }' > $SERVERLINK_DIR/instance.json
  find $HOME_DIR -type d -exec chmod 755 {} +
  find $HOME_DIR -type f -exec chmod 600 {} +
  chown -R $SJGMS_USER $HOME_DIR
  chgrp -R $(ls -ld $HOME_DIR | awk '{print $4}') $HOME_DIR
fi

[ -f $SERVICE_FILE ] || /usr/local/bin/serverjockey_cmd.pyz -nt sysdsvc:$SJGMS_USER,$SJGMS_PORT > $SERVICE_FILE
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo "adduser done"
exit 0
