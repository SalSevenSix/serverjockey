if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo."
  exit 1
fi
systemctl {args}
echo
exit 0
