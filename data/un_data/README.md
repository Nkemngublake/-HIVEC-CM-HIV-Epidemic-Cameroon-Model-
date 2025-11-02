# UN Population Data Portal Integration

This directory contains infrastructure for fetching and processing validation data from the UN Population Data Portal API.

## Overview

The UN Population Data Portal provides authoritative demographic and HIV indicator data for Cameroon that serves as validation targets for the HIVEC-CM model. This integration enables:

1. **Automated data extraction** from UN API
2. **Structured validation targets** for model calibration and validation
3. **Comprehensive validation metrics** against empirical data
4. **Publication-ready validation reports** and figures

## Directory Structure

```
data/un_data/
├── un_api_config.json          # API configuration and indicator codes
├── fetch_un_data.py            # Data extraction script
├── raw/                        # Raw data from UN API (auto-generated)
│   ├── population_total.csv
│   ├── population_age_sex_long.csv
│   ├── population_age_sex_wide.csv
│   ├── hiv_prevalence_15_49.csv
│   ├── new_hiv_infections.csv
│   └── ...
└── README.md                   # This file

data/validation_targets/
└── un_validation_targets.json  # Structured targets (auto-generated)

validation/
└── validate_model.py           # Model validation script
```

## Quick Start

### 1. Fetch UN Data

```bash
cd data/un_data

# Fetch all indicators (demographic + HIV)
python fetch_un_data.py --indicator all --start 1990 --end 2023

# Fetch only demographic indicators
python fetch_un_data.py --indicator demographic

# Fetch only HIV indicators
python fetch_un_data.py --indicator hiv

# Fetch specific indicator
python fetch_un_data.py --indicator hiv_prevalence_15_49 --start 2000 --end 2023
```

### 2. Create Validation Targets

```bash
# Create structured validation targets from raw data
python fetch_un_data.py --indicator all --create-targets
```

This generates `data/validation_targets/un_validation_targets.json` with:
- Calibration targets (1990-2015)
- Validation targets (2016-2023)
- Acceptance criteria
- Metadata

### 3. Validate Model

```bash
cd ../../validation

# Validate baseline scenario
python validate_model.py --scenario S0_baseline --period calibration

# Validate all scenarios
python validate_model.py --all-scenarios --period both

# Validate specific scenario for out-of-sample validation
python validate_model.py --scenario S1a_optimistic_funding --period validation
```

## API Configuration

The `un_api_config.json` file contains:

### Authentication
- **Bearer Token**: Valid until 2056-04-15
- **Endpoint**: `https://population.un.org/dataportalapi/api/v1`

### Location
- **Country**: Cameroon
- **Location Code**: 120

### Indicators

#### Demographic Indicators
| Indicator | Code | Description |
|-----------|------|-------------|
| Total Population | 47 | De facto population (thousands) |
| Population by Age/Sex | 60 | 5-year age groups by sex |
| Births | 155 | Live births during year |
| Deaths | 156 | Deaths during year |
| Death Rate (Age-specific) | 194 | Deaths per 1,000 by age group |
| Total Fertility Rate | 68 | Children per woman |
| Life Expectancy | 67 | Years at birth |

#### HIV Indicators
| Indicator | Code | Description |
|-----------|------|-------------|
| HIV Prevalence (15-49) | 102 | % of population aged 15-49 with HIV |
| HIV Deaths | 105 | Deaths due to HIV/AIDS (thousands) |
| New HIV Infections | 103 | New infections (thousands) |
| PMTCT Coverage | 106 | % of HIV+ pregnant women on ART |

### Time Periods
- **Calibration**: 1990-2015 (fit model parameters)
- **Validation**: 2016-2023 (out-of-sample testing)

### Acceptance Criteria
- **R² ≥ 0.85**: Coefficient of determination
- **Relative Error ≤ 15%**: Maximum acceptable error
- **NSE ≥ 0.70**: Nash-Sutcliffe efficiency
- **Coverage ≥ 90%**: Prediction interval coverage

## Data Extraction Details

### fetch_un_data.py

**Purpose**: Fetch data from UN API and save to CSV files

**Key Features**:
- Rate limiting (0.5s between requests)
- Error handling for API failures
- Both long and wide format exports
- Automatic directory creation
- Detailed logging

**Class**: `UNDataFetcher`

