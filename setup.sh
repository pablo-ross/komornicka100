#!/bin/bash

# Script to set up directory structure and prepare for Komornicka 100

echo "Setting up Komornicka 100 system..."

# Create necessary directories
mkdir -p gpx
mkdir -p nginx/ssl
mkdir -p nginx/logs
mkdir -p pgadmin

# Copy example env files if they don't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env file from example. Please edit it with your settings."
fi

# Create frontend env file
if [ ! -f frontend/.env.local ]; then
  cp frontend/.env.local.example frontend/.env.local
  echo "Created frontend/.env.local file from example. Please edit it with your settings."
fi

# Copy pgAdmin servers.json if it doesn't exist
if [ ! -f pgadmin/servers.json ]; then
  cp pgadmin/servers.json.example pgadmin/servers.json 2>/dev/null || echo "Note: pgadmin/servers.json.example not found. Skipping."
fi

# Make scripts executable
chmod +x run.sh

# Create a sample GPX file if the directory is empty
if [ -z "$(ls -A gpx 2>/dev/null)" ]; then
  echo "GPX directory is empty. You need to add your route GPX files to the gpx/ directory."
  echo "Example: gpx/route1.gpx, gpx/route2.gpx, etc."
fi

# Set permissions
echo "Setting directory permissions..."
chmod -R 755 gpx
chmod -R 755 nginx

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your settings"
echo "2. Edit frontend/.env.local file with your settings"
echo "3. Add your GPX route files to the gpx/ directory"
echo "4. Run './run.sh dev' to start in development mode"
echo ""
echo "For production deployment:"
echo "1. Add SSL certificates in nginx/ssl/ directory (cert.pem and key.pem)"
echo "2. Run './run.sh prod' and follow the prompts"
echo ""