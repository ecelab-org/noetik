#!/bin/bash

# NOETIK - Docker container starter script
# This script checks for Docker dependencies and starts the Noetik container

# Terminal colors
RED='\033[0;91m'
GREEN='\033[0;92m'
BLUE='\033[0;94m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default mode
MODE="api"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --mode|-m) MODE="$2"; shift ;;
        --help|-h)
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode, -m MODE    Run in 'cli', 'api', or 'web' mode (default: api)"
            echo "  --help, -h         Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Validate mode
if [[ "$MODE" != "cli" && "$MODE" != "api" && "$MODE" != "web" ]]; then
    echo -e "${RED}Error: Invalid mode '$MODE'. Use 'cli', 'api', or 'web'.${NC}"
    exit 1
fi

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}     NOETIK - AI Orchestration System    ${NC}"
echo -e "${GREEN}     Running in ${MODE} mode             ${NC}"
echo -e "${GREEN}=========================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    echo -e "${YELLOW}Please install Docker from https://docs.docker.com/get-started/get-docker/${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose plugin is not installed${NC}"
    echo -e "${YELLOW}Please install Docker Compose plugin${NC}"
    exit 1
fi

# Check if .env file exists, create from template if it doesn't
if [ ! -f .env ]; then
    echo -e "${YELLOW}Notice: No .env file found${NC}"
    if [ -f .env.template ]; then
        echo -e "${GREEN}Creating .env file from template...${NC}"
        cp .env.template .env
        echo -e "${YELLOW}Please edit .env file with your configuration before running again${NC}"
        exit 1
    else
        echo -e "${YELLOW}Warning: No .env.template found. Creating minimal .env file...${NC}"
        echo "PORT=8000" > .env
    fi
fi

# Create a checksum of dependency files
DEPS_FILES="pyproject.toml Dockerfile"
[ -f poetry.lock ] && DEPS_FILES="$DEPS_FILES poetry.lock"

# Calculate current checksum
CURRENT_CHECKSUM=$(cat $DEPS_FILES 2>/dev/null | sha256sum | cut -d ' ' -f 1)
CHECKSUM_FILE=".deps_checksum"

# Check if we need to rebuild
REBUILD=0
if [ ! -f $CHECKSUM_FILE ]; then
    # First run or checksum file was deleted
    echo -e "${YELLOW}No dependency checksum found. Will build container.${NC}"
    REBUILD=1
elif [ "$(cat $CHECKSUM_FILE 2>/dev/null)" != "$CURRENT_CHECKSUM" ]; then
    # Dependencies have changed
    echo -e "${YELLOW}Dependencies have changed. Rebuilding container...${NC}"
    REBUILD=1
else
    echo -e "${GREEN}Dependencies unchanged. Using existing container.${NC}"
fi

echo -e "${GREEN}Starting Noetik container in ${MODE} mode...${NC}"

if [ $REBUILD -eq 1 ]; then
    # Build the container
    docker compose build noetik
    # Save new checksum
    echo "$CURRENT_CHECKSUM" > $CHECKSUM_FILE
fi

# Run the container with the selected mode
docker compose run --service-ports --rm noetik python -m noetik.main --mode $MODE --log-level warning

# This part will execute when docker-compose is terminated
echo -e "${GREEN}Noetik container stopped.${NC}"
