SJGMS_USER="{user}"
SERVICE_FILE="/etc/systemd/system/${SJGMS_USER}.service"

if [ -f $SERVICE_FILE ]; then
  echo "removing service"
  systemctl stop $SJGMS_USER > /dev/null 2>&1
  rm $SERVICE_FILE > /dev/null 2>&1
  systemctl daemon-reload
fi

if id -u $SJGMS_USER > /dev/null 2>&1; then
  echo "removing user"
  if command -v apt > /dev/null; then
    apt -y purge $SJGMS_USER
    deluser --remove-home $SJGMS_USER || userdel --remove $SJGMS_USER
  elif command -v dnf > /dev/null; then
    dnf -y remove $SJGMS_USER
    userdel --remove $SJGMS_USER
  elif command -v pacman > /dev/null; then
    pacman -Rsn --noconfirm $SJGMS_USER
    userdel --remove $SJGMS_USER
  fi
  groupdel $SJGMS_USER > /dev/null 2>&1
  rm -rf /home/$SJGMS_USER > /dev/null 2>&1
fi

echo "userdel done"
exit 0