**Methods**:
- `fetch_indicator()`: Fetch single indicator
- `fetch_demographic_indicators()`: Fetch all demographic data
- `fetch_hiv_indicators()`: Fetch all HIV data
- `fetch_age_sex_population()`: Fetch age-sex stratified population
- `create_validation_targets()`: Convert raw data to validation targets

**Output Format** (raw CSV):
```csv
timeLabel,locationCode,locationName,value,sex,ageLabel
2010,120,Cameroon,19599.456,Both,Total
2011,120,Cameroon,20047.890,Both,Total
...
```

**Output Format** (validation targets JSON):
```json
{
  "metadata": {
    "source": "UN Population Data Portal",
    "location": "Cameroon",
    "calibration_period": "1990-2015",
    "validation_period": "2016-2023"
  },
  "calibration_targets": {
    "hiv_prevalence_15_49": {
      "1990": 0.5,
      "1991": 0.8,
      ...
    }
  },
  "validation_targets": { ... },
  "acceptance_criteria": { ... }
}
```

## Model Validation

### validate_model.py

**Purpose**: Comprehensive validation of model outputs against UN targets

**Key Features**:
- Multiple validation metrics (MAE, RMSE, MAPE, R², NSE, bias)
- Acceptance criteria checking
- Time series comparison plots
- Scatter plots with 1:1 lines
- Markdown validation reports
- Support for calibration and out-of-sample validation

**Class**: `ModelValidator`

**Validation Metrics**:

1. **MAE** (Mean Absolute Error): Average absolute difference
   ```
   MAE = (1/n) Σ|Observed - Predicted|
   ```

2. **RMSE** (Root Mean Squared Error): Root of average squared difference
   ```
   RMSE = √[(1/n) Σ(Observed - Predicted)²]
   ```

3. **MAPE** (Mean Absolute Percentage Error): Average percentage error
   ```
   MAPE = (100/n) Σ|((Observed - Predicted) / Observed)|
   ```

4. **R²** (Coefficient of Determination): Proportion of variance explained
   ```
   R² = 1 - [Σ(O-P)²] / [Σ(O-Ō)²]
   ```

5. **NSE** (Nash-Sutcliffe Efficiency): Predictive skill relative to mean
   ```
   NSE = 1 - [Σ(O-P)²] / [Σ(O-Ō)²]
   ```
   - NSE = 1: Perfect match
   - NSE = 0: Model = mean of observations
   - NSE < 0: Model worse than mean

6. **Bias**: Mean difference (systematic over/under-prediction)
   ```
   Bias = Mean(Predicted - Observed)
   ```

7. **Coverage**: Proportion of observations within 90% prediction intervals

**Output**: 
- Markdown report with metrics table and plots
- PNG figures for each indicator
- Pass/fail status against acceptance criteria

**Example Report Section**:
```markdown
### hiv_prevalence_15_49 ✅ PASS

**Data Points:** 26

| Metric | Value | Pass? |
|--------|-------|-------|
| MAE | 0.0245 | - |
| RMSE | 0.0312 | - |
| MAPE | 4.23% | - |
| R² | 0.9123 | ✅ |
| NSE | 0.8934 | ✅ |
| Bias | -0.0012 | - |
| Relative Bias | -2.1% | ✅ |

![hiv_prevalence_15_49](hiv_prevalence_15_49_S0_baseline_calibration.png)
```

## Workflow

### Standard Validation Workflow

```bash
# 1. Fetch UN data
cd data/un_data
python fetch_un_data.py --indicator all --start 1990 --end 2023 --create-targets

# 2. Run model simulations (if not already done)
cd ../../
python -m src.main --scenario S0_baseline --start-year 1990 --end-year 2023

# 3. Validate model outputs
cd validation
python validate_model.py --scenario S0_baseline --period both

# 4. Review validation report
open validation_outputs/validation_report_S0_baseline_calibration.md
open validation_outputs/validation_report_S0_baseline_validation.md
```

### Calibration Workflow

```bash
# 1. Initial validation
python validate_model.py --scenario S0_baseline --period calibration

# 2. Identify poorly fitting indicators (check report)

# 3. Adjust model parameters in config/parameters.json
#    Focus on parameters affecting poorly fitting indicators

# 4. Re-run simulation with adjusted parameters
cd ..
python -m src.main --scenario S0_baseline --start-year 1990 --end-year 2023

# 5. Re-validate
cd validation
python validate_model.py --scenario S0_baseline --period calibration

# 6. Repeat until acceptance criteria met

# 7. Final out-of-sample validation
python validate_model.py --scenario S0_baseline --period validation
```

