# Next Steps: Iterative Calibration Refinement Guide

**Date:** October 25, 2025  
**Current Status:** Initial calibration complete, model runs successfully  
**Priority:** Refine initial conditions and transmission parameters

---

## 🎯 Current Situation

### ✅ What's Working
- Calibration infrastructure fully operational (960 iterations completed)
- Model simulates successfully from 1985-2022 with calibrated parameters
- **ART coverage model excellent** (R² = 0.97) - validates model structure
- Complete validation pipeline functional
- All documentation comprehensive

### ⚠️ What Needs Refinement
- **HIV prevalence 1990:** 1.24% (model) vs 0.50% (UNAIDS target) - **too high by 148%**
- Epidemic trajectory: Model shows decline, UNAIDS shows growth
- Population growth: Model too fast (need demographic adjustment)

---

## 🔄 Recommended Iterative Calibration Workflow

### **Phase 1: Adjust Initial Seeding (Priority: HIGH)**

**Goal:** Match 1990 prevalence of 0.50%

**Action Steps:**

1. **Reduce Initial HIV Prevalence**
   
   Edit `config/parameters.json`:
   ```json
   "transmission": {
       "base_transmission_rate": 0.0035,  // Reset to original
       "initial_hiv_prevalence": 0.001,   // Reduce from 0.00312 to 0.001
       ...
   }
   ```

2. **Run Short Simulation to Test**
   ```bash
   python scripts/run_simulation.py \
       --config config/parameters.json \
       --population 10000 \
       --start-year 1985 \
       --years 5 \
       --output-dir results/calibration_test_phase1
   ```

3. **Check 1990 Prevalence**
   ```bash
   tail -1 results/calibration_test_phase1/simulation_results.csv
   # Look at hiv_prevalence column - should be ~0.005 (0.5%)
   ```

4. **Iterate Until 1990 Match**
   - If prevalence < 0.5%: increase `initial_hiv_prevalence` slightly
   - If prevalence > 0.5%: decrease `initial_hiv_prevalence` slightly
   - Repeat steps 2-3 until within 0.1% of target

---

### **Phase 2: Calibrate Growth Phase (1990-2000)**

**Goal:** Match epidemic growth trajectory

**Action Steps:**

1. **Adjust Transmission Parameters**
   
   Once 1990 matches, tune growth rate:
   ```json
   "transmission": {
       "base_transmission_rate": 0.004,  // Increase for growth
       ...
   },
   "social_behavioral": {
       "mean_contacts_per_year": 3.0,    // Moderate increase
       ...
   }
   ```

2. **Run to 2000**
   ```bash
   python scripts/run_simulation.py \
       --start-year 1985 \
       --years 15 \
       --output-dir results/calibration_test_phase2
   ```

3. **Target Metrics for 2000:**
   - HIV prevalence: ~2.0% (UNAIDS)
   - PLHIV: ~200-250k (scaled)

4. **Iterate on Transmission Rate**
   - If growth too slow: increase `base_transmission_rate`
   - If growth too fast: decrease `base_transmission_rate`
   - Adjust `mean_contacts_per_year` for fine-tuning

---

### **Phase 3: Full Period Calibration (1985-2023)**

**Goal:** Match entire trajectory with interventions

**Action Steps:**

1. **Run Full Simulation**
   ```bash
   python scripts/run_simulation.py \
       --start-year 1985 \
       --years 38 \
       --output-dir results/calibration_full
   ```

2. **Validate All Periods**
   ```bash
   cd validation
   # Create summary statistics file (see script below)
   python create_validation_summary.py
   
   # Run validation
   python quick_validate.py --scenario calibrated --period both
   ```

3. **Generate Diagnostics**
   ```bash
   python generate_diagnostics.py --scenario calibrated
   ```

4. **Check Target Metrics:**
   - 1990: Prevalence = 0.5%
   - 2000: Prevalence = 2.0%
   - 2010: Prevalence = 2.8%
   - 2015: Prevalence = 3.2%
   - 2023: Prevalence = 3.4%
   - ART coverage 2023: ~81%

---

### **Phase 4: Automated Re-Calibration**

If manual adjustment is too slow, run automated calibration with true model runs:

**Action Steps:**

1. **Create True Objective Function**
   
   Modify `validation/calibrate_model.py`:
   - Replace `_simulate_with_params()` with actual model run
   - This will be slower (~30 sec per evaluation) but more accurate

