# Docker Deployment

This folder contains Docker configuration files for containerized deployment of the HIVEC-CM web interface.

## Files

- **Dockerfile** - Docker image definition for the web UI
- **docker-compose.yml** - Docker Compose orchestration configuration
- **start_ui.sh** - Interactive helper script for Docker operations

## Quick Start

### Using the Helper Script (Recommended)

```bash
./docker/start_ui.sh
```

Select from the interactive menu:
1. **Build and start** - First-time setup or after code changes
2. **Start existing** - Restart a stopped container
3. **Stop** - Stop the running container
4. **View logs** - Monitor container logs
5. **Rebuild from scratch** - Clean rebuild (removes volumes)
6. **Run locally** - Run without Docker (uses venv)

### Manual Docker Commands

#### Build and Start
```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

#### Stop
```bash
docker-compose -f docker/docker-compose.yml down
```

#### View Logs
```bash
docker-compose -f docker/docker-compose.yml logs -f
```

## Configuration

### Ports
- **8501** - Streamlit web interface

### Volumes
The following directories are mounted for persistence:
- `./results` - Simulation output data
- `./config` - Parameter configuration files
- `./data` - Input data files

### Environment Variables
- `PYTHONUNBUFFERED=1` - Immediate output to logs
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` - Disable telemetry

## Health Checks

The container includes automatic health monitoring:
- **Endpoint:** `http://localhost:8501/_stcore/health`
- **Interval:** Every 30 seconds
- **Timeout:** 10 seconds
- **Retries:** 3 attempts before marking unhealthy
- **Start period:** 40 seconds grace period

## Accessing the Web Interface

Once started, open your browser to:
```
http://localhost:8501
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs

# Rebuild from scratch
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml build --no-cache
docker-compose -f docker/docker-compose.yml up -d
```

### Port already in use
```bash
# Find and stop process using port 8501
lsof -ti:8501 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "8502:8501"  # Use 8502 on host instead
```

### Code changes not reflected
Remember to rebuild after modifying code:
```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

## Requirements

- Docker Engine 20.10+
- Docker Compose v2.0+
- 2GB RAM minimum
- Port 8501 available

## System Resources

### Development (Fast Testing)
- **Population:** 10K-20K agents
- **Memory:** ~2GB
- **Time:** 3-5 min/scenario

### Production (Standard Analysis)
- **Population:** 50K-100K agents
- **Memory:** ~4GB
- **Time:** 10-20 min/scenario

### High-Resolution (Research)
- **Population:** 100K-500K agents
- **Memory:** ~8GB
- **Time:** 30-120 min/scenario
