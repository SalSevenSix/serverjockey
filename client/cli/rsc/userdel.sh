SJGMS_USER="{user}"
SERVICE_FILE="/etc/systemd/system/$SJGMS_USER.service"

if [ -f $SERVICE_FILE ]; then
  echo "removing service"
  systemctl stop $SJGMS_USER > /dev/null 2>&1
  rm $SERVICE_FILE > /dev/null 2>&1
  systemctl daemon-reload
fi

if id -u $SJGMS_USER > /dev/null 2>&1; then
  echo "removing user"
  userdel $SJGMS_USER
  rm -rf /home/$SJGMS_USER > /dev/null 2>&1
fi

echo "userdel done"
exit 0
