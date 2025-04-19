#!/bin/bash
# Script to initialize GPX files in the database

# Check if running in Docker or locally
if [ -f "/.dockerenv" ]; then
  # Running in Docker container
  echo "Running in Docker container"
  cd /app
  python scripts/init_source_gpx.py "$@"
else
  # Running locally
  echo "Running locally"
  cd backend
  python scripts/init_source_gpx.py "$@"
fi