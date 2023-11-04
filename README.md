# ServerJockey

ServerJockey is a game server management system. It is designed to be an easy
to use self-hosting option for multiplayer servers. Allowing you to create
and remotely manage your servers. A webapp and Discord bot are used as clients.

If your like using this system, please consider supporting me on Ko-fi.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D4E4ZYZ)


## Source Repository
[ServerJockey](https://github.com/SalSevenSix/serverjockey) project on GitHub


## DEB Package Install
Arch x86_64 only. Requires Python 3.10 installed. Tested and works on **Ubuntu 22.04**

* Install [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) if not installed
```bash
sudo apt install software-properties-common
sudo add-apt-repository multiverse
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install lib32gcc-s1 steamcmd
```

* Download and install the deb package
```bash
wget -O sjgms.deb https://4sas.short.gy/sjgms-deb-latest
sudo apt install ./sjgms.deb
```

* The ServerJockey system should automatically be started.
Find the login details for the webapp by using the CLI client as shown below.
```bash
serverjockey_cmd.pyz -nc showtoken
```


<!--
## RPM Package Install
Arch x86_64 only. Requires Python 3.10 installed. Tested and works on **Fedora 36**

* Download and install the rpm package
```bash
wget -O sjgms.rpm https://4sas.short.gy/sjgms-rpm-latest
sudo yum install ./sjgms.rpm
```

* Manually install [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD)
```bash
sudo yum install glibc.i686 libstdc++.i686
sudo su - sjgms
mkdir ~/Steam && cd ~/Steam
curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -
./steamcmd.sh +quit
```

* The ServerJockey system should automatically be started.
Find the login details for the webapp by using the CLI client as shown below.
```bash
serverjockey_cmd.pyz -nc showtoken
```
-->


## VirtualBox Appliance
ServerJockey is available pre-installed on a virtual machine (VM) image that
can be imported into VirtualBox. Use this option on Windows systems.
* [Download the VM image](https://4sas.short.gy/zombox-latest)
* Install [VirtualBox](https://www.virtualbox.org/) if not installed.
* Import the VM image file into VirtualBox.
* Adjust the CPU and memory settings for the VM as desired.
* Start the VM. Webapp URL and login token will be displayed in the console.


## Docker Image
ServerJockey is available as a Docker image.
Webapp URL and login token will be shown in the console output.
Images are compatible with [Pterodactyl](https://pterodactyl.io/).
* [Docker Images](https://hub.docker.com/r/salsevensix/serverjockey/tags)
* [Pterodactyl Egg](https://4sas.short.gy/ptero-egg-latest)

Start ServerJockey using Docker as follows.
Open additional ports for game servers as needed.
```bash
sudo docker run -p 6164:6164/tcp <image>:<tag>
```


## Running from source
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
