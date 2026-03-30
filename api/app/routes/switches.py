from fastapi import APIRouter, HTTPException
import httpx
from utils.dpid import DPIDConverter
from core.config import RYU_URL

router = APIRouter(prefix="/switches", tags=["switches"])


@router.get("/")
async def get_all_switches():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/v1.0/topology/switches")
            resp.raise_for_status()

            # CHẾ BIẾN: Chỉ lấy ID của các Switch, bỏ qua các thông số rườm rà của cổng
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

            # CHẾ BIẾN: Lọc bỏ port "LOCAL" (port ảo của Ryu), chỉ giữ lại thông số rx/tx cơ bản
            clean_stats = []
            for port in port_stats:
                if port.get("port_no") != "LOCAL":
                    clean_stats.append(
                        {
                            "port_id": port.get("port_no"),
                            "rx_bytes": port.get("rx_bytes"),  # Dữ liệu nhận
                            "tx_bytes": port.get("tx_bytes"),  # Dữ liệu gửi
                            "rx_errors": port.get("rx_errors"),
                            "tx_errors": port.get("tx_errors"),
                        }
                    )

            return {"dpid": dpid, "ports": clean_stats}
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
                "active_custom_rules": custom_rules,
                "total_rules": len(custom_rules),
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))
