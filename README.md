# HIVEC-CM: HIV Epidemic Cameroon Model

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

HIVEC-CM is an agent-based mathematical model simulating HIV/AIDS epidemic dynamics in Cameroon (1985-2100). The model supports public health policy analysis through detailed demographic tracking, disease progression modeling, and intervention impact assessment.

**Author**: Nkemngu Blake Afutendem  
**Institution**: University of Buea, Cameroon  
**Version**: 4.0 (November 2025)

## Key Features

- Agent-based modeling with individual-level tracking
- HIV disease progression through acute, chronic, and AIDS stages
- Treatment and prevention interventions (ART, male circumcision, testing)
- Calibrated against World Bank and UNAIDS data (1990-2022)
- Regional analysis (12 Cameroon regions)
- Age-sex stratification (10 age groups × 2 sexes)
- Policy scenario analysis (9 pre-configured scenarios)
- Web-based visualization interface

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Nkemngublake/-HIVEC-CM-HIV-Epidemic-Cameroon-Model-.git
cd -HIVEC-CM-HIV-Epidemic-Cameroon-Model-

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run a Simulation

```bash
# Single scenario
./scripts/run_simulation.py --mode single --scenario S0_baseline --population 25000

# All policy scenarios
./scripts/run_simulation.py --mode scenarios --population 50000 --output results/analysis

# Monte Carlo analysis
./scripts/run_simulation.py --mode montecarlo --runs 100 --population 10000
```

### Web Interface

```bash
# Local
streamlit run ui/app.py

# Docker
docker-compose -f docker/docker-compose.yml up
# Access at http://localhost:8501
```

## Model Structure

### Core Components

```
src/hivec_cm/
├── models/          # HIV model and parameter handling
├── scenarios/       # Policy scenario definitions
├── core/            # Disease and demographic parameters
└── calibration/     # Parameter optimization
```

### Scripts

Five command-line tools for different tasks:

1. **run_simulation.py** - Execute simulations (single, scenarios, montecarlo)
2. **analyze_results.py** - Analyze outputs (comprehensive, gaps, compare)
3. **generate_plots.py** - Create visualizations (age-sex, regional, cascade)
4. **monitor.py** - Live monitoring (progress tracking, status)
5. **validation.py** - Model validation (parameters, milestones, benchmarks)

## Policy Scenarios

Nine pre-configured scenarios for analysis:

| ID | Scenario | Description |
|----|----------|-------------|
| S0 | Baseline | Status quo continuation |
| S1a | Optimistic Funding | Sustained investment |
| S1b | Pessimistic Funding | 40% budget reduction |
| S2a | Intensified Testing | Expanded testing campaigns |
| S2b | Key Populations | Focus on high-risk groups |
| S2c | 95-95-95 Achievement | UNAIDS cascade targets |
| S2d | Youth Focus | Adolescent interventions |
| S3a | PSN Aspirational | National plan targets |
| S3b | Geographic Priority | Regional focus |

## Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete user guide
- **[QUICK_START.md](QUICK_START.md)** - Fast setup and basic usage
- **docs/** - Technical documentation by topic
  - `01_calibration/` - Model calibration
  - `02_validation/` - Validation methods
  - `03_data_collection/` - Data capture
  - `04_scenarios/` - Scenario definitions
  - `05_integration/` - Data integration
  - `06_time_varying/` - Time-varying parameters
  - `09_technical/` - Technical details
  - `10_analysis/` - Analysis methods

## Citation

```bibtex
@software{nkemngu2025hiveccm,
  author = {Nkemngu Blake Afutendem},
  title = {HIVEC-CM: Agent-Based Model for HIV/AIDS Epidemic Dynamics in Cameroon},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/Nkemngublake/-HIVEC-CM-HIV-Epidemic-Cameroon-Model-}
}
```

## License

MIT License - See [LICENSE](LICENSE) file for details

## Contact

**Nkemngu Blake Afutendem**  
University of Buea, Cameroon  
GitHub: [@Nkemngublake](https://github.com/Nkemngublake)

---

**Data Sources**: World Bank Open Data, UNAIDS, Cameroon CAMPHIA Survey (2017-2018)
├── results/                      # Output directory
├── docs/                         # Documentation
├── src/main.py                   # Main execution script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## ⚡ Performance & Acceleration

- Binned mixing: Transmission uses age/risk binned partner pools (5-year bins) to avoid scanning all infected per contact. This reduces per-contact partner selection to O(1) expected time.
- Optional Numba: Poisson contact counts can be sampled with a Numba-accelerated kernel when available. Enable via model options or CLI.

### Enable Acceleration

- Python API:
  - `EnhancedHIVModel(params, use_numba=True, mixing_method='binned')`
- CLI:
  - `hivec-cm --config config/parameters.json --years 1 --mixing-method binned --use-numba`
  - Defaults: `mixing_method=binned`, `use_numba` disabled unless flag is passed.

### Benchmark Results

Ran on this machine with `years=1.0`, `dt=0.1` (10 steps). Times in seconds, first-run with JIT cost included for Numba.

```
     Pop |   Scan (no numba) |  Binned (no numba) |  Binned (numba)
-------------------------------------------------------------------
   10000 |             0.565 |              0.507 |           1.075
   25000 |             2.100 |              1.317 |           1.315
   50000 |             6.792 |              2.731 |           3.061
```

Notes:
- Binned mixing is 2–3x faster than the baseline scan at larger sizes.
- Numba includes JIT compile cost in the first run above; subsequent runs can be faster, especially for longer simulations or more steps.

### Run the Benchmark Yourself

```
python scripts/benchmark_transmission.py
```

If Numba is installed (see `requirements.txt`), the “Binned (numba)” column will report results; otherwise NaN.

## 🖥️ Local UI Options

You can run an interactive local UI to watch the simulation evolve.

- Streamlit (fastest to run locally):
  - Install deps: `pip install -r requirements.txt`
  - Run: `streamlit run ui/streamlit_app.py`
  - Features: live plots (prevalence, ART, infections, population), start/stop controls, Numba + mixing method toggles.

- Plotly Dash (optional):
  - Included: `ui/dash_app.py`
  - Run: `python ui/dash_app.py`
  - Mechanism: background thread + queue; `dcc.Interval` polls updates every 300ms.
