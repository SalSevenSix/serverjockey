if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -t uninstall"
  exit 1
fi

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
