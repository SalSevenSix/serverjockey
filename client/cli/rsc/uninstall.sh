systemctl stop serverjockey > /dev/null 2>&1
which apt > /dev/null 2>&1 && apt -y remove {userdef}
which yum > /dev/null 2>&1 && yum -y remove {userdef}
systemctl daemon-reload
if id -u {userdef} > /dev/null 2>&1; then
  userdel {userdef}
  rm -rf /home/{userdef} > /dev/null 2>&1
fi

echo "uninstall done"
exit 0
