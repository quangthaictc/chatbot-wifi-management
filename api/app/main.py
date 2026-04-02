#!/usr/bin/env python

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import httpx
from routes import access, stations, switches, security
from core.config import RYU_URL

from utils.logger_config import get_logger

app = FastAPI(title="QuackWF API", version="1.0.0")

app.include_router(access.router)
app.include_router(stations.router)
app.include_router(switches.router)
app.include_router(security.router)

logger = get_logger("FastAPI")


@app.get("/network/overview", tags=["network"])
async def get_network_overview():
    async with httpx.AsyncClient() as client:
        try:
            switches_task = client.get(f"{RYU_URL}/v1.0/topology/switches")
            links_task = client.get(f"{RYU_URL}/v1.0/topology/links")

            switches_resp, links_resp = await asyncio.gather(switches_task, links_task)

            switches_resp.raise_for_status()
            links_resp.raise_for_status()

            logger.info(f"HTTP GET: 200 - /network/overview")
            return {"switches": switches_resp.json(), "links": links_resp.json()}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP GET: {e.response.status_code} - {e.request.url}")


@app.get("/health", tags=["system"])
async def health_check():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{RYU_URL}/stats/switches")
            resp.raise_for_status()
            logger.info(f"HTTP GET: 200 - /network/health")
            return {"status": "healthy", "ryu_connected": True}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP GET: {e.response.status_code} - {e.request.url}")
            return {"status": "unhealthy", "ryu_connected": False}
