# HIVEC-CM: HIV Epidemic Cameroon Model

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Status: Active](https://img.shields.io/badge/Status-Active%20Development-green.svg)](https://github.com/Nkemngublake/-HIVEC-CM-HIV-Epidemic-Cameroon-Model-/issues)

## Overview

**HIVEC-CM** (HIV Epidemic Cameroon Model) is a sophisticated agent-based mathematical model for simulating HIV/AIDS epidemic dynamics in Cameroon from 1990-2100. The model incorporates evidence-based parameters, time-varying interventions, and policy scenarios to support public health decision-making and research.

## ✨ Key Features

- **Agent-Based Modeling**: Individual-level tracking with detailed demographic and health status modeling
- **Disease Progression**: Comprehensive HIV disease stages (acute, chronic, AIDS) with realistic transition rates
- **Intervention Modeling**: ART scale-up, prevention programs, male circumcision, and testing strategies
- **Advanced Calibration**: Automated parameter optimization using differential evolution and Nelder-Mead algorithms
- **Comprehensive Analysis**: Epidemiological indicators, transmission dynamics, and intervention impact assessment
- **Data Integration**: Real-world calibration using World Bank population data and UNAIDS HIV statistics
- **Professional Visualization**: Multi-panel dashboards with publication-quality figures

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd HIV_AIDS_Cameroon_Analysis
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv hiv_model_env
   source hiv_model_env/bin/activate  # On Windows: hiv_model_env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

1. **Run a simple simulation**:
   ```bash
   python run_model.py --years 20 --output results
   ```

2. **Run with calibration**:
   ```bash
   python run_model.py --calibrate --years 30 --output calibrated_results
   ```

3. **Use custom configuration**:
   ```bash
   python run_model.py --config config/custom.yaml --output custom_results
   ```

4. **Validate input data**:
   ```bash
   python run_model.py --validate-data --years 25
   ```

## 📊 Model Architecture

### Core Components

- **`src/models/hiv_model.py`**: Enhanced agent-based HIV epidemic model with individual tracking
- **`src/models/calibrator.py`**: Advanced parameter estimation and model calibration
- **`src/analysis/analyzer.py`**: Comprehensive analysis framework with visualization
- **`src/utils/`**: Data loading, configuration management, and utilities

### Key Model Features

- **Individual Agents**: Each person tracked with age, gender, HIV status, treatment history
- **Disease Progression**: Acute → Chronic → AIDS progression with realistic rates
- **Treatment Modeling**: ART initiation, adherence, failure, and efficacy
- **Demographics**: Birth, death, aging, and population dynamics
- **Interventions**: Prevention programs, testing campaigns, treatment scale-up

## 🎯 Use Cases

### Research Applications

- **Epidemic Forecasting**: Project future HIV prevalence and incidence
- **Intervention Planning**: Evaluate impact of different prevention and treatment strategies
- **Policy Analysis**: Assess cost-effectiveness of public health interventions
- **Academic Research**: Publication-ready epidemiological modeling and analysis

### Example Analyses

1. **Baseline Epidemiology**: Understand historical HIV trends in Cameroon
2. **ART Impact**: Quantify the effect of treatment scale-up on epidemic dynamics
3. **Prevention Strategies**: Model male circumcision, PrEP, and behavioral interventions
4. **Future Scenarios**: Project epidemic trajectories under different policy scenarios

## 📈 Output and Results

### Generated Files

- **`simulation_results.csv`**: Complete time-series data from the simulation
- **`analysis_dashboard.png`**: Multi-panel visualization of key indicators
- **`analysis_summary.txt`**: Text summary of epidemic indicators
- **`run_metadata.json`**: Complete run configuration and metadata

### Key Metrics

- HIV prevalence and incidence over time
- ART coverage and treatment outcomes
- Population dynamics and demographic trends
- Intervention impact assessments
- Validation metrics against real data

## ⚙️ Configuration

### Configuration File Format (YAML)

```yaml
# Simulation parameters
simulation:
  years: 35
  dt: 0.1
  output_frequency: 10

# Model parameters
model:
  initial_population: 75000
  initial_hiv_prevalence: 0.054
  transmission_rate: 0.12
  art_efficacy: 0.95

# Calibration settings
calibration:
  method: differential_evolution
  max_iterations: 100
  parameters_to_calibrate:
    - transmission_rate
    - death_rate_hiv
    - art_efficacy

# Interventions
interventions:
  art_scale_up:
    enabled: true
    start_year: 2005
    target_coverage: 0.81
```

### Command Line Options

```bash
python run_model.py [OPTIONS]

Options:
  --years YEARS                 Simulation duration (default: 35)
  --population POPULATION       Initial population size (default: 75000)
  --calibrate                   Run calibration before simulation
  --output OUTPUT              Output directory (default: results)
  --config CONFIG              Configuration file (YAML format)
  --data-file DATA_FILE        Custom data file for calibration
  --validate-data              Validate input data before running
  --log-level LEVEL            Logging level (DEBUG, INFO, WARNING, ERROR)
```

## 📋 Data Sources

- **World Bank**: Population statistics and HIV prevalence data for Cameroon
- **UNAIDS**: Treatment coverage, program effectiveness data
- **Integrated Dataset**: `data/cameroon_hiv_population_data.csv` with 1990-2022 data

## 🔬 Model Validation

The model is validated against historical data using multiple metrics:

- **Mean Absolute Error (MAE)**: Average deviation from observed prevalence
- **R-squared**: Proportion of variance explained by the model
- **Correlation**: Linear relationship between simulated and observed data
- **Trend Analysis**: Comparison of epidemic trajectories

## 🛠️ Development

### Project Structure

```
HIV_AIDS_Cameroon_Analysis/
├── src/                          # Source code
│   ├── models/                   # Core epidemiological models
│   ├── analysis/                 # Analysis and visualization
│   └── utils/                    # Utilities and helpers
├── config/                       # Configuration files
├── data/                         # Input datasets
├── tests/                        # Unit tests
├── notebooks/                    # Jupyter notebooks
├── results/                      # Output directory
├── docs/                         # Documentation
├── run_model.py                  # Main execution script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Technical Documentation

### Mathematical Model

The model implements a compartmental SEIR-like structure with the following states:
- **Susceptible**: Individuals at risk of HIV infection
- **Acute HIV**: Recently infected individuals (high viral load)
- **Chronic HIV**: Stable infection phase
- **AIDS**: Advanced HIV disease
- **On ART**: Individuals receiving antiretroviral treatment

### Calibration Methods

- **Differential Evolution**: Global optimization algorithm for parameter estimation
- **Nelder-Mead**: Local optimization for fine-tuning parameters
- **Multi-objective**: Simultaneous optimization of multiple epidemiological indicators

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions, issues, or collaborations:

- Open an issue on GitHub
- Contact the development team
- Review the documentation in the `docs/` directory

## 🙏 Acknowledgments

- **World Bank** for providing comprehensive demographic and health data
- **UNAIDS** for HIV/AIDS statistics and program data
- **Cameroon Ministry of Health** for epidemiological insights
- **Research Community** for epidemiological modeling best practices

---

*This model is designed for research and educational purposes. Results should be interpreted by qualified epidemiologists and public health professionals.*

## Project Structure
```
├── data/                       # Raw and processed datasets
│   ├── raw/                   # Original downloaded data
│   ├── processed/             # Cleaned and merged datasets
│   └── external/              # External data sources
├── scripts/                   # Analysis and processing scripts
│   ├── data_processing.py     # Data download utilities
│   ├── data_wrangling.py      # Data cleaning and merging
│   ├── time_series_analysis.py # Time series visualization
│   └── statistical_analysis.py # Statistical analysis
├── figures/                   # Generated visualizations
├── reports/                   # Analysis reports and findings
├── notebooks/                 # Jupyter notebooks for exploration
├── config/                    # Configuration files
└── tests/                     # Unit tests

```

## Data Sources
- **World Bank**: Population data and HIV prevalence rates for Cameroon
- **UNAIDS**: Additional HIV/AIDS statistics and estimates

## Key Datasets
1. `cameroon_hiv_population_data.csv` - Merged population and HIV prevalence data
2. `estimated_people_living_with_hiv.csv` - UNAIDS estimates
3. `people_on_art.csv` - Antiretroviral therapy coverage data

## Installation & Setup
```bash
# Clone repository
git clone <repository-url>
cd HIV_AIDS_Cameroon_Analysis

# Install dependencies
pip install -r requirements.txt

# Run analysis
python scripts/data_processing.py
python scripts/data_wrangling.py
python scripts/time_series_analysis.py
```

## Usage
1. **Data Download**: Run `data_processing.py` to fetch latest data
2. **Data Preparation**: Run `data_wrangling.py` to clean and merge datasets
3. **Analysis**: Run analysis scripts or use Jupyter notebooks for exploration

## Analysis Findings
[Add your key findings here]

## Contributing
[Add contribution guidelines]

## License
[Add license information]
