import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from schemas.alert import Alert
import httpx

from core.config import TELEGRAM_API_TOKEN, ADMIN_ID, RYU_URL

router = APIRouter(prefix="/security", tags=["security"])

alert_states = {}
minutes = 5


async def auto_block_task(alert_id: str, dpid: int, mac: str):
    """
    Subtask auto block after 5 minutes (300 seconds)
    """
    await asyncio.sleep(minutes * 60)

    if alert_states.get(alert_id) == "pending":
        # If the admin hasn't taken any action yet, the MAC address will be automatically blocked.
        flow_data = {
            "dpid": dpid,
            "cookie": 1,
            "cookie_mask": 1,
            "table_id": 0,
            "priority": 65535,
            "match": {"dl_src": mac},
            "actions": [],
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            await client.post(f"{RYU_URL}/stats/flowentry/add", json=flow_data)

            # Send message to Telegram
            msg = f"TIMEOUT REACHED ({minutes} MINUTES)\nThe system has AUTOMATICALLY BLOCKED MAC {mac} to ensure security!"
            url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage"
            await client.post(
                url, json={"chat_id": ADMIN_ID, "text": msg, "parse_mode": "Markdown"}
            )

        # Update state
        alert_states[alert_id] = "auto_blocked"


@router.post("/alert")
async def trigger_security_alert(payload: Alert, bg_tasks: BackgroundTasks):
    alert_id = f"{payload.dpid}_{payload.attacker_mac}"
    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage"

    async with httpx.AsyncClient(timeout=20.0) as client:
        if payload.severity == "CRITICAL":
            # CASE 1: CRITICAL ATTACK, block now.
            flow_data = {
                "dpid": payload.dpid,
                "table_id": 0,
                "priority": 65535,
                "match": {"dl_src": payload.attacker_mac},
                "actions": [],
            }
            await client.post(f"{RYU_URL}/stats/flowentry/add", json=flow_data)

            message = (
                f"*CRITICAL*\n\n"
                f"*Attack type:* {payload.attack_type}\n"
                f"*MAC:* `{payload.attacker_mac}`\n\n"
                f"*Action:* MAC addresses have been automatically blocked.."
            )
            await client.post(
                telegram_api_url,
                json={"chat_id": ADMIN_ID, "text": message, "parse_mode": "Markdown"},
            )

        else:
            # CASE 2: NORMAL ATTACK, send message with 2 buttons Skip and Block.
            alert_states[alert_id] = "pending"
            message = (
                f"*WARNING*\n\n"
                f"*Attack type:* {payload.attack_type}\n"
                f"*MAC:* `{payload.attacker_mac}`\n\n"
                f"Please issue a command; if this message is ignored, the system will automatically block this MAC address after {minutes} minutes!"
            )

            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "Block",
                            "callback_data": f"secblock_{payload.dpid}_{payload.attacker_mac}",
                        },
                        {
                            "text": "Skip",
                            "callback_data": f"secignore_{payload.dpid}_{payload.attacker_mac}",
                        },
                    ]
                ]
            }

            await client.post(
                telegram_api_url,
                json={
                    "chat_id": ADMIN_ID,
                    "text": message,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard,
                },
            )

            # Calling auto block
            bg_tasks.add_task(
                auto_block_task, alert_id, payload.dpid, payload.attacker_mac
            )

    return {"status": "success"}


@router.post("/resolve/{dpid}/{mac}/{action}")
async def resolve_alert(dpid: int, mac: str, action: str):
    alert_id = f"{dpid}_{mac}"
    if alert_id in alert_states:
        alert_states[alert_id] = action
    return {"status": "resolved"}
