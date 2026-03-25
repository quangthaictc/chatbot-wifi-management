#!/usr/bin/env python

import os
import sys
import yaml

from mn_wifi.net import Mininet_wifi
from mn_wifi.net import CLI
from mn_wifi.node import UserAP
from mininet.node import RemoteController
from mininet.log import setLogLevel
from mininet.log import info

def create_mininet_wifi(config_file, ctrler_addr="127.0.0.1"):
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    net = Mininet_wifi(controller=RemoteController, accessPoint=UserAP, autoAssociation=False)

    

if __name__ == "__main__":
    ctrl_address = os.getenv("SDN_CONTROLLER", "127.0.0.1")

    # Check if the command-line argument is provided
    if len(sys.argv) < 2:
        print(
            "Usage: sudo ./path/auto_topo.py <netconfig_file> [controller_address]"
        )
        sys.exit(1)

    config_file = sys.argv[1]

    if len(sys.argv) > 2:
        ctrl_address = sys.argv[2]
    
