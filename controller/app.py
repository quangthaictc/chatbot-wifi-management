#!/usr/bin/python3.9

import os
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import packet_base
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.lib.packet import in_proto
from ryu.app.ofctl.api import get_datapath
from base_switch import BaseSwitch
from utils import Network

# Protocol Names
ETHERNET = ethernet.ethernet.__name__
# VLAN = vlan.vlan.__name__
IPV4 = ipv4.ipv4.__name__
ARP = arp.arp.__name__
ICMP = icmp.icmp.__name__
TCP = tcp.tcp.__name__
UDP = udp.udp.__name__

# Constants
ENTRY_TABLE = 0
LOCAL_TABLE = 0
REMOTE_TABLE = 1

MIN_PRIORITY = 0
LOW_PRIORITY = 100
MID_PRIORITY = 300

# Set idle_time=0 to make flow entries permenant
LONG_IDLE_TIME = 60
MID_IDLE_TIME = 40
IDLE_TIME = 30

class MainController(BaseSwitch):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create central MAC table
        self.mac_table = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, event):

        datapath = event.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        msgs = [self.del_flow(datapath)]

        # Set Match to ANY
        match = parser.OFPMatch()
