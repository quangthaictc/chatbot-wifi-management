import httpx
from config.settings import RYU_URL


async def get_network_switches():
    """
    Fetches the current switches of the SDN network by retrieving active switches from the Ryu controller.

    This function calls the internal Ryu API to get a list of all currently
    connected OpenFlow switches identified by their hexadecimal Datapath IDs (DPIDs).

    Returns:
        A dictionary containing:
            - 'active_switches': A list of strings representing switch DPIDs in hex format (e.g., ["0x1", "0x2"]).
            - 'error': A string message if the connection to the Ryu controller fails.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RYU_URL}/stats/switches")
            return response.json()
        except Exception as e:
            return {"error": f"Can't connected to Ryu: {str(e)}"}


tools_list = [get_network_switches]
