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
    device_id: str  # UUID from the simulator API
    device_type: str
    name: Optional[str] = None  # Human-readable device name
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

    async def create_device_from_config(self, device_config: Dict[str, Any]) -> Device:
        """
        Create a device by posting the config dictionary as-is to the simulator.
        This matches the SIMULATOR_TOPOLOGY_CREATION.py approach.

        Args:
            device_config: Complete device configuration dictionary from topology YAML
                          (must include: type, name, hardware, and optionally: device_id, config, debug)

        Returns:
            Device object with creation details

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        device_name = device_config.get("name", "unknown")
        device_type = device_config.get("type", "unknown")

        logger.info(f"Creating device from config: {device_name} (type: {device_type})")

        response = await self.client.post(
            f"{self.base_url}/api/v1/devices",
            json=device_config
        )
        response.raise_for_status()

        data = response.json()
        created_id = data.get("id")
        logger.info(f"Device created successfully: {device_name} (ID: {created_id})")

        return Device(
            device_id=created_id or device_config.get("device_id", device_name),
            device_type=device_type,
            name=device_name,
            config=device_config.get("config"),
            status="created"
        )

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
            device_id=created_id or device_id,
            device_type=device_type,
            name=device_id,
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
            device_id=data["id"],  # Use the UUID
            device_type=data["type"],
            name=data.get("name"),  # Separate name field
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
                device_id=d["id"],  # Use the UUID for API operations
                device_type=d["type"],
                name=d.get("name"),  # Separate name field for display
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

    async def get_interfaces(self) -> List[Dict[str, Any]]:
        """
        Get all registered interfaces in the topology.

        Returns:
            List of interface dictionaries with 'interface_id' and other properties

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug("Fetching registered interfaces")

        response = await self.client.get(
            f"{self.base_url}/api/v1/topology/interfaces"
        )
        response.raise_for_status()

        return response.json()

    async def get_connections(self) -> List[Dict[str, Any]]:
        """
        Get all connections in the topology.

        Returns:
            List of connection dictionaries

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug("Fetching topology connections")

        response = await self.client.get(
            f"{self.base_url}/api/v1/topology/connections"
        )
        response.raise_for_status()

        return response.json()

    async def create_connection(
        self,
        name: str,
        endpoints: List[str],
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a connection between network interfaces.

        Args:
            name: Name for the connection (e.g., "Network1")
            endpoints: List of interface IDs in format "device_id:device_name:interface_name"
            properties: Optional connection properties (latency_ms, packet_loss_percent, etc.)

        Returns:
            Created connection dictionary

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        payload = {
            "name": name,
            "endpoints": endpoints
        }

        if properties:
            payload["properties"] = properties

        logger.info(f"Creating connection: {name} with {len(endpoints)} endpoints")

        response = await self.client.post(
            f"{self.base_url}/api/v1/topology/connections",
            json=payload
        )
        response.raise_for_status()

        logger.info(f"Connection created successfully: {name}")
        return response.json()

    async def delete_connection(self, connection_id: str) -> bool:
        """
        Delete a connection from the topology.

        Args:
            connection_id: Unique identifier of the connection to delete

        Returns:
            True if deletion was successful

        Raises:
            httpx.HTTPStatusError: If connection not found or request fails
        """
        logger.info(f"Deleting connection: {connection_id}")

        response = await self.client.delete(
            f"{self.base_url}/api/v1/topology/connections/{connection_id}"
        )
        response.raise_for_status()

        logger.info(f"Connection deleted successfully: {connection_id}")
        return True

    async def execute_command(
        self,
        device_id: str,
        command: str
    ) -> Dict[str, Any]:
        """
        Execute a CLI command on a device.

        Args:
            device_id: The UUID of the device
            command: The command to execute (e.g., "show running-config")

        Returns:
            Dictionary containing the command output

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug(f"Executing CLI command on device {device_id}: {command}")

        response = await self.client.post(
            f"{self.base_url}/api/v1/devices/{device_id}/cli",
            json={
                "trigger": "enter",
                "text": command,
                "non_interactive": True
            }
        )
        response.raise_for_status()

        return response.json()

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