2. **Run Automated Calibration**
   ```bash
   python validation/calibrate_model_v2.py \
       --max-iterations 30 \
       --population 10000 \
       --method differential_evolution
   ```
   
   Expected runtime: ~5-10 hours (30 iterations × 30 sec × population evaluations)

3. **Apply Optimal Parameters**
   ```bash
   # Results will be in validation_outputs/calibrated_parameters_v2.json
   python scripts/apply_calibrated_params.py
   ```

---

## 📊 Target Metrics Summary

### UNAIDS Cameroon Validation Targets

| Year | Prevalence (%) | PLHIV (000s) | New Infections (000s) | ART Coverage (%) |
|------|----------------|--------------|----------------------|------------------|
| 1990 | 0.5 | 50 | 10 | 0 |
| 2000 | 2.0 | 200 | 30 | 0 |
| 2010 | 2.8 | 310 | 25 | 32 |
| 2015 | 3.2 | 375 | 20 | 54 |
| 2020 | 3.4 | 400 | 15 | 73 |
| 2023 | 3.4 | 410 | 12 | 81 |

### Acceptance Criteria (per indicator)
- **R² ≥ 0.85** (explains 85%+ of variance)
- **Relative Bias ≤ ±15%** (systematic error)
- **NSE ≥ 0.70** (Nash-Sutcliffe Efficiency)

---

## 🛠️ Helper Scripts

### Quick Check Script

Save as `scripts/quick_check_calibration.py`:

```python
#!/usr/bin/env python3
"""Quick check of current calibration status"""
import pandas as pd
import sys

# Load simulation results
df = pd.read_csv('results/calibration_full/simulation_results.csv')
df = df.drop_duplicates(subset=['year'], keep='last')

# Scale factor
SCALE = 1190.0

# Target years and values (UNAIDS)
targets = {
    1990: 0.5,
    2000: 2.0,
    2010: 2.8,
    2015: 3.2,
    2020: 3.4,
    2023: 3.4
}

print("="*60)
print("CALIBRATION CHECK")
print("="*60)
print(f"Year | Model Prev | Target Prev | Error")
print("-"*60)

errors = []
for year, target in targets.items():
    if year in df['year'].values:
        row = df[df['year'] == year].iloc[0]
        model_prev = row['hiv_prevalence'] * 100
        error = model_prev - target
        errors.append(abs(error))
        status = "✅" if abs(error) < 0.5 else "⚠️" if abs(error) < 1.0 else "❌"
        print(f"{year} | {model_prev:>9.2f}% | {target:>10.2f}% | {error:>+6.2f}% {status}")

print("-"*60)
print(f"Mean Absolute Error: {sum(errors)/len(errors):.2f}%")
print(f"Max Error: {max(errors):.2f}%")
print()

if max(errors) < 0.5:
    print("🎉 Excellent calibration! All years within 0.5%")
elif max(errors) < 1.0:
    print("✅ Good calibration! All years within 1.0%")
elif max(errors) < 2.0:
    print("⚠️  Acceptable calibration, but needs improvement")
else:
    print("❌ Poor calibration - iterative refinement needed")
```

Run with:
```bash
python scripts/quick_check_calibration.py
```

---

### Parameter Sweep Script

Save as `scripts/parameter_sweep.py`:

```python
#!/usr/bin/env python3
"""
Sweep initial prevalence to find optimal 1990 match
"""
import subprocess
import pandas as pd
import numpy as np

print("="*60)
print("PARAMETER SWEEP: Initial HIV Prevalence")
print("="*60)

# Test range
init_prev_values = np.linspace(0.0005, 0.003, 10)

results = []
for init_prev in init_prev_values:
    print(f"\nTesting initial_hiv_prevalence = {init_prev:.5f}")
    
    # Update parameters (simplified - need to properly edit JSON)
    # ... JSON update code here ...
    
    # Run simulation
    subprocess.run([
        'python', 'scripts/run_simulation.py',
        '--start-year', '1985',
        '--years', '5',
        '--population', '10000',
        '--output-dir', f'results/sweep_{init_prev:.5f}'
    ], capture_output=True)
    
    # Read results
    df = pd.read_csv(f'results/sweep_{init_prev:.5f}/simulation_results.csv')
    df = df.drop_duplicates(subset=['year'], keep='last')
    
    if 1990 in df['year'].values:
        prev_1990 = df[df['year'] == 1990].iloc[0]['hiv_prevalence'] * 100
        error = abs(prev_1990 - 0.5)
        results.append({
            'init_prev': init_prev,
            'prev_1990': prev_1990,
            'error': error
        })
        print(f"  → 1990 prevalence: {prev_1990:.3f}% (error: {error:.3f}%)")

# Find best
results_df = pd.DataFrame(results)
best = results_df.loc[results_df['error'].idxmin()]
print("\n" + "="*60)
print(f"🎯 BEST PARAMETER:")
print(f"   initial_hiv_prevalence = {best['init_prev']:.5f}")
print(f"   → 1990 prevalence = {best['prev_1990']:.3f}%")
print(f"   → Error = {best['error']:.3f}%")
print("="*60)
```

