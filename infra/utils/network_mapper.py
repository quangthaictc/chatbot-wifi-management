import yaml
from utils.dpid import DPIDConverter


class NetworkMapper:
    def __init__(self, yaml_path="/app/network_config.yaml"):
        self.yaml_path = yaml_path
        self.mac_to_name = {}
        self.dpid_to_name = {}
        self._load_config()

    def _load_config(self):
        try:
            with open(self.yaml_path, "r") as file:
                config = yaml.safe_load(file)

            for sw in config.get("switches", []) + config.get("access_points", []):
                dpid_int = DPIDConverter.to_int(sw["dpid"])
                self.dpid_to_name[dpid_int] = sw["real_name"]

            for sta in config.get("stations", []):
                mac_lower = sta["mac"].lower()
                self.mac_to_name[mac_lower] = sta["real_name"]

        except Exception as e:
            print(f"Error read file {self.yaml_path}: {e}")

    def get_device_name(self, dpid: int) -> str:
        return self.dpid_to_name.get(dpid, f"Unknown-Device-{dpid}")

    def get_station_info(self, mac: str) -> str:
        mac_lower = mac.lower()
        name = self.mac_to_name.get(mac_lower, "Unknown-Station")
        return f"{name} ({mac_lower})"
