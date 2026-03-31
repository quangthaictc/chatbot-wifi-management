#!/usr/bin/env python

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from utils.draw_network import generate_network_diagram
import httpx
from routes import access, stations, switches, security
from core.config import RYU_URL

app = FastAPI(title="QuackWF API", version="1.0.0")

app.include_router(access.router)
app.include_router(stations.router)
app.include_router(switches.router)
app.include_router(security.router)


@app.get("/network/overview", tags=["network"])
async def get_network_overview():
    async with httpx.AsyncClient() as client:
        try:
            switches_task = client.get(f"{RYU_URL}/v1.0/topology/switches")
            links_task = client.get(f"{RYU_URL}/v1.0/topology/links")

            switches_resp, links_resp = await asyncio.gather(switches_task, links_task)

            switches_resp.raise_for_status()
            links_resp.raise_for_status()

            return {"switches": switches_resp.json(), "links": links_resp.json()}
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.get("/network/diagram", tags=["network"])
async def get_network_diagram_image():
    # Gọi lại hàm lấy JSON của bạn
    topo_data = await get_network_overview()

    # Đưa JSON cho hàm vẽ ảnh
    image_path = generate_network_diagram(topo_data)

    # FastAPI trả thẳng file ảnh này về cho client (Telegram Bot)
    return FileResponse(
        image_path, media_type="image/png", filename="network_diagram.png"
    )


@app.get("/health", tags=["system"])
async def health_check():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/stats/switches")
            resp.raise_for_status()
            return {"status": "healthy", "ryu_connected": True}
        except httpx.RequestError:
            return {"status": "unhealthy", "ryu_connected": False}
