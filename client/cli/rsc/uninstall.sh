SJGMS_USER="{userdef}"

if which apt > /dev/null; then
  apt -y remove $SJGMS_USER
  deluser --remove-home $SJGMS_USER
fi
if which yum > /dev/null; then
  yum -y remove $SJGMS_USER
  userdel --remove $SJGMS_USER
fi
rm -rf /home/$SJGMS_USER > /dev/null 2>&1

echo "uninstall done"
exit 0
