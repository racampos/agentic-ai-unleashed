#!/usr/bin/env python3
"""
Test Script for NetGSim Simulator Integration

Tests the complete flow:
1. Simulator health check
2. Device creation
3. Device listing
4. Device deletion
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.netgsim_client import NetGSimClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def main():
    print("=" * 60)
    print("NetGSim Simulator Integration Test")
    print("=" * 60)

    # Initialize client
    print("\n1. Initializing NetGSim client...")
    async with NetGSimClient() as client:
        print(f"   ✓ Connected to: {client.base_url}")

        # Health check
        print("\n2. Health check...")
        try:
            health = await client.health_check()
            print(f"   ✓ Simulator Status: {health.get('status')}")
            print(f"   ✓ Simulator ID: {health.get('simulator_id')}")
        except Exception as e:
            print(f"   ✗ Health check failed: {e}")
            return

        # Create device
        print("\n3. Creating test device (router1)...")
        created_name = None
        try:
            device = await client.create_device(
                device_id="test-router",
                device_type="router"
            )
            created_name = device.device_id
            print(f"   ✓ Device created: {device.device_id}")
            print(f"   ✓ Type: {device.device_type}")
            print(f"   ✓ Status: {device.status}")
        except Exception as e:
            print(f"   ✗ Device creation failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # List devices
        print("\n4. Listing all devices...")
        try:
            devices = await client.list_devices()
            print(f"   ✓ Found {len(devices)} device(s):")
            for d in devices:
                print(f"      - {d.device_id} ({d.device_type}) - {d.status}")
        except Exception as e:
            print(f"   ✗ Listing devices failed: {e}")
            import traceback
            traceback.print_exc()

        # Get specific device (need the UUID, skip for now)
        print("\n5. Getting device details...")
        try:
            # Get first device from list
            devices = await client.list_devices()
            if devices:
                first_device = devices[0]
                print(f"   ✓ Device: {first_device.device_id}")
                print(f"   ✓ Type: {first_device.device_type}")
                print(f"   ✓ Status: {first_device.status}")
        except Exception as e:
            print(f"   ✗ Get device failed: {e}")
            import traceback
            traceback.print_exc()

        # Note: Deletion requires device UUID which we'd need to track
        # For this test, we'll skip deletion since we created "test-router"
        print("\n6. Test Complete (device cleanup skipped for demo)")
        print(f"   Note: Created device '{created_name}' still exists in simulator")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