---

## 📝 Quick Commands Reference

### Test Current Parameters
```bash
# Run 5-year test
python scripts/run_simulation.py --start-year 1985 --years 5 --population 10000 --output-dir results/test

# Check 1990 result
tail -1 results/test/simulation_results.csv | awk -F',' '{print "Prevalence:", $15 * 100 "%"}'
```

### Run Full Calibration Test
```bash
# Full 38-year run
python scripts/run_simulation.py --start-year 1985 --years 38 --population 10000 --output-dir results/calibration_full

# Quick validation check
python scripts/quick_check_calibration.py
```

### Generate Validation Report
```bash
cd validation

# Create summary stats
python -c "
import pandas as pd
from pathlib import Path
df = pd.read_csv('../results/calibration_full/simulation_results.csv')
df = df.drop_duplicates(subset=['year'], keep='last')
# ... create summary_statistics.csv in expected format ...
"

# Run validation
python quick_validate.py --scenario calibrated --period both

# Generate diagnostics
python generate_diagnostics.py --scenario calibrated
```

---

## 🎯 Success Milestones

### Milestone 1: Initial Seeding ✅ (When Achieved)
- [ ] 1990 prevalence within 0.2% of 0.5% target
- [ ] Simulation runs without errors
- [ ] Initial conditions documented

### Milestone 2: Growth Phase ✅ (When Achieved)
- [ ] 1990-2000 trajectory matches UNAIDS trend
- [ ] 2000 prevalence within 0.5% of 2.0% target
- [ ] R² > 0.5 for prevalence (1990-2000)

### Milestone 3: Full Calibration ✅ (When Achieved)
- [ ] All years 1990-2023 within acceptance criteria
- [ ] HIV prevalence R² ≥ 0.85
- [ ] All 6 indicators pass validation
- [ ] ART coverage maintains R² > 0.95

### Milestone 4: Publication Ready ✅ (When Achieved)
- [ ] Monte Carlo runs (20 iterations) show consistent results
- [ ] Sensitivity analysis completed
- [ ] All diagnostic plots publication-quality
- [ ] Methods section written
- [ ] Supplementary materials prepared

---

## 💾 Backup Current State

Before starting refinement, backup current configuration:

```bash
# Backup current parameters
cp config/parameters.json config/parameters_calibrated_v1.json

# Backup results
cp -r results/calibrated_validation_simple results/calibrated_validation_simple_backup

# Tag in git
git add .
git commit -m "Checkpoint: Initial calibration complete, starting iterative refinement"
git tag v1.0-calibration-initial
```

---

## 📚 References

### Key Documents
- `VALIDATION_INFRASTRUCTURE_COMPLETE.md` - Complete infrastructure guide
- `VALIDATION_EXECUTION_SUMMARY.md` - Detailed execution log
- `CALIBRATED_SIMULATION_RESULTS.md` - Current simulation results
- `validation_outputs/calibrated_parameters.json` - Optimization results

### UNAIDS Data Source
- `data/validation_targets/unaids_cameroon_data.json`
- Calibration period: 1990-2015
- Validation period: 2016-2023

---

## ⏱️ Expected Timeline

### Manual Iterative Refinement
- **Phase 1 (Initial Seeding):** 2-4 hours (5-10 iterations × 5 min each)
- **Phase 2 (Growth Phase):** 3-6 hours (5-10 iterations × 15 min each)
- **Phase 3 (Full Period):** 1-2 hours (2-3 iterations × 30 min each)
- **Total:** 6-12 hours

### Automated Re-Calibration
- **Setup:** 2 hours (modify calibration script)
- **Execution:** 5-10 hours (30 evaluations × 30 sec × population)
- **Validation:** 1 hour
- **Total:** 8-13 hours

---

**Status:** Ready to begin Phase 1  
**Next Action:** Adjust `initial_hiv_prevalence` to 0.001 and test  
**Priority:** HIGH - Foundation for all subsequent calibration

---

*This guide provides a systematic approach to achieving publication-ready model calibration through iterative refinement.*
