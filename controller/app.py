#!/usr/bin/python3.9

import os
import socket
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.app.ofctl.api import get_datapath
from base_switch import BaseSwitch

class MainController(BaseSwitch):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info("Controller IP: %s", socket.gethostbyname(socket.gethostname()))
        self.mac_table = {} 

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, event):
        datapath = event.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.logger.info("datapath connected %s", datapath.id)
        self.send_messages(datapath, [self.del_flow(datapath)])

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        
        msg = self.add_flow(datapath, 0, 0, match, inst)
        self.send_messages(datapath, [msg])

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        # Học MAC toàn cục
        self.mac_table.setdefault(src, {})
        self.mac_table[src] = {"dpid": dpid, "port": in_port}

        # Kiểm tra đích đến
        if dst in self.mac_table:
            dst_info = self.mac_table[dst]
            
            # 1. Nếu cùng Switch: Chặn nếu khác Port (Isolation)
            if dst_info["dpid"] == dpid:
                if dst_info["port"] != in_port:
                    self.logger.info("DROP: Same DPID %s, Different Port %s->%s", dpid, in_port, dst_info["port"])
                    return
                out_port = dst_info["port"]
            # 2. Nếu khác Switch: Đẩy ra cổng liên kết (Flood để tìm đường)
            else:
                out_port = ofproto.OFPP_FLOOD
        else:
            # 3. CHƯA BIẾT ĐÍCH: Flood toàn mạng để tìm
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Nạp flow chỉ khi đã xác định được port đích cụ thể và cùng DPID
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            msg_flow = self.add_flow(datapath, 0, 1, match, inst, i_time=10)
            self.send_messages(datapath, [msg_flow])

        # Packet Out
        out_msg = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=in_port, actions=actions, data=msg.data)
        self.send_messages(datapath, [out_msg])