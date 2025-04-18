#!/bin/bash

# Script to run Komornicka 100 in development or production mode

# Function to display usage information
function show_usage {
  echo "Usage: $0 [dev|prod]"
  echo "  dev  - Start in development mode"
  echo "  prod - Start in production mode"
  exit 1
}

# Function to check if Docker is running
function check_docker {
  if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
  fi
}

# Function to check if .env files exist
function check_env_files {
  if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and edit it."
    exit 1
  fi
  
  if [ ! -f frontend/.env.local ]; then
    echo "Error: frontend/.env.local file not found. Please copy frontend/.env.local.example to frontend/.env.local and edit it."
    exit 1
  fi
}

# Function to check if Docker network exists
function check_network {
  if ! docker network inspect k100 > /dev/null 2>&1; then
    echo "Creating Docker network 'k100'..."
    docker network create -d bridge k100
  fi
}

# Function to stop running containers
function stop_containers {
  echo "Stopping any running KMTB containers..."
  docker compose down
}

# Main script

# Check arguments
if [ $# -ne 1 ]; then
  show_usage
fi

# Check if Docker is running
check_docker

# Check if .env files exist
check_env_files

# Check if Docker network exists
check_network

# Process the command
case $1 in
  dev)
    echo "Starting Komornicka 100 in DEVELOPMENT mode..."
    stop_containers
    docker compose up -d
    echo "Development environment started! Access it at:"
    echo "  Frontend: http://localhost:3000"
    echo "  API: http://localhost:8000"
    echo "  Mailpit: http://localhost:8025"
    echo "  PgAdmin: http://localhost:5050"
    ;;
    
  prod)
    echo "Starting Komornicka 100 in PRODUCTION mode..."
    stop_containers
    docker compose -f docker-compose.prod.yml up -d
    echo "Production environment started! Access it at:"
    echo "  Frontend: https://k100.komornikimtb.pl"
    ;;
    
  *)
    show_usage
    ;;
esac

exit 0