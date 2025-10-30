"""
Tools for the AI Tutor Agent

These tools allow the LLM to actively retrieve information about
the network simulator state and device configurations.
"""

import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


# Global simulator client - will be set by main.py
_simulator_client = None


def set_simulator_client(client):
    """Set the global simulator client for tools to use."""
    global _simulator_client
    _simulator_client = client


async def get_device_running_config_impl(device_name: str) -> str:
    """
    Internal implementation to retrieve the current running configuration for a network device.

    Args:
        device_name: The name of the device (e.g., "Floor14", "Room-145")

    Returns:
        The device's running configuration as a string, or an error message
    """
    if not _simulator_client:
        return "Error: Simulator client not available. Cannot retrieve device configuration."

    try:
        # Get devices to find the device_id for the given name
        logger.info(f"[Tool] Looking up device_id for device name: {device_name}")
        devices = await _simulator_client.list_devices()

        # Find device by name
        target_device = None
        for device in devices:
            if device.name and device.name.lower() == device_name.lower():
                target_device = device
                break

        if not target_device:
            # Return helpful error with available devices
            available_names = [d.name or "?" for d in devices]
            return f"Error: Device '{device_name}' not found. Available devices: {', '.join(available_names)}"

        device_id = target_device.device_id
        logger.info(f"[Tool] Found device_id {device_id} for {device_name}")

        # Execute "show running-config" command
        logger.info(f"[Tool] Fetching running-config for {device_name} ({device_id})")
        result = await _simulator_client.execute_command(
            device_id=device_id,
            command="show running-config"
        )

        config = result.get("content", "")
        if not config:
            return f"Error: No configuration returned for device '{device_name}'"

        logger.info(f"[Tool] Successfully retrieved running-config for {device_name} ({len(config)} chars)")
        return config

    except httpx.HTTPStatusError as e:
        error_msg = f"Error retrieving configuration for '{device_name}': {e.response.status_code} {e.response.reason_phrase}"
        logger.error(f"[Tool] {error_msg}")
        return error_msg
    except Exception as e:
        import traceback
        error_msg = f"Error retrieving configuration for '{device_name}': {str(e)}"
        logger.error(f"[Tool] {error_msg}")
        logger.error(f"[Tool] Traceback: {traceback.format_exc()}")
        return error_msg


# OpenAI function calling tool definition
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_device_running_config",
            "description": "Retrieve the current running configuration for a network device. Use this when you need to see the actual configuration state of a device (IP addresses, routing, VLANs, passwords, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "The name of the device (e.g., 'Floor14', 'Room-145')"
                    }
                },
                "required": ["device_name"],
                "additionalProperties": False
            }
        }
    }
]


# Map of tool names to implementation functions
TOOL_IMPLEMENTATIONS = {
    "get_device_running_config": get_device_running_config_impl
}
