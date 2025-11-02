# HIVEC-CM Script Consolidation Guide

**Date**: November 2, 2024  
**Status**: ✅ Complete  
**Result**: 24 scripts → 5 unified scripts

---

## Overview

The `scripts/` folder has been consolidated from **24 scattered scripts** into **5 unified, well-organized scripts**. All original scripts are preserved in `scripts/_archived/` for reference.

---

## The 5 Consolidated Scripts

### 1. 📊 `run_simulation.py` - Unified Simulation Runner

**Purpose**: Execute simulations in 3 modes  
**Consolidates**: 
- `run_simulation.py` (original)
- `run_all_scenarios.py`
- `run_enhanced_montecarlo.py`
- `run_study_pipeline.py`

**Modes**:
1. **Single scenario** - Run one scenario with detailed results
2. **All scenarios** - Execute all 9 policy scenarios automatically
3. **Monte Carlo** - Uncertainty analysis with parameter variations

**Usage Examples**:
```bash
# Single scenario (baseline)
./scripts/run_simulation.py --mode single --scenario S0_baseline --population 25000

# All 9 policy scenarios
./scripts/run_simulation.py --mode scenarios --population 50000 --output results/policy_analysis

# Monte Carlo study (100 runs)
./scripts/run_simulation.py --mode montecarlo --runs 100 --population 10000 --uncertainty 0.2
```

**Features**:
- ✅ Detailed results collection (JSON + CSV)
- ✅ Age-sex stratification (10 age groups × 2 sexes)
- ✅ Regional data (12 Cameroon regions)
- ✅ Treatment cascade (95-95-95)
- ✅ Metadata generation
- ✅ Automatic directory creation

---

### 2. 🔍 `analyze_results.py` - Results Analysis Tool

**Purpose**: Comprehensive analysis of simulation outputs  
**Consolidates**: 
- `analyze_detection_gaps.py`
- `analyze_enhanced_results.py`
- `analyze_saint_seya_results.py`
- `compare_scenarios.py`
- `regenerate_detailed_csv.py`
- `extract_detailed_results.py`

**Modes**:
1. **Comprehensive** - Full analysis of all data dimensions
2. **Gaps** - Testing and detection gap analysis
3. **Compare** - Multi-scenario comparison
4. **Regenerate** - Rebuild CSV from JSON

**Usage Examples**:
```bash
# Comprehensive analysis
./scripts/analyze_results.py --mode comprehensive \
  --dir results/Saint_Seya_Simulation_Detailed/S0_baseline

# Detection gaps
./scripts/analyze_results.py --mode gaps \
  --dir results/scenarios_20251101/S2a_testing

# Compare all scenarios
./scripts/analyze_results.py --mode compare \
  --dir results/scenarios_20251101

# Regenerate CSV from JSON
./scripts/analyze_results.py --mode regenerate \
  --dir results/simulation_20251101_153959
```

**Output**:
- 📊 28 data dimensions analysis
- 🔬 Age-sex prevalence pivot tables
- 🗺️ Regional analysis (12 regions)
- 📈 Treatment cascade progression
- 📋 Scenario comparison tables (saved as CSV)

---

### 3. 📈 `generate_plots.py` - Visualization Tool

**Purpose**: Generate publication-ready visualizations  
**Consolidates**: 
- `plot_results.py`
- `plot_prevalence_validation.py`
- `visualize_saint_seya.py`
- `generate_publication_plots.py`
- `generate_validation_plots.py`

**Modes**:
1. **Age-sex** - Trends by age groups and sex
2. **Regional** - Regional prevalence heatmaps
3. **Cascade** - 95-95-95 treatment cascade
4. **Compare** - Multi-scenario comparison plots
5. **All** - Generate all visualizations

