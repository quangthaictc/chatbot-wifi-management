# Chatbot WiFi Management Project

## Project Overview

This project implements a centralized wireless network management system using **Software-Defined Networking (SDN) architecture**. By decoupling the control logic from the underlying hardware, the system provides high flexibility and programmability. A core component of this project is an AI-driven Chatbot Agent that allows administrators to manage network policies and security using natural language, significantly reducing the complexity of traditional CLI-based management.

## Core Features

- **AI Natural Language Processing:** Integration with Gemini API to parse human intent into actionable network configurations.

- **Automated Mitigation:** Real-time detection and automatic blocking of ARP Spoofing and DoS flooding attacks at the switch level.

- **Centralized Monitoring:** Real-time traffic analysis and event logging via a unified PLG (Promtail, Loki, Grafana) stack.

- **Visual Topology:** A web-based interface that renders the current state of the virtual wireless network using Flask and Mininet-WiFi.

## System Architecture

The system is divided into three distinct planes:

1. **Application Plane:** Consists of the **Telegram Bot (using Aiogram Framework)** and **FastAPI**. It handles user interaction and translates natural language into API calls.

2. **Control Plane:** Powered by **Ryu SDN Controller**. It manages the flow tables of the switches via the **OpenFlow protocol** and executes security logic.

3. **Data Plane:** Built with **Mininet-WiFi** and **Open vSwitch**. It simulates the physical layer, including Access Points, Stations, and wireless signal propagation.

## Tech Stack

- **Networking:** Mininet-WiFi, Open vSwitch, Ryu Framework, OpenFlow v1.3.

- **Backend:** Python 3.9, FastAPI, Flask.

- **AI and Bot:** Gemini API, Aiogram v3.

- DevOps and Monitoring: Docker and Docker Compose, **PLG Stack** -  Promtail (Log Collector), Loki (Log Aggregator), Grafana (Visualization).

## Getting Started

Create a .env file in the root directory (look at .env.example).

The recommended way to deploy the system is using Docker Compose to ensure environment consistency.

Clone the repository:

```bash
git clone <repository_url>
cd <project_directory>

docker compose up -d
```

## Manual Installation

This project tested on Ubuntu Server 24.04 LTS.

### Ryu Application Installation

Ryu requires Python 3.9 for optimal stability.

```bash
sudo apt update
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9 python3.9-venv gcc libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev -y

python3.9 -m venv .venv
source .venv/bin/activate

# Critical: Ryu installation requires specific setuptools version
pip install "setuptools<58.0.0"
pip install -r requirements.txt
```


### Mininet-WiFi Installation

```bash
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi
sudo util/install.sh -Wlnfv
```

## Configuration

- **network_config.yaml:** Defines the node parameters, including SSID, IP ranges, MAC addresses, and bandwidth limits for the simulation.

- **.env:** Stores sensitive credentials for the Telegram Bot, Gemini AI and some configurations.

- **logger_config.py:** A shared Python module that ensures all components (Bot, API, Controller) produce standardized logs for Loki to index.

## Usage

1. **Network Simulation:** Once started, access the Web UI at http://localhost:5000 to see the wireless topology.

2. **Telegram Interaction:** Open your Telegram Bot and send commands like "Show all active stations" or "Block device with MAC 02:00:00:00:01:00".

## Testing and Verification

> [!WARNING]
> If installing manually, you must also launch the applications manually!
>
> For each module (except Mininet-WiFi - infra directory), you must create and run the venv and then execute the command `pip install -r requirements.txt`.
>
> After successfully installing the libraries, execute the `main.py` file in each directory.
>
> To run the infrastructure, in the `infra/simulator` directory, execute the `web_simulator.py` file to automatically deploy devices in the Mininet-WiFi infrastructure based on the `network_config.yml` file at the project root.

- **Connectivity Tests:** Run `pingall` within the Mininet-WiFi CLI to verify initial path computation by the Ryu controller.

- **Security Stress Tests:** Use `python3 -c 'import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1); [s.sendto(b"DoS test", ("10.255.255.255", 80)) for _ in range(10000)]'` from a station node to simulate a DoS attack and verify if the controller pushes a "DROP" flow entry.

- **AI Intent Verification:** Test various phrasing of commands (e.g., "Kick out station 1" vs "Disconnect 10.0.0.1") to ensure Gemini correctly identifies the "Block" function.

## Directory Structure

```
project_root/
├── api/                # FastAPI source code
├── controller/         # SDN Controller
├── infra/              # Mininet-WiFi
├── loggings/           # Basic config logging system 
├── telegram/           # Telegram Bot and Gemini API logic
├── utils/              # Shared logging
├── docker-compose.yml  # Orchestration file
├── network_config.yml  # Automated change config while drag nodes in WebUI Simulation
└── network_config_original.yaml # Network topology definition (just a backup file)
```

## Troubleshooting

### Error while installation Ryu

Make sure the Python version is Python3.9 (maybe...).I've tested it on higher versions and it doesn't work, as I read in [this blog](https://www.linkedin.com/pulse/installing-ryu-sdn-controller-ubuntu-step-by-step-developer-kamran-g5gdf/)

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.9
```

### Interface Conflicts

If Mininet-WiFi fails to create ports (i got this error: "ovs-vsctl: cannot create a port named ap1-wlan1-1 because a port named ap1-wlan1-1 already exists on bridge ap1"), ensure NetworkManager is not controlling wireless interfaces. Add the following to `/etc/NetworkManager/NetworkManager.conf`:

```
[keyfile]
unmanaged-devices=interface-name:wlan*,interface-name:ap*,interface-name:sta*
```
