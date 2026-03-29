from fastapi import APIRouter, HTTPException
import httpx

from core.config import RYU_URL

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/status")
async def get_network_status():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RYU_URL}/network")
            response.raise_for_status()
            data = response.json()

            switches = data.get("active_switches", [])
            return {
                "total_switches": len(switches),
                "switch_list": switches,
                "status": "active" if switches else "no_switches_connected",
            }
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Cannot connect to Ryu: {exc}")


@router.get("/topology")
async def get_topology():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RYU_URL}/v1.0/topology/switches")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