## Integration with Model

### Required Model Outputs

For validation to work, model must output CSV files with:

**Minimum Required Columns**:
- `year`: Integer year
- `prevalence`: HIV prevalence (%)
- `incidence`: New infections
- `deaths`: HIV-related deaths
- `total_population`: Total population
- `births`: Number of births
- `total_deaths`: All-cause deaths

**Optional Columns** (for enhanced validation):
- `prevalence_15_49`: HIV prevalence ages 15-49
- `prevalence_male`: Male HIV prevalence
- `prevalence_female`: Female HIV prevalence
- `art_coverage`: % on ART
- `pmtct_coverage`: % pregnant women on PMTCT

### Mapping Model Outputs to UN Indicators

The validation script uses this mapping:

```python
indicator_map = {
    'hiv_prevalence_15_49': 'prevalence',
    'new_hiv_infections': 'incidence',
    'hiv_deaths': 'deaths',
    'population_total': 'total_population',
    'births': 'births',
    'deaths': 'total_deaths'
}
```

**Customize** this mapping in `validate_model.py` to match your actual model output column names.

## Troubleshooting

### API Issues

**Problem**: API returns 401 Unauthorized
```
Solution: Check bearer token hasn't expired (valid until 2056-04-15)
```

**Problem**: API returns empty data
```
Solution: 
1. Verify location code (120 for Cameroon)
2. Check indicator code is correct
3. Verify year range has available data
```

**Problem**: Rate limiting / timeouts
```
Solution: Script includes 0.5s delay between requests. Increase if needed:
time.sleep(1.0)  # Increase delay to 1 second
```

### Validation Issues

**Problem**: "No model results found"
```
Solution: 
1. Check results directory path is correct
2. Verify scenario name matches directory name exactly
3. Ensure model simulation completed successfully
```

**Problem**: "Year mismatch" warnings
```
Solution: Model must output data for ALL years in validation targets.
Check model run period: 1990-2023 for full validation.
```

**Problem**: Low validation metrics (R² < 0.85)
```
Solution:
1. Calibrate model parameters
2. Check for systematic bias (positive = over-prediction)
3. Verify model structure captures key dynamics
4. Consider additional data sources (CAMPHIA surveys)
```

## Advanced Usage

### Custom Time Periods

Edit `un_api_config.json`:
```json
"time_period": {
  "calibration": {
    "start": 1990,
    "end": 2010
  },
  "validation": {
    "start": 2011,
    "end": 2023
  }
}
```

### Additional Indicators

Add to `un_api_config.json`:
```json
"indicators": {
  "hiv": {
    "art_coverage": {
      "code": 107,
      "name": "ART coverage (%)",
      "description": "% of PLHIV on ART"
    }
  }
}
```

Then fetch:
```bash
python fetch_un_data.py --indicator art_coverage
```

### Batch Processing

Create shell script for multiple scenarios:
```bash
#!/bin/bash
# validate_all.sh

for scenario in S0_baseline S1a_optimistic_funding S1b_pessimistic_funding S3a_PSN
do
  echo "Validating $scenario..."
  python validate_model.py --scenario $scenario --period both
done

echo "All scenarios validated!"
```

## Data Sources

- **UN Population Data Portal**: https://population.un.org/dataportal/
- **API Documentation**: https://population.un.org/dataportalapi/
- **Cameroon Data**: Location code 120
- **Indicators**: World Population Prospects 2024 Revision

## Citation

When using UN data for validation, cite:

> United Nations, Department of Economic and Social Affairs, Population Division (2024). World Population Prospects 2024, Online Edition. Available at: https://population.un.org/dataportal/

## Contact

For issues with:
- **UN API**: Contact UN Population Division
- **Model validation**: See main HIVEC-CM README
- **Integration**: Check model documentation

## References

1. Nash, J.E., Sutcliffe, J.V. (1970). River flow forecasting through conceptual models part I. *Journal of Hydrology*, 10(3), 282-290.

2. Moriasi, D.N., et al. (2007). Model evaluation guidelines for systematic quantification of accuracy in watershed simulations. *Transactions of the ASABE*, 50(3), 885-900.

3. United Nations (2024). World Population Prospects 2024. UN Department of Economic and Social Affairs, Population Division.

---

**Last Updated**: 2024  
**Version**: 1.0  
**Maintainer**: HIVEC-CM Model Team
