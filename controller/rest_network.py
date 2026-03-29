from ryu.app import wsgi
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from webob import Response
import json

network_api_name = "network_api_app"


class NetworkAPI(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {"wsgi": WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(NetworkAPI, self).__init__(*args, **kwargs)
        self.switches = {}

        wsgi = kwargs["wsgi"]
        wsgi.register(NetworkController, {network_api_name: self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath

    @set_ev_cls(ofp_event.EventOFPStateChange, MAIN_DISPATCHER)
    def state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.switches[datapath.id] = datapath
        elif ev.state is None:
            if datapath.id in self.switches:
                del self.switches[datapath.id]


class NetworkController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(NetworkController, self).__init__(req, link, data, **config)
        self.ryu_app = data[network_api_name]

    @route("switches", "/network/switches", methods=["GET"])
    def list_switches(self, req, **kwargs):
        switches = [hex(dpid) for dpid in self.ryu_app.switches.keys()]
        body = json.dumps({"active_switches": switches})
        return Response(content_type="application/json", body=body.encode("utf-8"))
