import os
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp
from ryu.lib import hub
import requests


class QuackWFController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(QuackWFController, self).__init__(*args, **kwargs)

        # Bang luu dia chi MAC phuc vu cho L2 Switch
        self.mac_to_port = {}

        # URL cua FastAPI container (Can dam bao trung ten container hoac dia chi IP)
        self.fast_api_url = os.getenv("FAST_API_URL")

        # --- CAC BIEN PHUC VU SECURITY ---
        self.arp_table = {}  # Luu IP -> MAC de chong ARP Spoofing
        self.packet_tracker = {}  # Luu MAC -> {'count': int, 'dpid': int} de chong DoS
        self.alerted_macs = (
            set()
        )  # Chanh gui canh bao lien tuc (spam) cho cung 1 dia chi MAC

        # Khoi chay luong giam sat mang ngam (chay song song)
        self.monitor_thread = hub.spawn(self._monitor_traffic)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Luat mac dinh (Table-miss flow entry): Day tat ca goi tin chua biet duong len Controller
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Ham ho tro them luat (flow rule) vao switch"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath, priority=priority, match=match, instructions=inst
            )
        datapath.send_msg(mod)

    def send_security_alert(self, attack_type, severity, dpid, attacker_mac):
        # Neu da canh bao MAC nay roi thi bo qua, doi khoi dong lai he thong moi bao tiep
        if attacker_mac in self.alerted_macs:
            return

        payload = {
            "attack_type": attack_type,
            "severity": severity,
            "dpid": dpid,
            "attacker_mac": attacker_mac,
            "details": f"He thong Ryu tu dong phat hien {attack_type} tu dia chi MAC {attacker_mac}",
        }

        try:
            # Goi sang API de ban thong bao len Telegram
            requests.post(
                f"{self.fast_api_url}/security/alert", json=payload, timeout=5.0
            )
            self.alerted_macs.add(attacker_mac)
            self.logger.info(
                f"Da gui canh bao {attack_type} tu MAC {attacker_mac} sang FastAPI."
            )
        except Exception as e:
            self.logger.error(f"Loi khi gui canh bao sang FastAPI: {e}")

    def _monitor_traffic(self):
        while True:
            # Kiem tra moi 5 giay
            hub.sleep(5)

            for mac, data in list(self.packet_tracker.items()):
                # Neu 1 MAC gui hon 200 goi tin Packet-In trong 5 giay len cho Controller
                # (Day chinh la hien tuong bão goi tin - DoS)
                if data["count"] > 200:
                    self.send_security_alert(
                        attack_type="Control Plane DoS Flooding",
                        severity="CRITICAL",
                        dpid=data["dpid"],
                        attacker_mac=mac,
                    )

            # Reset bo dem cho chu ky kiem tra tiep theo
            self.packet_tracker.clear()

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug(
                "packet truncated: only %s of %s bytes",
                ev.msg.msg_len,
                ev.msg.total_len,
            )

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Bo qua cac goi tin LLDP cua he thong
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # --- SECURITY LOGIC START ---

        # 1. Theo doi so luong goi tin cua tung MAC (Chong DoS)
        if src not in self.packet_tracker:
            self.packet_tracker[src] = {"count": 0, "dpid": dpid}
        self.packet_tracker[src]["count"] += 1

        # 2. Phat hien ARP Spoofing
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            src_ip = arp_pkt.src_ip

            # Neu IP nay da ton tai trong bang nhung MAC lai khac -> Co the dang bi gia mao
            if src_ip in self.arp_table and self.arp_table[src_ip] != src:
                self.send_security_alert(
                    attack_type="ARP Spoofing",
                    severity="WARNING",
                    dpid=dpid,
                    attacker_mac=src,
                )
            else:
                # Luu lai cap IP-MAC hop le vao he thong
                self.arp_table[src_ip] = src

        # --- SECURITY LOGIC END ---

        # Hoc dia chi MAC cua thiet bi gui de switch biet duong chuyen tiep goi tin sau nay
        self.mac_to_port[dpid][src] = in_port

        # Neu da biet MAC dich nam o cong nao thi gui vao cong do, chua biet thi Flood (gui tat ca cac cong)
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Cai dat flow rule de tu nay switch tu forward, khong can gui len Controller (neu khong phai flood)
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # Kiem tra buffer_id hop le truoc khi add_flow
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        # Tao tin nhan Packet-Out de day goi tin tiep tuc hanh trinh cua no
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)
        # --- L2 SWITCHING LOGIC END ---
