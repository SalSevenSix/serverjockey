# ServerJockey

ServerJockey is a game server management system. It is designed to be an easy
to use self-hosting option for multiplayer servers. Allowing you to create
and remotely manage your servers. A webapp and Discord bot are used as clients.

If your like using this system, please consider supporting me on Ko-fi.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D4E4ZYZ)


## Source Repository
[ServerJockey](https://github.com/SalSevenSix/serverjockey) project on GitHub


## Ubuntu/Debian Install
Arch x86_64 only. Requires Python 3.10 installed. Tested and works on Ubuntu 22.04

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
wget -O sjgms.deb https://4sas.short.gy/sjgms-deb-latest
sudo apt install ./sjgms.deb
```

* The ServerJockey system should automatically be started.
Find the login details for the webapp by using the CLI client as shown below.
```bash
serverjockey_cmd.pyz -t
```


## Fedora/CentOS Install
Arch x86_64 only. Requires Python 3.10 installed. Tested and works on Fedora 36

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
serverjockey_cmd.pyz -t
```


## VirtualBox Appliance
ServerJockey is available pre-installed on a virtual machine (VM) image that
can be imported into VirtualBox. Use this option on Windows systems.

* Download the VM image: https://4sas.short.gy/zombox-latest
* Install [VirtualBox](https://www.virtualbox.org/) if not installed.
* Import the VM image file into VirtualBox.
* Adjust the CPU and memory settings for the VM as desired.
* Start the VM. Webapp URL and login token will be displayed in the console.


## Docker Image
ServerJockey is available as a Docker image. Webapp login token will be shown in
the console output. The image is compatible with [Pterodactyl](https://pterodactyl.io/).
Docker is also a good option for Windows systems.
[Images on Docker Hub](https://hub.docker.com/r/salsevensix/serverjockey/tags)
