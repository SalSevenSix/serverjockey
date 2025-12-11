%define __strip /bin/true

Name:           sjgms
Version:        0.25.0
Release:        1%{?dist}
Summary:        ServerJockey Game Management System
BuildArch:      x86_64
License:        Proprietary
Source0:        %{name}-%{version}.tar.gz
URL:            https://github.com/SalSevenSix/serverjockey


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


%files
%defattr(755,root,root)
/usr/local/bin/serverjockey.pyz
/usr/local/bin/serverjockey_cmd.pyz
/usr/local/bin/serverlink


%pre
[ -f /etc/systemd/system/serverjockey.service ] || exit 0
systemctl stop serverjockey > /dev/null 2>&1
exit 0


%post
/usr/local/bin/serverjockey_cmd.pyz -nt adduser
exit $?


%preun
[ -f /etc/systemd/system/serverjockey.service ] || exit 0
systemctl stop serverjockey > /dev/null 2>&1
exit 0


%postun
[ -f /etc/systemd/system/serverjockey.service ] || exit 0
rm /etc/systemd/system/serverjockey.service > /dev/null 2>&1
systemctl daemon-reload
exit 0


%changelog
* Fri Dec 12 2025 Bowden Salis <bsalis76@gmail.com> - 0.25.0
- Feature release 0.25.0
* Thu Dec 11 2025 Bowden Salis <bsalis76@gmail.com> - 0.24.0
- TeamSpeak server support release
* Wed Oct 15 2025 Bowden Salis <bsalis76@gmail.com> - 0.23.0
- Small improvements release
* Thu Oct 02 2025 Bowden Salis <bsalis76@gmail.com> - 0.22.0
- Small changes and lib updates
* Sun Jul 27 2025 Bowden Salis <bsalis76@gmail.com> - 0.21.0
- AI features release
* Wed Jul 02 2025 Bowden Salis <bsalis76@gmail.com> - 0.20.0
- Support for Valheim and discord bot chatlog feature
* Fri Apr 11 2025 Bowden Salis <bsalis76@gmail.com> - 0.19.0
- Trigger improvements release
* Thu Mar 13 2025 Bowden Salis <bsalis76@gmail.com> - 0.18.0
- Mod uploads and Triggers features
* Wed Feb 19 2025 Bowden Salis <bsalis76@gmail.com> - 0.17.0
- ServerLink enhancements, aliases, rewards and activity
* Sat Jan 11 2025 Bowden Salis <bsalis76@gmail.com> - 0.16.0
- Small features and library upgrades release
* Thu Dec 19 2024 Bowden Salis <bsalis76@gmail.com> - 0.15.0
- Small improvements and library upgrades release
* Mon Oct 28 2024 Bowden Salis <bsalis76@gmail.com> - 0.14.0
- Factorio Space Age support release
* Tue Sep 17 2024 Bowden Salis <bsalis76@gmail.com> - 0.13.0
- Technical upgrades release
* Wed Aug 14 2024 Bowden Salis <bsalis76@gmail.com> - 0.12.0
- Ubuntu 24 migration technical release
* Wed Jul 17 2024 Bowden Salis <bsalis76@gmail.com> - 0.11.0
- Discord guide doco refresh
* Sat Jun 29 2024 Bowden Salis <bsalis76@gmail.com> - 0.10.0
- Nginx and Prometheus integrations release
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
* Mon Oct 23 2023 Bowden Salis <bsalis76@gmail.com> - 0.4.0
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
