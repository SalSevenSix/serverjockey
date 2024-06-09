if which apt > /dev/null; then
  apt -y remove {userdef}
  deluser --remove-home {userdef}
fi
if which yum > /dev/null; then
  yum -y remove {userdef}
  userdel --remove {userdef}
fi
rm -rf /home/{userdef} > /dev/null 2>&1

echo "uninstall done"
exit 0
