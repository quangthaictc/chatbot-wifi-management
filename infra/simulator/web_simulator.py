#!/usr/bin/env python3
import yaml
import threading
import re
import os
import math
from flask import Flask, request, jsonify, render_template
from mininet.log import setLogLevel
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController, OVSKernelSwitch

from utils.logger_config import get_logger

app = Flask(__name__)
net_global = None
logger = get_logger("Mininet-WiFi")

@app.route("/")
def index():
    return render_template('index.html', title='Mininet WiFi')

@app.route("/api/topology", methods=["GET"])
def get_topo():
    with open("network_config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return jsonify(config)


@app.route("/api/update_node", methods=["POST"])
def update_node():
    data = request.json
    sta_name = data.get("id")
    connected_to = data.get("connectedTo")
    x = data.get("x")
    y = data.get("y")

    if net_global:
        sta_obj = net_global.get(sta_name)
        if sta_obj:
            if not connected_to:
                sta_obj.cmd(f"iw dev {sta_name}-wlan0 disconnect")
            else:
                with open("network_config.yaml", "r") as f:
                    temp_config = yaml.safe_load(f)

                ssid = ""
                for ap in temp_config.get("access_points", []):
                    if ap["id"] == connected_to:
                        ssid = ap["ssid"]
                        break

                if ssid:
                    sta_obj.cmd(f'iwconfig {sta_name}-wlan0 essid "{ssid}"')
                    sta_ip = ""
                    for sta in temp_config.get("stations", []):
                        if sta["id"] == sta_name:
                            sta_ip = sta["ip"].split("/")[0]
                            break
                    if sta_ip:
                        sta_obj.cmd(f"arping -A -c 2 -I {sta_name}-wlan0 {sta_ip} &")

    with open("network_config.yaml", "r") as f:
        config = yaml.safe_load(f)

    for sta in config.get("stations", []):
        if sta["id"] == sta_name:
            if x is not None and y is not None:
                sta["ui_pos"] = f"{x},{y}"
            sta["connected_to"] = connected_to
            break

    with open("network_config.yaml", "w") as f:
        yaml.dump(config, f, sort_keys=False)

    return jsonify({"status": "success"})


@app.route("/api/scan", methods=["POST"])
def scan_wifi():
    return jsonify({"ssids": []})


@app.route("/api/connect", methods=["POST"])
def connect_wifi():
    sta_name = request.json.get("station")
    ssid = request.json.get("ssid")
    ap_id = request.json.get("ap_id")

    with open("network_config.yaml", "r") as f:
        config = yaml.safe_load(f)

    if net_global:
        sta_obj = net_global.get(sta_name)
        if sta_obj:
            sta_obj.cmd(f'iwconfig {sta_name}-wlan0 essid "{ssid}"')
            sta_ip = ""
            for sta in config.get("stations", []):
                if sta["id"] == sta_name:
                    sta_ip = sta["ip"].split("/")[0]
                    break
            if sta_ip:
                sta_obj.cmd(f"arping -A -c 2 -I {sta_name}-wlan0 {sta_ip} &")

    for sta in config["stations"]:
        if sta["id"] == sta_name:
            sta["connected_to"] = ap_id
            break

    with open("network_config.yaml", "w") as f:
        yaml.dump(config, f, sort_keys=False)

    logger.info(f"{sta} connected to AP {ap_id} with SSID {ssid}")
    return jsonify({"status": "success", "connected_ap": ap_id})


@app.route("/api/terminal", methods=["POST"])
def run_terminal():
    node_name = request.json.get("node")
    cmd = request.json.get("command")
    node_obj = net_global.get(node_name)

    if cmd.startswith("ping") and "-c" not in cmd:
        cmd = cmd.replace("ping", "ping -c 4 ", 1)

    if node_obj:
        logger.info(f"node {node_name} executed command {cmd}")
        output = node_obj.cmd(cmd)
    else:
        logger.error(f"Node {node_name} not found")
        output = "Node not found."
    return jsonify({"output": output})


def start_mininet():
    global net_global
    with open("network_config.yaml", "r") as file:
        config = yaml.safe_load(file)

    net = Mininet_wifi(controller=RemoteController, switch=OVSKernelSwitch)
    net_global = net
    nodes = {}


    c0 = net.addController("c0", ip="127.0.0.1", port=6653)


    for sw in config.get("switches", []):
        nodes[sw["id"]] = net.addSwitch(sw["id"], dpid=str(int(sw["dpid"], 16)))
    for ap in config.get("access_points", []):
        nodes[ap["id"]] = net.addAccessPoint(
            ap["id"],
            ssid=ap["ssid"],
            mode="g",
            channel=str(ap["channel"]),
            dpid=str(int(ap["dpid"], 16)),
            position=ap["position"],
        )

    for sta in config.get("stations", []):
        nodes[sta["id"]] = net.addStation(
            sta["id"], ip=sta["ip"], mac=sta["mac"], position=sta["position"]
        )

    net.setPropagationModel(model="logDistance", exp=1.5)
    net.configureWifiNodes()

    for ap in config.get("access_points", []):
        if "connected_to" in ap and ap["connected_to"]:
            net.addLink(nodes[ap["id"]], nodes[ap["connected_to"]])

    for sta in config.get("stations", []):
        if "connected_to" in sta and sta["connected_to"]:
            net.addLink(nodes[sta["id"]], nodes[sta["connected_to"]])

    net.build()
    c0.start()
    for node in config.get("switches", []) + config.get("access_points", []):
        nodes[node["id"]].start([c0])

    for sta in config.get("stations", []):
        if not sta.get("connected_to"):
            sta_node = net.get(sta["id"])
            if sta_node:
                sta_node.cmd(f"iw dev {sta['id']}-wlan0 disconnect")

    # gen traffic
    net.pingAll()

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    flask_app = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0", port=5000, debug=False, use_reloader=False
        ),
        daemon=True,
    )
    flask_app.start()
    start_mininet()
