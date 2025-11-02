# HIVEC-CM Monte Carlo Simulation Results
## Baseline and Financial Scenarios (1985-2050)

**Simulation Date:** October 9, 2025  
**Status:** ✅ **COMPLETE**

---

## Simulation Configuration

### Scenarios Analyzed
1. **S0_baseline** - Baseline (Status Quo)
   - Current trends and programming levels continue
   - 2022 performance baseline

2. **S1a_optimistic_funding** - Optimistic Funding
   - 20% budget increase through domestic mobilization
   - Enhanced service delivery across all programs

3. **S1b_pessimistic_funding** - Pessimistic Funding
   - 20% budget cut from international funding reduction
   - Reduced program coverage and service delivery

### Simulation Parameters

| Parameter | Value |
|-----------|-------|
| **Start Year** | 1985 |
| **End Year** | 2050 |
| **Duration** | 65 years |
| **Initial Population** | 10,000 agents |
| **Monte Carlo Iterations** | 50 per scenario |
| **Total Iterations** | 150 (3 scenarios × 50) |
| **Time Step** | 1.0 year |
| **CPU Cores Used** | 8 (parallel processing) |
| **Total Runtime** | 8.1 minutes |
| **Throughput** | ~18.5 iterations/minute |

---

## Performance Metrics

### Individual Scenario Performance

| Scenario | Runtime | Avg/Iteration | Throughput |
|----------|---------|---------------|------------|
| **S0_baseline** | 3.0 minutes | 3.6 seconds | 16.8 iter/min |
| **S1a_optimistic_funding** | 2.6 minutes | 3.2 seconds | 19.0 iter/min |
| **S1b_pessimistic_funding** | 2.5 minutes | 3.0 seconds | 20.3 iter/min |

**Overall Average:** 3.3 seconds per iteration across all scenarios

---

## Output Structure

### Directory Organization

```
results/montecarlo_scenarios/
│
├── S0_baseline/
│   └── 20251009_095853/
│       ├── raw_results.csv (3,300 rows - 50 iterations × 66 years)
│       ├── summary_statistics.csv
│       ├── confidence_intervals.csv
│       ├── runtime_statistics.json
│       └── run_config.json
│
├── S1a_optimistic_funding/
│   └── 20251009_100152/
│       ├── raw_results.csv (3,300 rows)
│       ├── summary_statistics.csv
│       ├── confidence_intervals.csv
│       ├── runtime_statistics.json
│       └── run_config.json
│
├── S1b_pessimistic_funding/
│   └── 20251009_100429/
│       ├── raw_results.csv (3,300 rows)
│       ├── summary_statistics.csv
│       ├── confidence_intervals.csv
│       ├── runtime_statistics.json
│       └── run_config.json
│
└── scenario_comparison/
    └── 20251009_100657/
        ├── all_scenarios_summary.csv
        ├── study_metadata.json
        └── plots/
            ├── scenario_comparison_comprehensive.png
            └── final_year_summary.csv
```

### Output Files Description

#### Raw Results (`raw_results.csv`)
- **Size:** 3,300 rows per scenario (50 iterations × 66 years)
- **Total:** 9,900 rows across all scenarios
- **Contains:** Year-by-year results for each iteration
- **Key Variables:**
  - `year`: Simulation year (1985-2050)
  - `iteration`: Monte Carlo iteration number (0-49)
  - `scenario`: Scenario ID
  - `hiv_prevalence`: HIV prevalence rate
  - `new_infections`: Annual new HIV infections
  - `deaths_hiv`: Annual HIV-related deaths
  - `on_art`: Number of people on antiretroviral treatment
  - `total_population`: Total population size
  - `runtime_seconds`: Computational time for iteration
  - `seed`: Random seed used

#### Summary Statistics (`summary_statistics.csv`)
- **Contains:** Aggregated statistics across all iterations for each year
- **Metrics:** Mean, Std, Min, Max, Median
- **Variables:**
  - HIV prevalence
  - New infections
  - HIV deaths
  - ART coverage
  - Population size

#### Confidence Intervals (`confidence_intervals.csv`)
- **Contains:** 95% confidence intervals (2.5th and 97.5th percentiles)
- **Purpose:** Uncertainty quantification for key indicators
- **Variables:**
  - HIV prevalence (p2.5, p97.5)
  - New infections (p2.5, p97.5)

#### Runtime Statistics (`runtime_statistics.json`)
- Total runtime (seconds and minutes)
- Average iteration time
- Success/failure counts
- Throughput metrics

#### Run Configuration (`run_config.json`)
- Complete simulation parameters
- Scenario-specific parameters
- Timestamp and metadata
- Reproducibility information

---

## Key Results Summary

### Baseline Scenario (S0_baseline)
- **Purpose:** Reference scenario showing HIV epidemic trajectory under current trends
- **Iterations:** 50 successful
- **Data Points:** 3,300 year-iteration combinations
- **Coverage:** 1985-2050 (65 years)

### Optimistic Funding Scenario (S1a_optimistic_funding)
- **Purpose:** Assess impact of 20% budget increase on epidemic outcomes
- **Key Changes:** Enhanced testing, treatment, and prevention coverage
- **Expected Impact:** Reduced incidence and mortality

### Pessimistic Funding Scenario (S1b_pessimistic_funding)
- **Purpose:** Assess consequences of 20% funding cuts
- **Key Changes:** Reduced service coverage, increased stockouts
- **Expected Impact:** Increased incidence and mortality

