# serverjockey

## Install
* **Recommended**: Update your linux system first
```bash
sudo apt update
sudo apt upgrade
```

* Install [cURL](https://curl.haxx.se/) if not installed
```bash
sudo apt install curl
curl --version
```

* Install `unzip` if not installed
```bash
sudo apt install unzip
unzip -v
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
Expect it to fail initially as dependencies are checked and not found.
Follow the instructions given to install the remaining dependencies.
```bash
./start.sh
```
