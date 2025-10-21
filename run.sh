#!/bin/bash
set -a

if [ ! -f .env ]; then
  echo "[ERROR] .env file not found!"
  exit 1
fi

source .env

set +a

echo "Starting Uvicorn server at ${SERVER_HOST}:${SERVER_PORT} ..."
uv run -m uvicorn main:app --host "$SERVER_HOST" --port "$SERVER_PORT" --reload