---

## Analysis and Visualization

### Generated Plots

**Comprehensive Comparison Plot** (`scenario_comparison_comprehensive.png`)
- Four-panel figure showing:
  1. HIV Prevalence Trajectory (1985-2050)
  2. Annual New Infections
  3. HIV-Related Deaths
  4. ART Coverage

Each plot includes:
- Mean trajectories for all three scenarios
- Uncertainty bounds (min-max range)
- Color-coded by scenario
- Grid and legend

### Statistical Comparison

**Final Year Summary** (`final_year_summary.csv`)
- Tabular comparison of 2050 outcomes
- HIV prevalence
- Total new infections
- Total HIV deaths
- Scenario-to-baseline differences

---

## Reproducibility Information

### Random Seeds
- **Base seed:** 42
- **Scenario-specific offsets:** 
  - S0_baseline: seed + 1
  - S1a_optimistic_funding: seed + 2
  - S1b_pessimistic_funding: seed + 3
- **Iteration-specific:** Each iteration gets unique seed based on:
  - `(base_seed + iteration_id + hash(scenario_id)) % (2^31 - 1)`

### Software Environment
- **Model:** HIVEC-CM (HIV Epidemic Cameroon Model)
- **Python Version:** 3.13
- **Key Dependencies:**
  - numpy, pandas, matplotlib, seaborn
  - multiprocessing (parallel processing)
  - tqdm (progress monitoring)

### Computational Resources
- **Cores Used:** 8 (full parallel processing)
- **Processing Mode:** Fastest available
- **Memory:** Efficient iteration-based processing
- **Total CPU Time:** ~8 minutes wall-clock time

---

## Quality Assurance

### Validation Checks
✅ **All 150 iterations completed successfully** (50 per scenario)  
✅ **No failed iterations**  
✅ **All output files generated correctly**  
✅ **Data integrity verified** (3,300 rows per scenario)  
✅ **Statistical summaries computed**  
✅ **Confidence intervals calculated**  
✅ **Visualization generated**  

### Data Completeness
- ✅ Raw results: 100% complete
- ✅ Summary statistics: 100% complete
- ✅ Confidence intervals: 100% complete
- ✅ Runtime metrics: 100% complete
- ✅ Comparison data: 100% complete

---

## Next Steps

### Recommended Analyses

1. **Time Series Analysis**
   - Examine trajectory patterns
   - Identify inflection points
   - Assess intervention timing effects

2. **Scenario Comparison**
   - Quantify differences vs baseline
   - Calculate infections/deaths averted
   - Estimate cost-effectiveness

3. **Uncertainty Analysis**
   - Examine confidence interval widths
   - Identify high-uncertainty periods
   - Assess parameter sensitivity

4. **Policy Implications**
   - Translate findings for policymakers
   - Estimate resource needs
   - Project long-term outcomes

### Additional Scenarios

Consider running complementary scenarios:
- **S2a_intensified_testing** - Testing scale-up
- **S2b_key_populations** - Key population focus
- **S2c_emtct** - PMTCT enhancement
- **S2d_youth_focus** - Youth programs
- **S3a_psn_aspirational** - Full PSN 2024-2030 implementation

---

## Access and Usage

### Data Access
All results are stored in:
```bash
results/montecarlo_scenarios/
```

### Loading Results in Python

```python
import pandas as pd

# Load baseline results
baseline = pd.read_csv('results/montecarlo_scenarios/S0_baseline/20251009_095853/raw_results.csv')

# Load optimistic funding results
optimistic = pd.read_csv('results/montecarlo_scenarios/S1a_optimistic_funding/20251009_100152/raw_results.csv')

# Load pessimistic funding results
pessimistic = pd.read_csv('results/montecarlo_scenarios/S1b_pessimistic_funding/20251009_100429/raw_results.csv')

# Load comparison summary
comparison = pd.read_csv('results/montecarlo_scenarios/scenario_comparison/20251009_100657/all_scenarios_summary.csv')
```

### Re-running Analysis

```bash
# Re-analyze results
python scripts/analyze_montecarlo_scenarios.py

# Run additional scenarios
python scripts/run_scenario_montecarlo.py --scenarios S2a_intensified_testing S3a_psn_aspirational --start-year 1985 --end-year 2050 --population 10000 --iterations 50 --cores 8
```

---

## Summary

✅ **Simulation Status:** COMPLETE  
✅ **Total Iterations:** 150 (50 per scenario)  
✅ **Runtime:** 8.1 minutes  
✅ **Success Rate:** 100%  
✅ **Output Files:** 15+ files across 3 scenarios  
✅ **Data Points:** 9,900 year-iteration combinations  
✅ **Visualization:** Comprehensive comparison plots generated  

The HIVEC-CM Monte Carlo simulation for baseline and financial scenarios has been completed successfully. All results are stored in organized directories with comprehensive statistical summaries, confidence intervals, and visualizations ready for policy analysis.

---

**For Questions or Additional Analysis:**
- Review output files in `results/montecarlo_scenarios/`
- Run analysis script: `python scripts/analyze_montecarlo_scenarios.py`
- Check documentation: `PSN_SCENARIO_PROGRESS.md`, `SCENARIO_QUICK_REFERENCE.md`

**Model:** HIVEC-CM (HIV Epidemic Cameroon Model)  
**Date:** October 9, 2025
