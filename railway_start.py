#!/usr/bin/env python3
"""
Railway startup script - reads PORT from environment and starts uvicorn
"""
import os
import subprocess
import sys

# Get PORT from environment, default to 8000
port = os.environ.get("PORT", "8000")

# Start uvicorn
cmd = [
    "uvicorn",
    "api.main:app",
    "--host", "0.0.0.0",
    "--port", port
]

print(f"Starting uvicorn on port {port}...")
sys.exit(subprocess.call(cmd))
