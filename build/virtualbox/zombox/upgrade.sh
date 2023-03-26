#!/bin/bash

if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run as follows..."
  echo "  sudo ./upgrade.sh"
  exit 1
fi

echo "Upgrading ServerJockey"
rm sjgms.deb > /dev/null 2>&1
wget -O sjgms.deb https://4sas.short.gy/sjgms-deb-latest
[ $? -eq 0 ] || exit 1
[ -f sjgms.deb ] || exit 1
apt install ./sjgms.deb
[ $? -eq 0 ] || exit 1
rm sjgms.deb > /dev/null 2>&1
echo "Upgrade complete"

exit 0