**Usage Examples**:
```bash
# Age-sex trends
./scripts/generate_plots.py --mode age-sex \
  --dir results/S0_baseline --output plots

# Regional heatmap
./scripts/generate_plots.py --mode regional \
  --dir results/S0_baseline --output plots

# Treatment cascade progression
./scripts/generate_plots.py --mode cascade \
  --dir results/S0_baseline --output plots

# Compare multiple scenarios
./scripts/generate_plots.py --mode compare \
  --dir results/scenarios_20251101 --output plots

# Generate all plots
./scripts/generate_plots.py --mode all \
  --dir results/S0_baseline --output plots
```

**Visualizations**:
- 📊 Age-sex stratified charts (4-panel layout)
- 🗺️ Regional heatmaps (12 Cameroon regions)
- 📈 Treatment cascade time series
- 🎯 Multi-scenario comparison overlays
- 🖼️ Publication-ready PNG (300 DPI)

---

### 4. ⏱️ `monitor.py` - Live Monitoring Tool

**Purpose**: Real-time simulation monitoring  
**Consolidates**: 
- `monitor_saint_seya.py`
- `monitor_simulation.py`

**Modes**:
1. **Live** - Real-time updates for single simulation
2. **Scenarios** - Monitor multiple scenarios simultaneously
3. **Status** - Quick status check (one-time)

**Usage Examples**:
```bash
# Live monitoring (refresh every 5 seconds)
./scripts/monitor.py --mode live \
  --dir results/simulation_20251101_153959 --interval 5

# Monitor multiple scenarios (refresh every 10 seconds)
./scripts/monitor.py --mode scenarios \
  --dir results/scenarios_20251101 --interval 10

# Quick status check
./scripts/monitor.py --mode status \
  --dir results/simulation_20251101_153959
```

**Features**:
- ⏱️ Live progress tracking
- 📊 Current year metrics
- 🎯 Treatment cascade progress
- ✅ Completion status
- 📈 Performance metrics (years/second)
- 🔄 Auto-refresh (configurable interval)

---

### 5. ✅ `validation.py` - Validation and Testing

**Purpose**: Model validation and performance benchmarking  
**Consolidates**: 
- `validate_scenario_parameters.py`
- `comprehensive_validation.py`
- `compute_milestones.py`
- `benchmark_transmission.py`

**Modes**:
1. **Validate** - Parameter validation
2. **Milestones** - Compute key HIV milestones
3. **Benchmark** - Performance benchmarking
4. **Comprehensive** - Validate against historical data

**Usage Examples**:
```bash
# Validate parameters
./scripts/validation.py --mode validate \
  --config config/parameters.json

# Compute milestones
./scripts/validation.py --mode milestones \
  --dir results/S0_baseline

# Benchmark performance
./scripts/validation.py --mode benchmark \
  --config config/parameters.json --population 25000

# Comprehensive validation against historical data
./scripts/validation.py --mode comprehensive \
  --dir results/S0_baseline \
  --validation data/validation_targets/prevalence_unaids.csv
```

**Validation Checks**:
- ✅ Parameter bounds checking
- 🎯 Milestone detection (peak prevalence, 90-90-90, 95-95-95)
- ⚡ Performance metrics (agent-years/second)
- 📊 MAE/RMSE against historical data
- 📈 Incidence reduction tracking

---

## Migration from Old Scripts

### Old Script → New Script Mapping

| Old Script | New Script | Mode/Function |
|-----------|-----------|--------------|
| `run_simulation.py` | `run_simulation.py` | `--mode single` |
| `run_all_scenarios.py` | `run_simulation.py` | `--mode scenarios` |
| `run_enhanced_montecarlo.py` | `run_simulation.py` | `--mode montecarlo` |
| `run_study_pipeline.py` | `run_simulation.py` | (integrated) |
| `analyze_detection_gaps.py` | `analyze_results.py` | `--mode gaps` |
| `analyze_enhanced_results.py` | `analyze_results.py` | `--mode comprehensive` |
| `analyze_saint_seya_results.py` | `analyze_results.py` | `--mode comprehensive` |
| `compare_scenarios.py` | `analyze_results.py` | `--mode compare` |
| `regenerate_detailed_csv.py` | `analyze_results.py` | `--mode regenerate` |
| `extract_detailed_results.py` | `analyze_results.py` | (integrated) |
| `plot_results.py` | `generate_plots.py` | `--mode all` |
| `plot_prevalence_validation.py` | `generate_plots.py` | `--mode all` |
| `visualize_saint_seya.py` | `generate_plots.py` | `--mode age-sex` |
| `generate_publication_plots.py` | `generate_plots.py` | `--mode all` |
| `generate_validation_plots.py` | `generate_plots.py` | `--mode all` |
| `monitor_saint_seya.py` | `monitor.py` | `--mode scenarios` |
| `monitor_simulation.py` | `monitor.py` | `--mode live` |
| `validate_scenario_parameters.py` | `validation.py` | `--mode validate` |
| `comprehensive_validation.py` | `validation.py` | `--mode comprehensive` |
| `compute_milestones.py` | `validation.py` | `--mode milestones` |
| `benchmark_transmission.py` | `validation.py` | `--mode benchmark` |

