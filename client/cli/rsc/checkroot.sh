[ "$(whoami)" = "root" ] && exit 0
echo "Not root user. Please run using sudo as follows..."
echo "  sudo serverjockey_cmd.pyz -t {args}"
exit 1
