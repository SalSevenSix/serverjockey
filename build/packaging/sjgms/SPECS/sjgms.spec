%define __strip /bin/true

Name:           sjgms
Version:        0.10.0
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
* Tue Apr 30 2024 Bowden Salis <bsalis76@gmail.com> - 0.10.0
- Feature release v0.10.0
* Mon Apr 29 2024 Bowden Salis <bsalis76@gmail.com> - 0.9.0
- Technical release, library upgrades and Ubuntu 24 support
* Mon Apr 15 2024 Bowden Salis <bsalis76@gmail.com> - 0.8.0
- Added support for Palworld
* Tue Feb 06 2024 Bowden Salis <bsalis76@gmail.com> - 0.7.0
- Improvement release for Activity reporting and extension also added translations
* Tue Dec 26 2023 Bowden Salis <bsalis76@gmail.com> - 0.6.0
- Chrome Browser extension feature release
* Thu Nov 30 2023 Bowden Salis <bsalis76@gmail.com> - 0.5.0
- Activity reporting feature release
* Wed Oct 23 2023 Bowden Salis <bsalis76@gmail.com> - 0.4.0
- Feature release v0.4.0
* Mon Aug 14 2023 Bowden Salis <bsalis76@gmail.com> - 0.3.0
- Cachelock feature and webapp improvements
* Sat Aug 05 2023 Bowden Salis <bsalis76@gmail.com> - 0.2.0
- Discord chat integration and UPnP support
* Thu Jun 29 2023 Bowden Salis <bsalis76@gmail.com> - 0.1.0
- Small features and polish release for milestone v0.1.0
* Wed May 24 2023 Bowden Salis <bsalis76@gmail.com> - 0.0.8
- Added support for Starbound
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
