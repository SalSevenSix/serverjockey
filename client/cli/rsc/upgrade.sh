PKGTYPE="deb"
INSTALL_PKG="apt -y install"
INSTALL_FILE="apt -y install"
if command -v dnf > /dev/null; then
  PKGTYPE="rpm"
  INSTALL_PKG="dnf -y install"
  INSTALL_FILE="dnf -y install"
elif command -v pacman > /dev/null; then
  PKGTYPE="pkg.tar.zst"
  INSTALL_PKG="pacman -Syu --noconfirm"
  INSTALL_FILE="pacman -U --noconfirm"
fi

rm sjgms.${PKGTYPE} > /dev/null 2>&1
command -v wget > /dev/null || ${INSTALL_PKG} wget
echo "downloading package"
wget -q -O sjgms.${PKGTYPE} https://dl.serverjockey.net/sjgms-master-latest.${PKGTYPE} || exit 1
${INSTALL_FILE} ./sjgms.${PKGTYPE} || exit 1
rm sjgms.${PKGTYPE} > /dev/null 2>&1

echo "upgrade done"
exit 0
