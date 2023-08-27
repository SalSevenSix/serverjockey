if [ "$(whoami)" != "root" ]; then
  echo "Not root user. Please run using sudo as follows..."
  echo "  sudo serverjockey_cmd.pyz -t upgrade"
  exit 1
fi

INSTALLER="apt"
PKGTYPE="deb"
if which yum > /dev/null 2>&1; then
  INSTALLER="yum"
  PKGTYPE="rpm"
fi

rm sjgms.${PKGTYPE} > /dev/null 2>&1
wget --version > /dev/null 2>&1 || ${INSTALLER} -y install wget
echo "downloading..."
wget -q -O sjgms.${PKGTYPE} https://4sas.short.gy/sjgms-${PKGTYPE}-latest
[ $? -eq 0 ] || exit 1
${INSTALLER} -y install ./sjgms.${PKGTYPE}
[ $? -eq 0 ] || exit 1
rm sjgms.${PKGTYPE} > /dev/null 2>&1

echo "upgrade done"
exit 0
