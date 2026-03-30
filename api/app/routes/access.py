from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from core.config import RYU_URL

router = APIRouter(prefix="/access", tags=["access"])


class AccessRequest(BaseModel):
    dpid: int
    mac_address: str


@router.get("/blocked/{dpid}")
async def get_blocked_devices(dpid: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/stats/flow/{dpid}")
            resp.raise_for_status()

            raw_data = resp.json()
            flows = raw_data.get(str(dpid), [])

            blocked_macs = []
            for flow in flows:
                match = flow.get("match", {})
                actions = flow.get("actions", [])

                # CHẾ BIẾN: Lọc các flow có độ ưu tiên cao nhất, match theo MAC nguồn và action rỗng (DROP)
                if flow.get("priority") == 65535 and "dl_src" in match and not actions:
                    blocked_macs.append(match["dl_src"])

            return {
                "dpid": dpid,
                "blocked_devices": blocked_macs,
                "total_blocked": len(blocked_macs),
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))


@router.post("/block")
async def block_device(req: AccessRequest):
    flow_data = {
        "dpid": req.dpid,
        "cookie": 1,
        "cookie_mask": 1,
        "table_id": 0,
        "priority": 65535,
        "match": {"dl_src": req.mac_address},
        "actions": [],
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{RYU_URL}/stats/flowentry/add", json=flow_data)
            resp.raise_for_status()
            return {
                "status": "success",
                "action": "block",
                "mac_address": req.mac_address,
                "message": f"The device with MAC address {req.mac_address} has been disconnected.",
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))


@router.delete("/block/{dpid}/{mac_address}")
async def unblock_device(dpid: int, mac_address: str):
    flow_data = {
        "dpid": dpid,
        "cookie": 1,
        "cookie_mask": 1,
        "table_id": 0,
        "priority": 65535,
        "match": {"dl_src": mac_address},
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{RYU_URL}/stats/flowentry/delete_strict", json=flow_data
            )
            resp.raise_for_status()
            return {
                "status": "success",
                "action": "unblock",
                "mac_address": mac_address,
                "message": f"Network connection has been restored for MAC {mac_address}.",
            }
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))
