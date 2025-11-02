# Live Simulation Monitoring - Implementation Guide

## Overview

Added real-time monitoring capability to the HIVEC-CM web interface to display live agent statistics and evolution during simulation runs.

## New Features

### 1. **Live Agent Statistics Display**
- 👥 Agents Alive (total population)
- 🦠 HIV+ Agents (with prevalence %)  
- 💊 Agents on ART (with coverage %)
- 🔴 New Infections (per year)

### 2. **Real-Time Progress Tracking**
- Overall simulation progress (all scenarios)
- Current scenario progress (per-year)
- Current simulation year display
- Scenario counter (#X/Total)

### 3. **Live Prevalence Evolution Plot**
- Interactive Plotly chart
- Shows HIV prevalence over time
- Updates in real-time as simulation progresses
- Color-coded by scenario

### 4. **Auto-Refresh**
- UI refreshes every 2 seconds during simulation
- No manual page reload needed
- Smooth progress updates

## Files Modified

### `/ui/app.py`
**Changes:**
- Added `import time` for auto-refresh
- Enhanced `configure_and_run_page()` function
- Replaced basic progress bar with comprehensive live monitor
- Added live statistics metrics display
- Added live prevalence plot from streaming data
- Implemented auto-refresh mechanism

**Key Code Sections:**
```python
# Live monitoring section (lines 476-596)
- Reads `.progress.json` for current state
- Displays 4-metric dashboard
- Loads `.live_data.json` for historical plot
- Auto-refreshes every 2 seconds
```

### `/src/utils/simulation_monitor.py` (NEW FILE)
**Purpose:** Backend monitoring utilities

**Key Classes:**
- `SimulationMonitor`: Tracks and logs simulation progress

**Key Methods:**
- `update_progress()`: Write current simulation state
- `read_progress()`: Read latest progress data
- `read_live_data()`: Get historical data for plots
- `mark_scenario_complete()`: Flag scenario completion
- `mark_all_complete()`: Flag full run completion

**Data Files Created:**
- `.progress.json`: Current state (overwritten each update)
- `.live_data.json`: Append-only log of all updates

## Usage

### 1. Start Simulation via Web UI
```bash
# Start Docker container
./docker/start_ui.sh

# Open browser to http://localhost:8501
# Configure parameters and click "START SIMULATION"
```

### 2. Watch Live Updates
The UI will automatically display:
- Real-time agent counts
- HIV prevalence percentage
- ART coverage statistics
- Live evolution plot

### 3. Data Files Location
```
results/{output_dir}/
├── .progress.json       # Current state (temp file)
├── .live_data.json      # Historical log (kept)
└── {scenario_id}/
    ├── simulation_results.csv
    └── metadata.json
```

## Progress Data Format

### `.progress.json`