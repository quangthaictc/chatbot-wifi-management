#!/bin/bash

service openvswitch-switch start

mn -c

python3 simulator/web_simulator.py

tail -f /dev/null

