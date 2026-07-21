#!/usr/bin/env bash
# Convenience script to run the API locally with auto-reload.
#
# Usage: ./scripts/run_dev.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "No .env found — copying .env.example. Review and edit it before running in a real environment."
    cp .env.example .env
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
