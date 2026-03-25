#!/usr/bin/env python

import os
import sys
from time import sleep
import socket

from mn_wifi.net import Mininet_wifi
from mn_wifi.net import CLI
from mn_wifi.node import OVSAP, UserAP
from mininet.node import OVSSwitch
from mininet.node import RemoteController
from mininet.log import setLogLevel
from mininet.log import info


def topology(ctrler_addr="127.0.1.1"):
    info("Infrastructure IP: %s\n", socket.gethostbyname(socket.gethostname()))
    "Create a network."
    net = Mininet_wifi(accessPoint=UserAP, autoAssociation=False)

    sta_arg, ap_arg = {}, {}
    if '-v' in sys.argv:
        sta_arg = {'nvif': 2}
    else:
        # isolate_clientes: Client isolation can be used to prevent low-level
        # bridging of frames between associated stations in the BSS.
        # By default, this bridging is allowed.
        # OpenFlow rules are required to allow communication among nodes
        ap_arg = {'client_isolation': True}

    info("*** Adding stations")
    sta1 = net.addStation('sta1')
    sta2 = net.addStation('sta2')
    sta3 = net.addStation('sta3')
    sta4 = net.addStation('sta4')
    sta5 = net.addStation('sta5')

    info("*** Adding access points\n")
    ap1 = net.addAccessPoint('ap1',
                             vssids='HUFLIT-GV,HUFLIT-NV',
                             ssid='HUFLIT',
                             mode='g',
                             channel='1',
                             cls=OVSAP,
                             protocols='OpenFlow13',
                             **ap_arg)
    
    ap2 = net.addAccessPoint('ap2',
                             vssids='HUFLIT-GV,HUFLIT-NV',
                             ssid='HUFLIT',
                             mode='g',
                             channel='1',
                             cls=OVSAP,
                             protocols='OpenFlow13',
                             **ap_arg)
    
    s1 = net.addSwitch('s1', cls=OVSSwitch, protocols='OpenFlow13')
    
    info("*** Adding controller\n")
    c0 = net.addController('c0', controller=RemoteController, ip=ctrler_addr, port=6633)

    info("*** Configuring nodes\n")
    net.configureNodes()

    net.addLink(ap1, s1)
    net.addLink(ap2, s1)

    sta1.setRange(100, intf=sta1.params['wlan'][0])
    sta2.setRange(100, intf=sta2.params['wlan'][0])
    sta3.setRange(100, intf=sta3.params['wlan'][0])
    sta4.setRange(100, intf=sta4.params['wlan'][0])
    sta5.setRange(100, intf=sta5.params['wlan'][0])

    info("*** Starting network\n")
    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    ap2.start([c0])

    ### This way on examples/forwardingBySSID
    sleep(2)
    cmd = 'iw dev {} connect {} {}'
    intf1 = ap1.wintfs[0].vssid
    intf2 = ap2.wintfs[0].vssid

    sta1.cmd(cmd.format(sta1.params['wlan'][0], 'HUFLIT', ap1.wintfs[0].mac))
    sta2.cmd(cmd.format(sta2.params['wlan'][0], intf1[0], ap1.wintfs[1].mac))
    sta3.cmd(cmd.format(sta3.params['wlan'][0], intf1[0], ap1.wintfs[1].mac))
    sta4.cmd(cmd.format(sta4.params['wlan'][0], intf2[1], ap2.wintfs[2].mac))
    sta5.cmd(cmd.format(sta5.params['wlan'][0], intf1[1], ap1.wintfs[2].mac))
    ###

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == "__main__":
    setLogLevel('info')
    topology()
