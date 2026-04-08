SJGMS_USER="{userdef}"

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

echo "uninstall done"
exit 0
