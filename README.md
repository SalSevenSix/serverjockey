# ServerJockey

![](https://serverjockey.net/assets/mediakit/banner-468x60.jpg)

ServerJockey is a game server management system for Project Zomboid
and other supported games. It is designed to be an easy to use self-hosted
option for multiplayer servers. It allows you to create and remotely
manage your servers using a webapp and Discord bot.

* 🌐️  Visit the [website](https://serverjockey.net/)
* 🎮️  Join the [Discord](https://discord.gg/TEuurWAhHn)
* 📺️  Instructional guides and dev updates on [YouTube](https://www.youtube.com/channel/UCprGg-h1FbXwZ5HdRanbijw)
* 🗃️  Source code on [GitHub](https://github.com/SalSevenSix/serverjockey)

If your like using this system, please consider supporting it on Ko-fi.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/serverjockey)

📣️ ***Choose ONE of the deployment options from below...***


## DEB Package Install
For x86_64/amd64 only. Requires Python 3.10 or higher installed as default.
Tested and works on Ubuntu 22.04 LTS, 24.04 LTS, 26.04 LTS

**1.** Install [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) if not installed already
```bash
sudo apt install software-properties-common
sudo add-apt-repository multiverse
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install lib32gcc-s1 steamcmd
```

**2.** Download and install the deb package
```bash
wget -O sjgms.deb https://dl.serverjockey.net/sjgms-master-latest.deb
sudo apt install ./sjgms.deb
```

**3.** The ServerJockey service should automatically be started.
Find the login details for the webapp by using the CLI client as shown below.
```bash
serverjockey_cmd.pyz -nc showtoken
```


## VirtualBox Appliance
ServerJockey is available pre-installed on a virtual machine (VM) image that
can be imported into VirtualBox. Use this option on Windows systems.
* [Download the VM image](https://dl.serverjockey.net/ZomBox-latest.ova)
* Install [VirtualBox](https://www.virtualbox.org/) if not installed.
* Import the VM image file into VirtualBox.
* Start the VM. Webapp URL and login token will be displayed in the console.
* *If there are any network issues or welcome banner is not shown*: Check `Settings > Network`
and make sure a valid physical network adaptor is attached using Bridged mode.


## Docker Image
ServerJockey is available as a Docker image.
Webapp URL and login token will be shown in the console output.
Images are compatible with [Pterodactyl](https://pterodactyl.io/).
* [Docker Images](https://hub.docker.com/r/salsevensix/serverjockey/tags)
* [Pterodactyl Egg](https://dl.serverjockey.net/egg-server-jockey-latest.json)

Start ServerJockey using Docker as follows.
Open additional ports for game servers as needed.
```bash
sudo docker run -p 6164:6164/tcp salsevensix/serverjockey:latest
```
If desired, you can bind the container directory `/home/container` to the local filesystem.


## RPM Package Install
For x86_64/amd64 only. Requires Python 3.10 or higher installed as default.

**1.** Download and install the rpm package
```bash
wget -O sjgms.rpm https://dl.serverjockey.net/sjgms-master-latest.rpm
sudo dnf install ./sjgms.rpm
```

**2.** Manually install [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD)
```bash
sudo dnf update
sudo dnf install glibc.i686 libstdc++.i686
sudo su - sjgms -s /bin/bash
mkdir ~/Steam && cd ~/Steam
curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -
```

**3.** The ServerJockey service should automatically be started.
Find the login details for the webapp by using the CLI client as shown below.
```bash
serverjockey_cmd.pyz -nc showtoken
```


## PACMAN Package Install
For x86_64/amd64 only. Requires Python 3.10 or higher installed as default.

**1.** Install [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) from source if not installed already
```bash
sudo pacman -Syy base-devel
git clone https://aur.archlinux.org/steamcmd.git
cd steamcmd
makepkg -si
```

**2.** Download and install the pacman package
```bash
wget -O sjgms.pkg.tar.zst https://dl.serverjockey.net/sjgms-master-latest.pkg.tar.zst
sudo pacman -U ./sjgms.pkg.tar.zst
```

**3.** The ServerJockey service should automatically be started.
Find the login details for the webapp by using the CLI client as shown below.
```bash
serverjockey_cmd.pyz -nc showtoken
```


## Running from Source
ServerJockey can be run from the source code. This option should work on
a wider range of linux distros. Note that the `serverjockey.sh` script
will check for required dependencies. Follow the instructions provided by
the script to install dependencies that need root privileges. Retry running
the script until all dependencies are satisfied, then the system will start.
```bash
BRANCH="master"
wget https://github.com/SalSevenSix/serverjockey/archive/refs/heads/$BRANCH.zip
unzip -q $BRANCH.zip && mv serverjockey-$BRANCH serverjockey
./serverjockey/serverjockey.sh --showtoken
```