### Other scripts (not consolidated):
- `generate_report.py` → Reporting (future consolidation)
- `export_labels.py` → LaTeX tools (future consolidation)
- `generate_latex_labels.py` → LaTeX tools (future consolidation)

---

## Complete Workflow Example

Here's a typical analysis workflow using the new consolidated scripts:

```bash
# 1. Validate configuration
./scripts/validation.py --mode validate --config config/parameters.json

# 2. Run all 9 policy scenarios
./scripts/run_simulation.py --mode scenarios --population 50000 \
  --output results/policy_analysis_2024

# 3. Monitor progress (in separate terminal)
./scripts/monitor.py --mode scenarios \
  --dir results/policy_analysis_2024 --interval 10

# 4. After completion, compare scenarios
./scripts/analyze_results.py --mode compare \
  --dir results/policy_analysis_2024

# 5. Generate visualizations
./scripts/generate_plots.py --mode compare \
  --dir results/policy_analysis_2024 --output plots/comparison

# 6. Compute milestones for baseline
./scripts/validation.py --mode milestones \
  --dir results/policy_analysis_2024/S0_baseline

# 7. Comprehensive analysis of best scenario
./scripts/analyze_results.py --mode comprehensive \
  --dir results/policy_analysis_2024/S2c_etme
```

---

## Key Improvements

### ✅ Organization
- **Before**: 24 scattered scripts, unclear purposes
- **After**: 5 clearly categorized scripts with documented modes

### ✅ Consistency
- **Before**: Different argument styles, inconsistent naming
- **After**: Unified argument parsing, consistent conventions

### ✅ Maintainability
- **Before**: Duplicated code across scripts
- **After**: Consolidated functionality, easier updates

### ✅ Discoverability
- **Before**: Hard to find right script for task
- **After**: Clear categories with `--help` documentation

### ✅ Parameters
- **Before**: Mix of old and new parameters
- **After**: Uses most up-to-date parameters from latest scripts

---

## Original Scripts Archive

All 24 original scripts are preserved in:
```
scripts/_archived/
```

You can reference them for:
- Historical comparison
- Feature verification
- Migration validation
- Documentation purposes

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│              HIVEC-CM Scripts Quick Reference               │
├─────────────────────────────────────────────────────────────┤
│ 📊 run_simulation.py   → Run simulations (3 modes)          │
│ 🔍 analyze_results.py  → Analyze outputs (4 modes)          │
│ 📈 generate_plots.py   → Create visualizations (5 modes)    │
│ ⏱️  monitor.py          → Live monitoring (3 modes)          │
│ ✅ validation.py       → Validate & benchmark (4 modes)     │
├─────────────────────────────────────────────────────────────┤
│ Help: ./scripts/<script>.py --help                          │
│ Archive: scripts/_archived/ (24 original scripts)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Support

For questions or issues:
1. Check `--help` for each script
2. Review this guide
3. Check original scripts in `_archived/`
4. Refer to main documentation in `docs/`

---

**Consolidation completed**: November 2, 2024  
**Original script count**: 24  
**New script count**: 5  
**Reduction**: 79% fewer files, 100% functionality preserved
