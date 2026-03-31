from fastapi import APIRouter, HTTPException
import httpx

from utils.dpid import DPIDConverter
from utils.network_mapper import NetworkMapper
from core.config import RYU_URL

router = APIRouter(prefix="/stations", tags=["stations"])
mapper = NetworkMapper()


@router.get("/")
async def get_all_stations():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/v1.0/topology/hosts")
            resp.raise_for_status()

            raw_hosts = resp.json()
            active_stations = []

            for host in raw_hosts:
                port_info = host.get("port", {})
                active_stations.append(
                    {
                        "device_name": mapper.get_station_info(host.get("mac")),
                        "mac_address": host.get("mac"),
                        "ip_addresses": host.get("ipv4", []),
                        "connected_to_dpid": DPIDConverter.to_int(
                            port_info.get("dpid")
                        ),
                        "dpid_device_name": mapper.get_device_name(
                            DPIDConverter.to_int(port_info.get("dpid"))
                        ),
                        "connected_port": port_info.get("port_no"),
                    }
                )

            return {"total_stations": len(active_stations), "stations": active_stations}
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))


@router.get("/top-talkers/{dpid}")
async def get_top_talkers(dpid: int, limit: int = 5):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/stats/flow/{dpid}")
            resp.raise_for_status()

            raw_data = resp.json()
            flows = raw_data.get(str(dpid), [])

            talkers = []
            for flow in flows:
                match = flow.get("match", {})
                if flow.get("priority") > 0 and (
                    "nw_src" in match or "dl_src" in match
                ):
                    source = match.get("nw_src") or match.get("dl_src")
                    talkers.append(
                        {
                            "source": source,
                            "device_name": mapper.get_station_info(source),
                            "byte_count": flow.get("byte_count", 0),
                            "packet_count": flow.get("packet_count", 0),
                        }
                    )

            talkers.sort(key=lambda x: x["byte_count"], reverse=True)
            top_talkers = talkers[:limit]

            return {
                "dpid": dpid,
                "dpid_device_name": mapper.get_device_name(dpid),
                "top_talkers": top_talkers,
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))
