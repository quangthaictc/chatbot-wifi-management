import yaml
import httpx
from config.settings import FAST_API_URL


async def get_network_switches() -> dict:
    """
    Fetches the list of all active switches in the SDN network.

    Returns:
        A dictionary containing 'active_switches' (list of integer DPIDs) and 'total' count.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{FAST_API_URL}/switches/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def get_switch_stats(dpid: int) -> dict:
    """
    Retrieves network traffic statistics (rx/tx bytes and errors) for all ports on a specific switch.

    Args:
        dpid: The integer Datapath ID of the switch.

    Returns:
        A dictionary containing the switch DPID and a list of port statistics.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{FAST_API_URL}/switches/{dpid}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def get_switch_bandwidth(dpid: int) -> dict:
    """
    Calculates the real-time bandwidth usage (speed in Mbps) for all ports on a specific switch.
    This function takes exactly 1 second to execute to measure traffic over a time interval.
    Use this to check if the network is congested, if someone is downloading heavy files, or to detect DDoS.

    Args:
        dpid: The integer Datapath ID of the switch.

    Returns:
        A dictionary containing the DPID and real-time bandwidth stats (rx_mbps and tx_mbps) for each port.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(f"{FAST_API_URL}/switches/{dpid}/bandwidth")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def get_switch_flows(dpid: int) -> dict:
    """
    Retrieves the custom flow rules currently active on a specific switch.
    Useful for checking if certain IP or MAC addresses are being blocked or routed.

    Args:
        dpid: The integer Datapath ID of the switch.

    Returns:
        A dictionary containing the switch DPID, a list of active custom rules, and the total rule count.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{FAST_API_URL}/switches/{dpid}/flows")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def get_blocked_devices(dpid: int) -> dict:
    """
    Retrieves a list of MAC addresses that are currently blocked on a specific switch.

    Args:
        dpid: The integer Datapath ID of the switch.

    Returns:
        A dictionary containing the DPID, a list of blocked MAC addresses, and the total count.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{FAST_API_URL}/access/blocked/{dpid}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def block_device(dpid: int, mac_address: str) -> dict:
    """
    Blocks network access for a specific device based on its MAC address by adding a drop rule to the switch.

    Args:
        dpid: The integer Datapath ID of the switch where the rule will be applied.
        mac_address: The MAC address of the device to block (e.g., "00:00:00:00:00:01").

    Returns:
        A dictionary containing the action status and a confirmation message.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            payload = {"dpid": dpid, "mac_address": mac_address}
            response = await client.post(f"{FAST_API_URL}/access/block", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def unblock_device(dpid: int, mac_address: str) -> dict:
    """
    Unblocks a previously blocked device by removing the drop rule for its MAC address from the switch.

    Args:
        dpid: The integer Datapath ID of the switch.
        mac_address: The MAC address of the device to unblock.

    Returns:
        A dictionary containing the action status and a confirmation message.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.delete(
                f"{FAST_API_URL}/access/block/{dpid}/{mac_address}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def get_all_stations() -> dict:
    """
    Retrieves a list of all active stations (end-user devices/hosts) connected to the SDN network.

    Returns:
        A dictionary containing the total count of stations and a list of station details including MAC, IP, connected switch DPID, and port.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{FAST_API_URL}/stations/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def get_top_talkers(dpid: int, limit: int = 5) -> dict:
    """
    Identifies the top bandwidth-consuming devices (top talkers) on a specific switch.

    Args:
        dpid: The integer Datapath ID of the switch.
        limit: The maximum number of top talkers to return. Default is 5.

    Returns:
        A dictionary containing the DPID and a sorted list of top talkers with their source MAC/IP and byte count.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{FAST_API_URL}/stations/top-talkers/{dpid}?limit={limit}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


tools_list = [
    get_network_switches,
    get_switch_stats,
    get_switch_bandwidth,
    get_switch_flows,
    get_blocked_devices,
    block_device,
    unblock_device,
    get_all_stations,
    get_top_talkers,
]
