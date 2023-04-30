%define __strip /bin/true

Name:           sjgms
Version:        0.0.8
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
cp serverjockey_cmd.pyz $RPM_BUILD_ROOT/usr/local/bin
cp serverlink $RPM_BUILD_ROOT/usr/local/bin
mkdir -p $RPM_BUILD_ROOT/etc/systemd/system
cp serverjockey.service $RPM_BUILD_ROOT/etc/systemd/system


%files
%defattr(755,root,root)
/usr/local/bin/serverjockey.pyz
/usr/local/bin/serverjockey_cmd.pyz
/usr/local/bin/serverlink
%defattr(644,root,root)
/etc/systemd/system/serverjockey.service


%preun
systemctl stop serverjockey > /dev/null 2>&1
exit 0


%pre
systemctl stop serverjockey > /dev/null 2>&1
exit 0


%post
/usr/local/bin/serverjockey_cmd.pyz -nt adduser


%changelog
* Mon Apr 24 2023 Bowden Salis <bsalis76@gmail.com> - 0.0.8
- Feature release v0.0.8
* Mon Apr 24 2023 Bowden Salis <bsalis76@gmail.com> - 0.0.7
- Added CLI client
* Sat Dec 03 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.6
- Small features and added docker distro
* Fri Oct 14 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.5
- Added support for Unturned
* Thu Sep 15 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.4
- Feature release v0.0.4
* Thu Sep 15 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.3
- Webapp improvements and more
* Thu Aug 18 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.2
- Full test and build for first GitHub release
* Thu Aug 18 2022 Bowden Salis <bsalis76@gmail.com> - 0.0.1
- First version being packaged
