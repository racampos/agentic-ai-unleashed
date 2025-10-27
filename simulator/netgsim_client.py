"""
NetGSim REST API client for device management.

This client handles device creation, retrieval, and deletion via the simulator's REST API.
It does NOT handle WebSocket connections - those are managed by the frontend browser.
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Device:
    """Represents a network device in the simulator."""
    device_id: str
    device_type: str
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class NetGSimClient:
    """
    REST API client for NetGSim simulator device management.

    This client is used by the backend agent to create and manage devices.
    WebSocket connections for CLI interaction are handled by the frontend.
    """

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize the NetGSim client.

        Args:
            base_url: Base URL of the simulator (defaults to SIMULATOR_BASE_URL env var)
            token: Authentication token (defaults to SIMULATOR_TOKEN env var)
        """
        self.base_url = base_url or os.getenv("SIMULATOR_BASE_URL")
        self.token = token or os.getenv("SIMULATOR_TOKEN")

        if not self.base_url:
            raise ValueError("SIMULATOR_BASE_URL must be set")
        if not self.token:
            raise ValueError("SIMULATOR_TOKEN must be set")

        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip("/")

        # Create async HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

        logger.info(f"Initialized NetGSim client for {self.base_url}")

    async def create_device(
        self,
        device_id: str,
        device_type: str,
        config: Optional[Dict[str, Any]] = None,
        hardware: Optional[str] = None
    ) -> Device:
        """
        Create a new network device in the simulator.

        Args:
            device_id: Unique identifier for the device (e.g., "router1", "switch1")
            device_type: Type of device (e.g., "router", "switch", "host")
            config: Optional device configuration (startup config, interfaces, etc.)
            hardware: Hardware platform (e.g., "cisco_2911", "cisco_4321", "cisco_2960", "host")
                     If not specified, defaults based on device_type

        Returns:
            Device object with creation details

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        # Default hardware platforms based on device type
        if not hardware:
            hardware_map = {
                "router": "cisco_2911",
                "switch": "cisco_2960",
                "host": "host",
            }
            hardware = hardware_map.get(device_type, "cisco_2911")

        payload = {
            "type": device_type,
            "name": device_id,
            "hardware": hardware
        }

        if config:
            payload["config"] = config

        logger.info(f"Creating device: {device_id} (type: {device_type}, hardware: {hardware})")

        response = await self.client.post(
            f"{self.base_url}/api/v1/devices",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        created_id = data.get("id")
        logger.info(f"Device created successfully: {device_id} (ID: {created_id})")

        return Device(
            device_id=device_id,
            device_type=device_type,
            config=config,
            status="created"
        )

    async def get_device(self, device_id: str) -> Device:
        """
        Get information about a specific device.

        Args:
            device_id: UUID of the device

        Returns:
            Device object with current details

        Raises:
            httpx.HTTPStatusError: If device not found or request fails
        """
        logger.debug(f"Fetching device: {device_id}")

        response = await self.client.get(
            f"{self.base_url}/api/v1/devices/{device_id}"
        )
        response.raise_for_status()

        data = response.json()

        return Device(
            device_id=data.get("name", data["id"]),
            device_type=data["type"],
            config=data.get("config"),
            status=data.get("status")
        )

    async def list_devices(self) -> List[Device]:
        """
        List all devices in the simulator.

        Returns:
            List of Device objects

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug("Listing all devices")

        response = await self.client.get(
            f"{self.base_url}/api/v1/devices"
        )
        response.raise_for_status()

        # Response is a list of devices directly
        devices = response.json()

        return [
            Device(
                device_id=d.get("name", d["id"]),
                device_type=d["type"],
                config=d.get("config"),
                status=d.get("status")
            )
            for d in devices
        ]

    async def delete_device(self, device_id: str) -> bool:
        """
        Delete a device from the simulator.

        Args:
            device_id: Unique identifier of the device to delete

        Returns:
            True if deletion was successful

        Raises:
            httpx.HTTPStatusError: If device not found or request fails
        """
        logger.info(f"Deleting device: {device_id}")

        response = await self.client.delete(
            f"{self.base_url}/api/v1/devices/{device_id}"
        )
        response.raise_for_status()

        logger.info(f"Device deleted successfully: {device_id}")
        return True

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the simulator is healthy and responsive.

        Returns:
            Health status dictionary

        Raises:
            httpx.HTTPStatusError: If the health check fails
        """
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.info("NetGSim client closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
