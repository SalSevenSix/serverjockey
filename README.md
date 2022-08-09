# ServerJockey

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D4E4ZYZ)

## Source Repository
[ServerJockey](https://github.com/SalSevenSix/serverjockey) project on GitHub

## Ubuntu/Debian Install
* **Recommended**. Update your system first
```bash
sudo apt update
sudo apt upgrade
```

* Install [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) if not installed
```bash
sudo add-apt-repository multiverse
sudo apt install software-properties-common
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install lib32gcc-s1 steamcmd
```

* Download and install the deb package
```bash
wget -O sjgms.deb https://4sas.short.gy/sjgms-latest
sudo apt install ./sjgms.deb
```

* The ServerJockey system should automatically be started.
Find login details for the webapp in the `serverjockey-client.json` file.
Use the IP of the machine in place of `localhost` in the URL.
Enter the token to login to the webapp on the home page.
```bash
cat /home/sjgms/serverjockey-client.json
```
