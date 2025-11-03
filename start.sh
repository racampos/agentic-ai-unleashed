#!/bin/bash
# Railway startup script

# Railway provides PORT environment variable
PORT=${PORT:-8000}

# Start uvicorn
exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
