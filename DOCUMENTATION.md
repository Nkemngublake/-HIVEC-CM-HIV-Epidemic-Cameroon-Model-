# HIVEC-CM: HIV Epidemic Cameroon Model
## Comprehensive Documentation

**Version**: 4.0  
**Author**: Nkemngu Blake Afutendem  
**Last Updated**: November 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Model Architecture](#model-architecture)
4. [Running Simulations](#running-simulations)
5. [Analysis & Visualization](#analysis--visualization)
6. [Docker Deployment](#docker-deployment)
7. [Configuration](#configuration)
8. [Project Structure](#project-structure)
9. [Troubleshooting](#troubleshooting)

---

## Overview

HIVEC-CM is an agent-based mathematical model simulating HIV/AIDS epidemic dynamics in Cameroon from 1985-2100. The model supports evidence-based policy analysis through detailed demographic tracking, disease progression modeling, and intervention impact assessment.

### Core Capabilities

- Individual-level agent tracking with demographic and clinical attributes
- HIV disease progression through acute, chronic, and AIDS stages
- Treatment modeling (ART initiation, adherence, viral suppression)
- Policy scenarios (9 pre-configured scenarios including UNAIDS 95-95-95 targets)
- Regional analysis (12 Cameroon regions)
- Age-sex stratification (10 age groups × 2 sexes)
- Monte Carlo uncertainty analysis

### Key Outputs

- Prevalence and incidence trajectories
- Treatment cascade metrics (diagnosed, on ART, virally suppressed)
- Age-sex stratified epidemic indicators
- Regional variation analysis
- Intervention impact assessments

---

## Installation & Setup

### Requirements

- Python 3.9 or higher
- 8GB RAM minimum (16GB recommended for large simulations)
- Docker (optional, for web interface deployment)

### Local Setup

```bash
# Clone repository
git clone https://github.com/Nkemngublake/-HIVEC-CM-HIV-Epidemic-Cameroon-Model-.git
cd -HIVEC-CM-HIV-Epidemic-Cameroon-Model-

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import hivec_cm; print('Installation successful')"
```

### Docker Setup

```bash
# Build and start container
docker-compose -f docker/docker-compose.yml up

# Access web interface at http://localhost:8501
```

---

## Model Architecture

### Agent-Based Framework

Each agent represents an individual with attributes:
- Demographics: age, sex, region
- HIV status: susceptible, infected (acute/chronic/AIDS), on ART
- Clinical: CD4 count, viral load, treatment history
- Risk factors: sexual behavior, co-infections

### Disease Progression

```
Susceptible → Acute (3-6 months) → Chronic (8-10 years) → AIDS (2-3 years) → Death
                                            ↓
                                    ART Treatment → Viral Suppression
```

### Intervention Modeling

**Treatment (ART)**
- Initiation rates based on diagnosis and eligibility
- Adherence levels affecting viral suppression
- Treatment failure and switching protocols

**Prevention**
- Male circumcision (60% HIV acquisition reduction)
- Behavioral interventions
- Testing campaigns

**Policy Scenarios**
1. S0: Baseline (status quo)
2. S1a: Optimistic funding (sustained investment)
3. S1b: Pessimistic funding (40% budget cut)
4. S2a: Intensified testing
5. S2b: Key populations focus
6. S2c: 95-95-95 cascade achievement
7. S2d: Youth and adolescent focus
8. S3a: PSN 2024-2030 aspirational targets
9. S3b: Geographic prioritization

### Calibration

Model parameters are calibrated against:
- World Bank population data (1990-2022)
- UNAIDS HIV prevalence estimates (1990-2022)
- CAMPHIA survey data (2017-2018)

Calibration uses differential evolution optimization to minimize mean absolute error (MAE) between model outputs and historical data.

---

## Running Simulations

### Command-Line Tools

The model provides 5 unified scripts for different tasks:

#### 1. run_simulation.py - Execute Simulations

```bash
# Single scenario (baseline)
./scripts/run_simulation.py --mode single \
    --scenario S0_baseline \
    --population 25000 \
    --config config/parameters.json \
    --output results/baseline

# All 9 policy scenarios
./scripts/run_simulation.py --mode scenarios \
    --population 50000 \
    --output results/policy_analysis

# Monte Carlo uncertainty analysis (100 runs)
./scripts/run_simulation.py --mode montecarlo \
    --runs 100 \
    --population 10000 \
    --uncertainty 0.15 \
    --output results/montecarlo
```

**Parameters:**
- `--mode`: Execution mode (single, scenarios, montecarlo)
- `--scenario`: Scenario ID (S0_baseline through S3b_geographic)
- `--population`: Number of agents (10,000-100,000)
- `--config`: Configuration file path
- `--output`: Output directory
- `--runs`: Number of Monte Carlo runs
- `--uncertainty`: Parameter uncertainty (±15% default)

#### 2. analyze_results.py - Analyze Outputs

```bash
# Comprehensive analysis of all data dimensions
./scripts/analyze_results.py --mode comprehensive \
    --dir results/baseline

# Detection gap analysis (testing and treatment gaps)
./scripts/analyze_results.py --mode gaps \
    --dir results/baseline

# Compare multiple scenarios
./scripts/analyze_results.py --mode compare \
    --dir results/policy_analysis

# Regenerate CSV from JSON
./scripts/analyze_results.py --mode regenerate \
    --dir results/baseline
```

**Outputs:**
- 28 data dimensions analyzed
- Age-sex stratified prevalence tables
- Regional analysis (12 regions)
- Treatment cascade metrics
- Scenario comparison tables (CSV)

#### 3. generate_plots.py - Create Visualizations

```bash
# Age-sex stratified trends
./scripts/generate_plots.py --mode age-sex \
    --dir results/baseline \
    --output plots

# Regional heatmaps
./scripts/generate_plots.py --mode regional \
    --dir results/baseline \
    --output plots

# Treatment cascade progression
./scripts/generate_plots.py --mode cascade \
    --dir results/baseline \
    --output plots

# Multi-scenario comparison
./scripts/generate_plots.py --mode compare \
    --dir results/policy_analysis \
    --output plots

# Generate all visualizations
./scripts/generate_plots.py --mode all \
    --dir results/baseline \
    --output plots
```

**Visualization Types:**
- 4-panel age-sex trends
- Regional heatmaps (12 regions)
- Treatment cascade time series
- Multi-scenario overlays
- Publication-ready PNG (300 DPI)

#### 4. monitor.py - Live Monitoring

```bash
# Monitor single simulation (5-second refresh)
./scripts/monitor.py --mode live \
    --dir results/baseline \
    --interval 5

# Monitor multiple scenarios (10-second refresh)
./scripts/monitor.py --mode scenarios \
    --dir results/policy_analysis \
    --interval 10

# Quick status check (one-time)
./scripts/monitor.py --mode status \
    --dir results/baseline
```

#### 5. validation.py - Model Validation

```bash
# Validate parameters
./scripts/validation.py --mode validate \
    --config config/parameters.json

# Compute epidemic milestones
./scripts/validation.py --mode milestones \
    --dir results/baseline

# Benchmark performance
./scripts/validation.py --mode benchmark \
    --config config/parameters.json \
    --population 25000

# Validate against historical data
./scripts/validation.py --mode comprehensive \
    --dir results/baseline \
    --validation data/validation_targets/prevalence_unaids.csv
```

### Typical Workflow

```bash
# 1. Validate configuration
./scripts/validation.py --mode validate --config config/parameters.json

# 2. Run all scenarios
./scripts/run_simulation.py --mode scenarios --population 50000 \
    --output results/analysis_2025

# 3. Monitor progress (separate terminal)
./scripts/monitor.py --mode scenarios --dir results/analysis_2025

# 4. After completion, compare results
./scripts/analyze_results.py --mode compare --dir results/analysis_2025

# 5. Generate visualizations
./scripts/generate_plots.py --mode compare \
    --dir results/analysis_2025 --output plots/comparison

# 6. Compute milestones
./scripts/validation.py --mode milestones --dir results/analysis_2025/S0_baseline
```

---

## Analysis & Visualization

### Web Interface

Start the Streamlit web interface:

```bash
# Local
streamlit run ui/app.py

# Docker
docker-compose -f docker/docker-compose.yml up
# Access at http://localhost:8501
```

**Interface Features:**

**View Results Page (4 tabs):**
1. Overview: Aggregate metrics, prevalence trajectory, treatment cascade
2. Age-Sex Analysis: Stratified prevalence (10 age groups × 2 sexes), trends
3. Regional Analysis: 12 regions, heatmaps, regional comparisons
4. Data Downloads: CSV, JSON, metadata with structure preview

**Compare Scenarios Page (3 tabs):**
1. Overview: Final outcomes table, bar charts, time series overlays
2. Age-Sex: Multi-scenario age group comparison by sex
3. Regional: Heatmap matrix (regions × scenarios), regional drill-down

### Data Outputs

Each simulation produces:

**JSON (detailed_results.json)**
```json
{
  "1985": {
    "aggregate": {"population": 25000, "infected": 150, "prevalence": 0.006},
    "age_sex_prevalence": {"15-19": {"M": {...}, "F": {...}}},
    "regional_prevalence": {"Centre": {...}, "Littoral": {...}},
    "treatment_cascade_95_95_95": {"diagnosed_coverage": 0.85, ...},
    "incidence_by_age_sex": {...},
    "mortality_by_age_sex": {...}
  }
}
```

**CSV (detailed_age_sex_results.csv)**
Flattened format with columns:
- year, type, age_group, sex, region, population, infected, prevalence_pct

**Metadata (run_metadata.json)**
Execution details: scenario, timestamp, model version, data dimensions

---

## Docker Deployment

### Building the Image

```bash
# Build with cache
docker-compose -f docker/docker-compose.yml build

# Build without cache (clean build)
docker-compose -f docker/docker-compose.yml build --no-cache
```

### Running the Container

```bash
# Start in foreground
docker-compose -f docker/docker-compose.yml up

# Start in background
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop container
docker-compose -f docker/docker-compose.yml down
```

### Container Structure

```
/app/
├── src/hivec_cm/          # Source code
├── scripts/               # 5 consolidated scripts
├── ui/                    # Streamlit interface
├── config/                # Parameters
├── data/                  # Validation targets
└── requirements.txt
```

### Port Configuration

- Web interface: `8501`
- Health check: `8501/_stcore/health`

---

## Configuration

### Parameter Files

**config/parameters.json** - Main configuration
```json
{
  "start_year": 1985,
  "end_year": 2070,
  "initial_population": 25000,
  "initial_prevalence": 0.001,
  "base_transmission_rate": 0.015,
  "art_efficacy": 0.96,
  "male_circumcision_coverage": 0.20,
  "male_circumcision_efficacy": 0.60
}
```

**config/parameters_v4_calibrated.json** - Calibrated parameters
Optimized against historical data (1990-2022)

### Scenario Definitions

Scenarios are defined in `src/hivec_cm/scenarios/scenario_definitions.py`:

```python
class S2c_95_95_95_Achievement(BaseScenario):
    scenario_id = "S2c_etme"
    name = "95-95-95 Cascade Achievement"
    description = "Achieving UNAIDS 95-95-95 targets by 2030"
    
    funding_multiplier = 1.5
    general_testing_rate = 0.95
    art_initiation_rate = 0.95
    viral_suppression_rate = 0.95
```

### Regional Configuration

12 Cameroon regions modeled:
- Centre, Littoral, Ouest, Sud-Ouest, Nord-Ouest
- Nord, Extreme-Nord, Adamaoua, Est, Sud

Each region has:
- Population distribution
- HIV prevalence levels
- ART coverage rates
- Geographic risk factors

---

## Project Structure

```
HIVEC-CM/
├── config/                          # Configuration files
│   ├── parameters.json              # Main parameters
│   └── parameters_v4_calibrated.json
│
├── data/                            # Data files
│   ├── validation_targets/          # Historical data for calibration
│   └── un_data/                     # UN population data
│
├── docker/                          # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── start_ui.sh
│
├── scripts/                         # Execution scripts (5 total)
│   ├── run_simulation.py           # Run simulations
│   ├── analyze_results.py          # Analyze outputs
│   ├── generate_plots.py           # Create visualizations
│   ├── monitor.py                  # Live monitoring
│   └── validation.py               # Validation & testing
│
├── src/                             # Source code
│   ├── hivec_cm/
│   │   ├── models/                  # Core model classes
│   │   │   ├── model.py            # Main HIV model
│   │   │   └── parameters.py       # Parameter handling
│   │   ├── scenarios/               # Scenario definitions
│   │   ├── core/                    # Core parameters
│   │   └── calibration/             # Calibration tools
│   └── utils/                       # Utilities
│
├── ui/                              # Web interface
│   ├── app.py                       # Streamlit app
│   └── dash_app.py
│
├── tests/                           # Unit tests
│
├── results/                         # Simulation outputs (not in git)
│
├── DOCUMENTATION.md                 # This file
├── README.md                        # Project README
└── requirements.txt                 # Python dependencies
```

---

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Memory Issues**
```bash
# Reduce population size
./scripts/run_simulation.py --mode single --population 10000

# Or use fewer Monte Carlo runs
./scripts/run_simulation.py --mode montecarlo --runs 50
```

**Docker Port Conflicts**
```bash
# Change port in docker-compose.yml
ports:
  - "8502:8501"  # Use 8502 instead of 8501
```

**Slow Simulations**
- Reduce population size (10,000-25,000 for testing)
- Shorten simulation period (20-30 years for testing)
- Use fewer Monte Carlo runs (10-50 for testing)

### Performance Benchmarks

| Population | Years | Time (Single Core) |
|------------|-------|-------------------|
| 10,000     | 85    | ~5 minutes        |
| 25,000     | 85    | ~12 minutes       |
| 50,000     | 85    | ~25 minutes       |
| 100,000    | 85    | ~50 minutes       |

### Getting Help

- Check script help: `./scripts/run_simulation.py --help`
- Review error logs in terminal output
- Validate parameters: `./scripts/validation.py --mode validate`
- Test with small population first

---

## Citation

If you use this model in your research, please cite:

```
Nkemngu Blake Afutendem (2025). HIVEC-CM: Agent-Based Model for HIV/AIDS 
Epidemic Dynamics in Cameroon. GitHub repository: 
https://github.com/Nkemngublake/-HIVEC-CM-HIV-Epidemic-Cameroon-Model-
```

---

## License

MIT License - See LICENSE file for details

---

**Last Updated**: November 2025  
**Model Version**: 4.0  
**Documentation Version**: 1.0
