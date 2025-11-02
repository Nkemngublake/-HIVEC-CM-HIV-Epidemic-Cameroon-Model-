# HIVEC-CM Web Interface

Interactive web-based interface for configuring and running HIV epidemic simulations.

## Quick Start

### Option 1: Run Locally (Recommended for Development)

```bash
# Install dependencies (if not already installed)
pip install streamlit plotly

# Launch the web interface
streamlit run ui/app.py
```

The interface will open automatically in your browser at `http://localhost:8501`

### Option 2: Using Docker

```bash
# Using the start script
./start_ui.sh

# Or manually with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Option 3: Using the Helper Script

```bash
./start_ui.sh
```

Follow the interactive menu to:
1. Build and start
2. Start existing container
3. Stop container
4. View logs
5. Rebuild from scratch
6. Run locally without Docker

## Features

### 🎛️ Configure & Run
- **Scenario Selection**: Choose from 9 policy scenarios
- **Time Period**: Set simulation duration (1985-2070+)
- **Population Size**: Configure agent population (1K-1M)
- **Model Parameters**: Adjust transmission, treatment, and demographic parameters
- **Output Settings**: Define storage location and output formats

### 📊 View Results
- Real-time progress monitoring
- Interactive prevalence trajectory plots
- Comparative scenario analysis
- Download results in CSV format

### 📖 Documentation
- Model overview and technical details
- Scenario descriptions
- Usage guidelines
- References

### ⚙️ Advanced Settings
- CPU and memory configuration
- Random seed for reproducibility
- Performance optimization options
- Cache management

## Interface Sections

### Scenario Configuration
Select one or more scenarios to run:
- **S0**: Baseline (status quo)
- **S1a**: Optimistic funding (+20%)
- **S1b**: Pessimistic funding (-40% - CRISIS scenario)
- **S2a**: Intensified testing
- **S2b**: Key populations focus
- **S2c**: eTME achievement
- **S2d**: Youth & adolescent focus
- **S3a**: PSN 2024-2030 aspirational
- **S3b**: Geographic prioritization

### Parameter Controls

#### Time & Population
- Start Year (1980-2020)
- End Year (2025-2100)
- Population Size (1,000-1,000,000 agents)
- Time Step (0.05-1.0 years)

#### Transmission Parameters
- Base transmission rate
- Initial HIV prevalence
- Mean contacts per year
- Time-varying multipliers (emergence, growth, decline)

#### Treatment Parameters
- ART viral suppression efficacy
- ART mortality reduction
- Treatment cascade dynamics

### Output Configuration
- Custom directory naming
- Detailed results option
- Automatic plot generation
- Result compression

## Usage Example

1. **Launch the interface**:
   ```bash
   streamlit run ui/app.py
   ```

2. **Configure your simulation**:
   - Go to "Configure & Run" tab
   - Select scenarios (e.g., Baseline + Pessimistic Funding)
   - Set time period: 1985-2070 (85 years)
   - Set population: 100,000 agents
   
3. **Adjust parameters** (optional):
   - Fine-tune transmission rates
   - Modify treatment efficacy
   - Adjust demographic parameters

4. **Set output location**:
   - Name your simulation run
   - Choose base results path
   - Enable detailed results

5. **Run simulation**:
   - Click "START SIMULATION"
   - Monitor progress in real-time
   - View live updates

6. **Analyze results**:
   - Switch to "View Results" tab
   - Select your simulation run
   - Explore prevalence trajectories
   - Download data for further analysis

## Performance Tips

### For Fast Testing
- Population: 10,000-20,000 agents
- Time period: 1985-2030 (45 years)
- Time step: 0.1 years
- **Estimated time**: 3-5 minutes per scenario

### For Production Analysis
- Population: 50,000-100,000 agents
- Time period: 1985-2070 (85 years)
- Time step: 0.1 years
- **Estimated time**: 10-20 minutes per scenario

### For High-Resolution Studies
- Population: 100,000-500,000 agents
- Time period: 1985-2070 (85 years)
- Time step: 0.05 years
- **Estimated time**: 30-120 minutes per scenario

## Technical Details

### System Requirements
- **Python**: 3.9 or higher
- **RAM**: 4GB minimum, 8-16GB recommended
- **CPU**: Multi-core processor recommended
- **Storage**: 1GB free space per simulation run

### Dependencies
- streamlit >= 1.30.0
- plotly >= 5.0.0
- pandas >= 1.5.0
- numpy >= 1.23.0
- All HIVEC-CM model dependencies

### Port Configuration
Default port: 8501

To use a different port:
```bash
streamlit run ui/app.py --server.port 8502
```

### Docker Configuration
The Docker setup includes:
- Automatic health checks
- Volume mounting for persistent results
- Port mapping (8501:8501)
- Auto-restart on failure

## Troubleshooting

### Issue: Interface won't start
**Solution**: Check if port 8501 is already in use
```bash
lsof -i :8501
```

### Issue: Simulation not progressing
**Solution**: Check terminal output for errors, ensure sufficient memory

### Issue: Results not appearing
**Solution**: Verify output directory permissions, check disk space

### Issue: Docker container fails to start
**Solution**: Check Docker logs
```bash
docker-compose logs
```

## Data Management

### Results Directory Structure
```
results/
└── simulation_YYYYMMDD_HHMMSS/
    ├── execution_summary.json
    ├── S0_baseline/
    │   ├── simulation_results.csv
    │   └── metadata.json
    ├── S1a_optimistic_funding/
    │   ├── simulation_results.csv
    │   └── metadata.json
    └── ...
```

### Cleanup Old Results
Results can accumulate quickly. To manage storage:

```bash
# Remove results older than 30 days
find results/ -type d -mtime +30 -exec rm -rf {} +

# Or use the UI's "Clean Old Results" button in Advanced Settings
```

## Security Notes

- The interface runs locally by default
- No external network access required
- All data stays on your machine
- Docker containers are isolated

## Updates and Maintenance

### Update the model
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Clear cache
Use the "Clear Cache" button in Advanced Settings, or:
```bash
rm -rf ~/.streamlit/cache/
```

## Support

For issues or questions:
1. Check the Documentation tab in the UI
2. Review model documentation in `docs/`
3. Check terminal output for error messages
4. Verify parameter ranges are valid

## Version Information

- **Interface Version**: 1.0.0
- **Model Version**: 7.0 (Time-Varying Calibrated)
- **Last Updated**: November 2025
