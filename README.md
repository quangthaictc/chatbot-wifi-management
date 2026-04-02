# Draft notes - The full documentation will be available soon!

Ryu just work good in python3.9 (maybe)

Thanks so much for [this blog](https://www.linkedin.com/pulse/installing-ryu-sdn-controller-ubuntu-step-by-step-developer-kamran-g5gdf/)

## Installation

### Ryu setup

**Install python3.9 & dependencies**

```bash
sudo apt update
sudo apt install software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa
# Then press ENTER

sudo apt update -y

sudo apt install python3.9 python3.9-venv gcc libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev
```

**Create and active venv**

```bash
python3.9 -m venv .venv
```

```bash
source .venv/bin/active
```

**Install python packages**

```bash
# Fix error while install ryu

pip install "setuptools<58.0.0"

pip install -r requirements.txt
```


**Check ryu-manager**

```bash
ryu-manager --version
```

### Mininet-Wifi setup

```bash
git clone https://github.com/intrig-unicamp/mininet-wifi

cd mininet-wifi

sudo util/install.sh -Wlnfv
```

install.sh options:
-W: wireless dependencies
-n: mininet-wifi dependencies
-f: OpenFlow
-v: OpenvSwitch
-l: wmediumd
optional:
-P: P4 dependencies
-6: wpan tools

**See more: [mininet-wifi repository](https://github.com/intrig-unicamp/mininet-wifi)**

Fix error when run Mininet-WiFi `ovs-vsctl: cannot create a port named ap1-wlan1-1 because a port named ap1-wlan1-1 already exists on bridge ap1`:

```bash
# /etc/NetworkManager/NetworkManager.conf
[keyfile]
unmanaged-devices=interface-name:wlan*,interface-name:ap*,interface-name:sta*
```

```bash
sudo systemctl restart NetworkManager.service

sudo systemctl daemon-reload
```
