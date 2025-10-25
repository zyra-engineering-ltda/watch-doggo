#!/bin/bash

# Service Status Monitor - Startup Script
# This script sets up the environment and starts the Flask application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Service Status Monitor - Startup Script${NC}"
echo "========================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is not installed or not in PATH${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if configuration file exists
if [ ! -f "config/services.json" ]; then
    echo -e "${RED}Error: Configuration file config/services.json not found${NC}"
    echo "Please create the configuration file before starting the application."
    exit 1
fi

# Set environment variables if not already set
export FLASK_APP=wsgi.py
export FLASK_ENV=${FLASK_ENV:-production}
export FLASK_HOST=${FLASK_HOST:-127.0.0.1}
export FLASK_PORT=${FLASK_PORT:-5000}
export FLASK_DEBUG=${FLASK_DEBUG:-False}

echo -e "${GREEN}Starting Service Status Monitor...${NC}"
echo "Host: $FLASK_HOST"
echo "Port: $FLASK_PORT"
echo "Debug: $FLASK_DEBUG"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the application${NC}"
echo ""

# Start the application
python -m flask run --host=$FLASK_HOST --port=$FLASK_PORT