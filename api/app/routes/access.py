from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from utils.network_mapper import NetworkMapper
from utils.logger_config import get_logger

from core.config import RYU_URL

router = APIRouter(prefix="/access", tags=["access"])
mapper = NetworkMapper()
logger = get_logger("FastAPI")


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

                # Filter highest priority, match by src MAC and null action (DROP)
                if flow.get("priority") == 65535 and "dl_src" in match and not actions:
                    blocked_macs.append(
                        f"{mapper.get_station_info(match['dl_src'])} - {match['dl_src']}"
                    )

            logger.info(f"HTTP GET: 200 - /access/blocked/{dpid}")
            return {
                "dpid": dpid,
                "location": mapper.get_device_name(dpid),
                "blocked_devices": blocked_macs,
                "total_blocked": len(blocked_macs),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP GET: {e.response.status_code} - {e.request.url}")


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

            logger.info(
                f"HTTP POST: 200 - /access/block?dpid={req.dpid}&mac_address={req.mac_address}"
            )
            return {
                "status": "success",
                "action": "block",
                "message": f"The device {mapper.get_station_info(req.mac_address)} with MAC address {req.mac_address} has been disconnected.",
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP POST: {e.response.status_code} - {e.request.url}")


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
            logger.info(f"HTTP DELETE: 200 - /access/block/{dpid}/{mac_address}")
            return {
                "status": "success",
                "action": "unblock",
                "message": f"Network connection has been restored for device {mapper.get_station_info(mac_address)} - {mac_address}.",
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP DELETE: {e.response.status_code} - {e.request.url}")
