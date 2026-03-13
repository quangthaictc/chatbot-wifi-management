# Draft notes - The full documentation will be available soon!

Ryu just work in python3.9 (maybe)

Thanks so much for [this blog](https://www.linkedin.com/pulse/installing-ryu-sdn-controller-ubuntu-step-by-step-developer-kamran-g5gdf/)

## Installation

Install python3.9 & dependencies

```bash
sudo apt update
sudo apt install software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa
# Then press ENTER multi time

sudo apt update -y

sudo apt install python3.9 python3.9-venv gcc libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev
```

### Create and active venv

```bash
python3.9 -m venv .venv
```

```bash
source .venv/bin/active
```

### Install python packages

```bash
# Fix error while install ryu

pip install setuptools==79.0.1

pip install -r requirements.txt
```


### Check ryu-manager

```bash
ryu-manager --version
```# Draft notes - The full documentation will be available soon!

Ryu just work in python3.9 (maybe)

Thanks so much for [this blog](https://www.linkedin.com/pulse/installing-ryu-sdn-controller-ubuntu-step-by-step-developer-kamran-g5gdf/)

## Installation

Install python3.9 & dependencies

```bash
sudo apt update
sudo apt install software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa
# Then press ENTER multi time

sudo apt update -y

sudo apt install python3.9 python3.9-venv gcc libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev
```

### Create and active venv

```bash
python3.9 -m venv .venv
```

```bash
source .venv/bin/active
```

### Install python packages

```bash
# Fix error while install ryu

pip install setuptools==79.0.1

pip install -r requirements.txt
```


### Check ryu-manager

```bash
ryu-manager --version
```
