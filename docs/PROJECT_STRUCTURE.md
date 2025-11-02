# HIVEC-CM Project Structure

Reorganized project structure for better maintainability and clarity.

## Root Directory

```
HIVEC-CM/
├── README.md                           # Main project documentation
├── LICENSE                             # Project license
├── Makefile                            # Build automation
├── pyproject.toml                      # Python project configuration
├── requirements.txt                    # Python dependencies
├── analysis_publication_ready.ipynb    # Main analysis notebook
├── generate_simulation_plots.py        # Plotting utilities
├── *.log                              # Execution logs
└── test_*.py                          # Test scripts
```

## Core Directories

### `/src/` - Source Code
Core model implementation and scenarios:
```
src/
├── hivec_cm/
│   ├── models/          # Agent-based model implementation
│   ├── scenarios/       # Policy scenario definitions
│   ├── agents/          # Agent classes and behavior
│   ├── parameters/      # Parameter management
│   └── utils/           # Utility functions
```

### `/config/` - Configuration
Parameter files and run configurations:
```
config/
├── parameters.json                    # Current parameters
├── parameters_v4_calibrated.json     # Calibrated v4 parameters
├── parameters_calibrated.json        # Latest calibration
├── parameters_test_decline_*.json    # Testing scenarios
└── run_config_*.json                 # Execution configs
```

### `/docker/` - Docker Deployment
All Docker-related files:
```
docker/
├── README.md              # Docker documentation
├── Dockerfile             # Image definition
├── docker-compose.yml     # Orchestration config
└── start_ui.sh           # Helper script
```

### `/docs/` - Documentation
Organized by topic:
```
docs/
├── README.md                          # Documentation index
├── 01_calibration/                    # Calibration & parameters
│   ├── CALIBRATION_MERGE_PROMPT.md
│   ├── PARAMETER_ARCHITECTURE.md
│   ├── PARAMETER_INTEGRATION_SUMMARY.md
│   ├── PARAMETER_MERGE_EXECUTIVE_SUMMARY.md
│   └── PARAMETER_MERGE_QUICKREF.md
├── 02_validation/                     # Model validation
│   └── MODEL_VALIDATION_README.md
├── 03_data_collection/                # Data collection enhancements
│   ├── ADDITIONAL_DATA_CAPTURE_ANALYSIS.md
│   ├── ENHANCED_DATA_COLLECTION_QUICK_REFERENCE.md
│   ├── REGIONAL_DATA_COLLECTION_COMPLETE.md
│   ├── PHASE1_ENHANCED_DATA_COLLECTION_COMPLETE.md
│   └── PHASE2_TESTING_COINFECTIONS_COMPLETE.md
├── 04_scenarios/                      # Scenario documentation
│   ├── SCENARIO_IMPLEMENTATION_COMPLETE.md
│   ├── SCENARIO_PARAMETER_VALIDATION_SUMMARY.md
│   ├── SCENARIO_QUICK_REFERENCE.md
│   ├── SCENARIO_RESULTS_ANALYSIS.md
│   ├── PSN_SCENARIO_PROGRESS.md
│   └── MULTI_SCENARIO_EXECUTION_PLAN.md
├── 05_integration/                    # CAMPHIA & demographic data
│   ├── CAMPHIA_INTEGRATION_COMPLETE.md
│   ├── CAMPHIA_INTEGRATION_SUMMARY.md
│   ├── CAMPHIA_INTEGRATION_QUICK_REFERENCE.md
│   ├── DEMOGRAPHIC_ENHANCEMENT_COMPLETE.md
│   └── DEMOGRAPHIC_IMPLEMENTATION_COMPLETE.md
├── 06_time_varying/                   # Time-varying parameters
├── 07_quick_references/               # Quick reference guides
│   ├── PHASE1_QUICK_REFERENCE.md
│   ├── PHASE2_QUICK_REFERENCE.md
│   └── QUICK_REFERENCE_COMPLETED_RUN.md
├── 08_session_summaries/              # Session summaries
│   ├── PHASES_123_COMPLETE_SUMMARY.md
│   ├── ENHANCEMENT_SUMMARY.md
│   ├── IMPLEMENTATION_STATUS.md
│   └── SIMULATION_EXECUTION_COMPLETE.md
├── 09_technical/                      # Technical documentation
│   ├── AGENT_ATTRIBUTES_MATHEMATICS.md
│   └── GITIGNORE_UPDATE_SUMMARY.md
└── 10_analysis/                       # Analysis guides
    ├── ANALYSIS_NOTEBOOK_GUIDE.md
    └── MONTECARLO_RESULTS_SUMMARY.md
```

