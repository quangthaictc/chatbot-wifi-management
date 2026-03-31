#!/usr/bin/env python

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController, OVSKernelSwitch


def topology():
    "Tao mang Mininet-WiFi voi 1 Core Switch va 3 Access Points"

    # Khoi tao mang, khai bao co dung ca Switch thuong va RemoteController
    net = Mininet_wifi(controller=RemoteController, switch=OVSKernelSwitch)

    info("*** 1. Tao Controller (Ryu)\n")
    c0 = net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6653)

    info("*** 2. Tao Core Switch (Day chuyen tai mang noi bo)\n")
    # Switch trung tam de noi cac AP voi nhau (Giong nhu Switch tổng trong cong ty)
    s1 = net.addSwitch("s1", protocols="OpenFlow13")

    info("*** 3. Tao 3 Access Points\n")
    # Dung cung SSID 'quackwf-corp' de mo phong mang doanh nghiep, khac channel
    ap1 = net.addAccessPoint(
        "ap1",
        ssid="quackwf-corp",
        mode="g",
        channel="1",
        protocols="OpenFlow13",
        position="10,50,0",
    )
    ap2 = net.addAccessPoint(
        "ap2",
        ssid="quackwf-corp",
        mode="g",
        channel="6",
        protocols="OpenFlow13",
        position="50,50,0",
    )
    ap3 = net.addAccessPoint(
        "ap3",
        ssid="quackwf-corp",
        mode="g",
        channel="11",
        protocols="OpenFlow13",
        position="90,50,0",
    )

    info("*** 4. Tao cac may tram (Stations)\n")
    # Set IP va MAC giu nguyen de ban de dang test kach ban Hack
    sta1 = net.addStation(
        "sta1", ip="10.0.0.1/8", mac="02:00:00:00:01:00", position="10,40,0"
    )
    sta2 = net.addStation(
        "sta2", ip="10.0.0.2/8", mac="02:00:00:00:02:00", position="50,40,0"
    )
    sta3 = net.addStation(
        "sta3", ip="10.0.0.3/8", mac="02:00:00:00:03:00", position="80,40,0"
    )
    sta4 = net.addStation(
        "sta4", ip="10.0.0.4/8", mac="02:00:00:00:04:00", position="100,40,0"
    )

    info("*** 5. Cau hinh moi truong WiFi\n")
    net.setPropagationModel(model="logDistance", exp=4.5)
    net.configureWifiNodes()

    info("*** 6. Ket noi day mang (Wired Links)\n")
    # Noi 3 cuc AP vao Switch trung tam
    net.addLink(s1, ap1)
    net.addLink(s1, ap2)
    net.addLink(s1, ap3)

    info("*** 7. Ket noi WiFi (Wireless Links)\n")
    # Phan bo cac may tram vao cac AP
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap2)
    net.addLink(sta3, ap3)
    net.addLink(sta4, ap3)  # sta3 va sta4 cung dung chung ap3

    info("*** 8. Khoi dong mang\n")
    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    info("*** 9. Mo giao dien dong lenh (CLI)\n")
    CLI(net)

    info("*** 10. Tat mang sau khi thoat CLI\n")
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    topology()
