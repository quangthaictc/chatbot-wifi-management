#!/bin/bash

ryu-manager monitor_prometheus.py ryu.app.simple_switch_13 ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
