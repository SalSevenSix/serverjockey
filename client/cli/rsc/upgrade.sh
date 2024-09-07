OSVER="ub$(grep 'VERSION_ID=' /etc/os-release | tr '"' ' ' | tr '.' ' ' | awk '{print $2}')"
INSTALLER="apt"
PKGTYPE="deb"
if which yum > /dev/null 2>&1; then
  INSTALLER="yum"
  PKGTYPE="rpm"
fi

rm sjgms.${PKGTYPE} > /dev/null 2>&1
wget --version > /dev/null 2>&1 || ${INSTALLER} -y install wget
echo "downloading package for OS ${OSVER}"
wget -q -O sjgms.${PKGTYPE} https://serverjockey.net/downloads/sjgms-master-latest-${OSVER}.${PKGTYPE} || exit 1
${INSTALLER} -y install ./sjgms.${PKGTYPE} || exit 1
rm sjgms.${PKGTYPE} > /dev/null 2>&1

echo "upgrade done"
exit 0
