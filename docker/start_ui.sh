#!/bin/bash
# Quick start script for HIVEC-CM Web Interface

echo "═══════════════════════════════════════════════════════════════════"
echo "HIVEC-CM Web Interface - Quick Start"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Get the project root directory (parent of docker folder)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker found"

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose -f docker/docker-compose.yml"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose -f docker/docker-compose.yml"
else
    echo "❌ Docker Compose is not available."
    exit 1
fi

echo "✓ Docker Compose found"
echo ""

# Show menu
echo "Select an option:"
echo "1. Build and start the web interface"
echo "2. Start existing container"
echo "3. Stop the container"
echo "4. View logs"
echo "5. Rebuild from scratch"
echo "6. Run locally (without Docker)"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "Building and starting HIVEC-CM Web Interface..."
        $COMPOSE_CMD up -d --build
        echo ""
        echo "✅ Web interface is starting!"
        echo "🌐 Open your browser and go to: http://localhost:8501"
        echo ""
        echo "To view logs: $COMPOSE_CMD logs -f"
        echo "To stop: $COMPOSE_CMD down"
        ;;
    2)
        echo ""
        echo "Starting HIVEC-CM Web Interface..."
        $COMPOSE_CMD up -d
        echo ""
        echo "✅ Web interface started!"
        echo "🌐 Open your browser and go to: http://localhost:8501"
        ;;
    3)
        echo ""
        echo "Stopping HIVEC-CM Web Interface..."
        $COMPOSE_CMD down
        echo "✅ Stopped"
        ;;
    4)
        echo ""
        echo "Showing logs (Ctrl+C to exit)..."
        $COMPOSE_CMD logs -f
        ;;
    5)
        echo ""
        echo "Rebuilding from scratch..."
        $COMPOSE_CMD down -v
        $COMPOSE_CMD build --no-cache
        $COMPOSE_CMD up -d
        echo ""
        echo "✅ Rebuilt and started!"
        echo "🌐 Open your browser and go to: http://localhost:8501"
        ;;
    6)
        echo ""
        echo "Running locally without Docker..."
        echo ""
        
        # Check if virtual environment exists
        if [ ! -d ".venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv .venv
        fi
        
        # Activate virtual environment
        source .venv/bin/activate
        
        # Install requirements
        echo "Installing requirements..."
        pip install -r requirements.txt
        pip install streamlit plotly
        
        echo ""
        echo "Starting Streamlit..."
        streamlit run ui/app.py
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
