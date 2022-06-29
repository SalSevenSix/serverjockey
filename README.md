# serverjockey

## Install
* **Recommended**: Update your system first
```bash
sudo apt update
sudo apt upgrade
```

* Install [cURL](https://curl.haxx.se/) if not installed
```bash
sudo apt install curl
```

* Install `unzip` if not installed
```bash
sudo apt install unzip
```

* Now download and unzip the
[serverjockey project](https://github.com/SalSevenSix/serverjockey)
from GitHub
```bash
mkdir projectzomboid; cd projectzomboid
curl -L -o master.zip https://github.com/SalSevenSix/serverjockey/archive/master.zip
unzip master.zip; mv serverjockey-master serverjockey; cd serverjockey
```

* Now execute `start.sh` to start the apps.
Expect it to fail as dependencies are checked and not found.
Follow the instructions given by the script to install
the remaining dependencies that require sudo.
```bash
./start.sh
```
