#!/usr/bin/env python
# dynamic_topo.py

import yaml
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController, OVSKernelSwitch


def build_dynamic_topology():
    with open("network_config.yaml", "r") as file:
        config = yaml.safe_load(file)

    net = Mininet_wifi(controller=RemoteController, switch=OVSKernelSwitch)
    nodes = {}

    info("*** 1. Add Controller\n")
    ctrl_ip = config["controller"]["ip"]
    ctrl_port = config["controller"]["port"]
    c0 = net.addController(
        "c0", controller=RemoteController, ip=ctrl_ip, port=ctrl_port
    )

    info("*** 2. Add Core Switches\n")
    for sw in config.get("switches", []):
        nodes[sw["id"]] = net.addSwitch(
            sw["id"], dpid=sw["dpid"], protocols="OpenFlow13"
        )

    info("*** 3. Add Access Points\n")
    for ap in config.get("access_points", []):
        nodes[ap["id"]] = net.addAccessPoint(
            ap["id"],
            ssid=ap["ssid"],
            mode="g",
            channel=str(ap["channel"]),
            dpid=ap["dpid"],
            position=ap["position"],
            protocols="OpenFlow13",
        )

    info("*** 4. Add Stations\n")
    for sta in config.get("stations", []):
        nodes[sta["id"]] = net.addStation(
            sta["id"], ip=sta["ip"], mac=sta["mac"], position=sta["position"]
        )

    info("*** 5. Configure Nodes\n")
    net.setPropagationModel(model="logDistance", exp=4.5)
    net.configureWifiNodes()

    info("*** 6. Add Links\n")
    for ap in config.get("access_points", []):
        if "connected_to" in ap and ap["connected_to"] in nodes:
            net.addLink(nodes[ap["id"]], nodes[ap["connected_to"]])

    for sta in config.get("stations", []):
        if "connected_to" in sta and sta["connected_to"] in nodes:
            net.addLink(nodes[sta["id"]], nodes[sta["connected_to"]])

    info("*** 7. Starting network...\n")
    net.build()
    c0.start()

    for sw in config.get("switches", []):
        nodes[sw["id"]].start([c0])

    for ap in config.get("access_points", []):
        nodes[ap["id"]].start([c0])

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    build_dynamic_topology()
