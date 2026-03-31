from fastapi import APIRouter, HTTPException
import httpx
from utils.network_mapper import NetworkMapper
from utils.dpid import DPIDConverter

from core.config import RYU_URL
import asyncio

router = APIRouter(prefix="/switches", tags=["switches"])
mapper = NetworkMapper()


@router.get("/")
async def get_all_switches():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/v1.0/topology/switches")
            resp.raise_for_status()

            raw_data = resp.json()
            switches = [DPIDConverter.to_int(switch.get("dpid")) for switch in raw_data]

            return {"active_switches": switches, "total": len(switches)}
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))


@router.get("/{dpid}")
async def get_switch_stats(dpid: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/stats/port/{dpid}")
            resp.raise_for_status()

            raw_data = resp.json()
            port_stats = raw_data.get(str(dpid), [])

            clean_stats = []
            for port in port_stats:
                if port.get("port_no") != "LOCAL":
                    clean_stats.append(
                        {
                            "port_id": port.get("port_no"),
                            "rx_bytes": port.get("rx_bytes"),
                            "tx_bytes": port.get("tx_bytes"),
                            "rx_errors": port.get("rx_errors"),
                            "tx_errors": port.get("tx_errors"),
                        }
                    )
            print(f"==================================={DPIDConverter.to_hex(dpid)}")
            return {
                "dpid": dpid,
                "dpid_device_name": mapper.get_device_name(dpid),
                "ports": clean_stats,
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))


@router.get("/{dpid}/bandwidth")
async def get_switch_bandwidth(dpid: int):
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp1 = await client.get(f"{RYU_URL}/stats/port/{dpid}")
            resp1.raise_for_status()
            data1 = resp1.json().get(str(dpid), [])

            await asyncio.sleep(1.0)

            resp2 = await client.get(f"{RYU_URL}/stats/port/{dpid}")
            resp2.raise_for_status()
            data2 = resp2.json().get(str(dpid), [])

            bandwidth_stats = []

            for p1, p2 in zip(data1, data2):
                if p1.get("port_no") != "LOCAL":
                    delta_rx_bytes = p2.get("rx_bytes", 0) - p1.get("rx_bytes", 0)
                    delta_tx_bytes = p2.get("tx_bytes", 0) - p1.get("tx_bytes", 0)

                    rx_mbps = round((delta_rx_bytes * 8) / 1_000_000, 2)
                    tx_mbps = round((delta_tx_bytes * 8) / 1_000_000, 2)

                    bandwidth_stats.append(
                        {
                            "port_id": p1.get("port_no"),
                            "rx_mbps": rx_mbps,  # Download speeds
                            "tx_mbps": tx_mbps,  # Upload speeds
                        }
                    )

            return {
                "dpid": dpid,
                "dpid_device_name": mapper.get_device_name(dpid),
                "bandwidth": bandwidth_stats,
            }

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))


@router.get("/{dpid}/flows")
async def get_switch_flows(dpid: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/stats/flow/{dpid}")
            resp.raise_for_status()

            raw_data = resp.json()
            flows = raw_data.get(str(dpid), [])

            # CHẾ BIẾN: Chỉ lấy các flow do người dùng tự thêm (priority != 0)
            # Giúp AI không bị rối bởi các luật mặc định (table-miss) của switch
            custom_rules = []
            for flow in flows:
                if flow.get("priority") > 0:
                    custom_rules.append(
                        {
                            "priority": flow.get("priority"),
                            "match": flow.get("match"),  # Chứa MAC/IP bị chặn
                            "actions": flow.get(
                                "actions"
                            ),  # Hành động (DROP, OUTPUT...)
                            "packet_count": flow.get("packet_count"),
                        }
                    )

            return {
                "dpid": dpid,
                "dpid_device_name": mapper.get_device_name(dpid),
                "active_custom_rules": custom_rules,
                "total_rules": len(custom_rules),
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))
