%define __strip /bin/true

Name:           sjgms
Version:        0.0.6
Release:        1%{?dist}
Summary:        ServerJockey Game Management System
BuildArch:      x86_64
License:        Proprietary
Source0:        %{name}-%{version}.tar.gz
URL:            https://github.com/SalSevenSix/serverjockey
Requires:       python3


%description
ServerJockey Game Management System


%prep
%setup -q


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/local/bin
cp serverjockey.pyz $RPM_BUILD_ROOT/usr/local/bin
cp serverlink $RPM_BUILD_ROOT/usr/local/bin
mkdir -p $RPM_BUILD_ROOT/usr/lib/python3.10/site-packages
cp -r psutil* $RPM_BUILD_ROOT/usr/lib/python3.10/site-packages
mkdir -p $RPM_BUILD_ROOT/etc/systemd/system
cp serverjockey.service $RPM_BUILD_ROOT/etc/systemd/system


%files
%defattr(755,root,root)
/usr/local/bin/serverjockey.pyz
/usr/local/bin/serverlink
%defattr(644,root,root)
/etc/systemd/system/serverjockey.service
/usr/lib/python3.10/site-packages/psutil-5.9.1.dist-info/INSTALLER
/usr/lib/python3.10/site-packages/psutil-5.9.1.dist-info/LICENSE
/usr/lib/python3.10/site-packages/psutil-5.9.1.dist-info/METADATA
/usr/lib/python3.10/site-packages/psutil-5.9.1.dist-info/RECORD
/usr/lib/python3.10/site-packages/psutil-5.9.1.dist-info/REQUESTED
/usr/lib/python3.10/site-packages/psutil-5.9.1.dist-info/WHEEL
/usr/lib/python3.10/site-packages/psutil-5.9.1.dist-info/top_level.txt
/usr/lib/python3.10/site-packages/psutil/__init__.py
/usr/lib/python3.10/site-packages/psutil/_common.py
/usr/lib/python3.10/site-packages/psutil/_compat.py
/usr/lib/python3.10/site-packages/psutil/_psaix.py
/usr/lib/python3.10/site-packages/psutil/_psbsd.py
/usr/lib/python3.10/site-packages/psutil/_pslinux.py
/usr/lib/python3.10/site-packages/psutil/_psosx.py
/usr/lib/python3.10/site-packages/psutil/_psposix.py
/usr/lib/python3.10/site-packages/psutil/_pssunos.py
/usr/lib/python3.10/site-packages/psutil/_psutil_linux.cpython-310-x86_64-linux-gnu.so
/usr/lib/python3.10/site-packages/psutil/_psutil_posix.cpython-310-x86_64-linux-gnu.so
/usr/lib/python3.10/site-packages/psutil/_pswindows.py
/usr/lib/python3.10/site-packages/psutil/__pycache__/__init__.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/__init__.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_common.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_common.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_compat.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_compat.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psaix.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psaix.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psbsd.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psbsd.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_pslinux.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_pslinux.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psosx.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psosx.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psposix.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_psposix.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_pssunos.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_pssunos.cpython-310.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_pswindows.cpython-310.opt-1.pyc
/usr/lib/python3.10/site-packages/psutil/__pycache__/_pswindows.cpython-310.pyc


%preun
systemctl stop serverjockey
exit 0


%pre
systemctl stop serverjockey
exit 0


%post
HOME_DIR="/home/sjgms"
SERVERLINK_DIR="$HOME_DIR/serverlink"
id -u sjgms > /dev/null 2>&1
if [ $? -ne 0 ]; then
  rm -rf $HOME_DIR > /dev/null 2>&1
  adduser --system sjgms
  [ $? -eq 0 ] || exit 1
  mkdir -p $SERVERLINK_DIR
  echo "{ \"module\": \"serverlink\", \"auto\": \"daemon\", \"hidden\": true }" > $SERVERLINK_DIR/instance.json
  {
    echo "{"
    echo "  \"CMD_PREFIX\": \"!\","
    echo "  \"ADMIN_ROLE\": \"pzadmin\","
    echo "  \"BOT_TOKEN\": null,"
    echo "  \"EVENTS_CHANNEL_ID\": null,"
    echo "  \"WHITELIST_DM\": \"Welcome to our server.\nYour login is \${user} and password is \${pass}\""
    echo "}"
  } > $SERVERLINK_DIR/serverlink.json
  find $HOME_DIR -type d -exec chmod 755 {} +
  find $HOME_DIR -type f -exec chmod 600 {} +
  chown -R sjgms $HOME_DIR
  chgrp -R sjgms $HOME_DIR
  #runuser - sjgms -s /bin/bash -c "steamcmd +quit"
  #[ -d "$HOME_DIR/.steam" ] || exit 1
fi
systemctl daemon-reload
systemctl enable serverjockey
systemctl start serverjockey


%changelog
* Thu Dec 03 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.6
- Feature release v0.0.6
* Thu Oct 14 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.5
- Added support for Unturned
* Thu Sep 15 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.4
- Feature release v0.0.4
* Thu Sep 15 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.3
- Webapp improvements and more
* Thu Aug 18 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.2
- Full test and build for first GitHub release
* Thu Aug 18 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.1
- First version being packaged
