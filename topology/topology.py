#!/usr/bin/env python

"This example creates a simple network topology with 1 AP and 2 stations"

import os
import sys
from time import sleep

from mn_wifi.net import Mininet_wifi
from mn_wifi.net import CLI
from mn_wifi.node import UserAP
from mininet.node import RemoteController
from mininet.log import setLogLevel
from mininet.log import info


def topology(ctrler_addr="127.0.0.1"):
    net = Mininet_wifi(controller=RemoteController, accessPoint=UserAP, autoAssociation=False)

    info("*** Adding stations")
    sta1 = net.addStation('sta1', position='10,60,0')
    sta2 = net.addStation('sta2', position='20,15,0')
    sta3 = net.addStation('sta3', position='10,25,0')
    sta4 = net.addStation('sta4', position='50,30,0')
    sta5 = net.addStation('sta5', position='45,65,0')

    info("*** Adding access points\n")
    ap1 = net.addAccessPoint('ap1',
                             vssids='HUFLIT-GV,HUFLIT-NV',
                             ssid='HUFLIT',
                             mode='g',
                             channel='1',
                             position='30,40,0')
    
    info("*** Adding controller\n")
    c0 = net.addController('c0', controller=RemoteController, ip=ctrler_addr, port=6633)

    info("*** Configuring nodes\n")
    net.configureNodes()

    sta1.setRange(100, intf=sta1.params['wlan'][0])
    sta2.setRange(100, intf=sta2.params['wlan'][0])
    sta3.setRange(100, intf=sta3.params['wlan'][0])
    sta4.setRange(100, intf=sta4.params['wlan'][0])
    sta5.setRange(100, intf=sta5.params['wlan'][0])

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])

    ### This way on examples/forwardingBySSID
    sleep(2)
    cmd = 'iw dev {} connect {} {}'
    intf = ap1.wintfs[0].vssid

    sta1.cmd(cmd.format(sta1.params['wlan'][0], 'HUFLIT', ap1.wintfs[0].mac))
    sta2.cmd(cmd.format(sta2.params['wlan'][0], intf[0], ap1.wintfs[1].mac))
    sta3.cmd(cmd.format(sta3.params['wlan'][0], intf[0], ap1.wintfs[1].mac))
    sta4.cmd(cmd.format(sta4.params['wlan'][0], intf[1], ap1.wintfs[2].mac))
    sta5.cmd(cmd.format(sta5.params['wlan'][0], intf[1], ap1.wintfs[2].mac))
    ###

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == "__main__":
    setLogLevel('debug')
    topology()