### `/scripts/` - Execution Scripts
Simulation execution and utilities:
```
scripts/
├── run_all_scenarios.py               # Main scenario executor
├── run_all_scenarios.sh               # Shell wrapper
├── run_remaining_scenarios.sh         # Resume execution
└── plot_results.py                    # Result visualization
```

### `/ui/` - Web Interface
Streamlit web application:
```
ui/
├── app.py                 # Main Streamlit application
└── README.md              # UI documentation
```

### `/tests/` - Test Suite
Unit and integration tests:
```
tests/
├── unit/                  # Unit tests
├── integration/           # Integration tests
└── fixtures/              # Test fixtures
```

### `/data/` - Input Data
External data sources:
```
data/
├── un_data/              # UN demographic data
└── validation_targets/   # UNAIDS validation targets
```

### `/results/` - Simulation Output
Generated simulation results:
```
results/
├── Test_Run_1000_agents/              # Test run (1K agents)
│   ├── S0_baseline/
│   ├── S1a_optimistic_funding/
│   ├── S1b_pessimistic_funding/
│   └── ...
└── Final_Analysis_1985_2100/          # Production runs
    └── ...
```

### `/validation/` & `/validation_outputs/`
Model validation data and results

## Key Files by Purpose

### Running Simulations
- `scripts/run_all_scenarios.py` - Main execution script
- `docker/start_ui.sh` - Web interface launcher
- `config/parameters.json` - Current parameters

### Configuration
- `pyproject.toml` - Python project settings
- `requirements.txt` - Dependencies
- `.flake8` - Code style configuration
- `.gitignore` - Git exclusions

### Documentation Entry Points
- `README.md` - Project overview
- `docs/README.md` - Documentation index
- `docker/README.md` - Docker guide
- `ui/README.md` - Web interface guide

### Analysis
- `analysis_publication_ready.ipynb` - Main analysis notebook
- `generate_simulation_plots.py` - Plotting utilities
- `docs/10_analysis/` - Analysis documentation

## Quick Navigation

| Task | Location |
|------|----------|
| Run simulations | `scripts/run_all_scenarios.py` |
| Configure parameters | `config/parameters.json` |
| View results | `ui/app.py` or notebooks |
| Read documentation | `docs/README.md` |
| Deploy with Docker | `docker/start_ui.sh` |
| Run tests | `tests/` |
| Analyze results | `analysis_publication_ready.ipynb` |

## File Naming Conventions

- **UPPERCASE.md** - Documentation files (now organized in `docs/`)
- **lowercase.py** - Python source files
- **lowercase.sh** - Shell scripts
- **lowercase.json** - Configuration files
- **lowercase.ipynb** - Jupyter notebooks
- **lowercase.log** - Log files

## Recent Reorganization (Nov 2025)

### Changes Made:
1. ✅ Created `/docker/` folder for all Docker files
2. ✅ Moved 30+ MD files into organized `/docs/` subdirectories
3. ✅ Added README files for docker/ and updated documentation

### Benefits:
- Cleaner root directory
- Logical grouping of related documents
- Easier navigation and maintenance
- Better separation of concerns
- Improved Docker workflow
