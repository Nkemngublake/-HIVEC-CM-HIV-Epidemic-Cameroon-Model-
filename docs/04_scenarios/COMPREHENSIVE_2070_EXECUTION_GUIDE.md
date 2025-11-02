# Comprehensive Scenario Execution Guide (1985-2070)
**HIVEC-CM HIV Epidemic Model - TRUE vs DETECTED Analysis**

*Execution Date: October 26, 2025*

---

## Overview

This execution runs all 9 policy scenarios from **1985-2070** (85 years) with **100,000 agents** to comprehensively analyze the gap between TRUE epidemiological states and DETECTED cases, enabling calculation of missed HIV-positive individuals due to testing coverage limitations.

### Key Innovation: TRUE vs DETECTED Differentiation

For the first time, the model captures **two parallel data streams**:

1. **TRUE STATES** (Ground Truth): Actual HIV status of all agents
2. **DETECTED STATES** (Health System Knowledge): What testing/diagnosis reveals

This enables calculation of:
- **Missed positives** (undiagnosed HIV+ individuals)
- **Testing coverage gaps**
- **Detection rate evolution**
- **True vs observed 95-95-95 cascade performance**

---

## Execution Configuration

### Simulation Parameters

```yaml
Start Year:           1985
End Year:             2070
Duration:             85 years
Population Size:      100,000 agents
Scaling Ratio:        1:119 (1 agent = 119 real people)
Real Population:      ~11.9 million (Cameroon)
Time Step:            0.1 years (36.5 days per step)
Total Steps:          850 steps per scenario
Scenarios:            9 policy scenarios
```

### Computational Requirements

```yaml
Per Scenario:
  - Agent-years:      8.5 million
  - Execution time:   20-30 minutes
  - Memory usage:     ~2-3 GB peak
  - Storage:          ~200-300 MB

Total (9 scenarios):
  - Agent-years:      76.5 million
  - Execution time:   3-4.5 hours
  - Memory usage:     ~16-24 GB peak
  - Storage:          ~2-3 GB total
```

---

## Enhanced Data Collection

### TRUE Epidemiological States (Ground Truth)

These metrics represent the **actual** state of the epidemic, regardless of whether individuals have been tested or diagnosed:

| Metric | Description | Use Case |
|--------|-------------|----------|
| `hiv_infections` | Total HIV+ individuals (alive) | True epidemic size |
| `acute`, `chronic`, `aids` | HIV+ by disease stage | Disease progression tracking |
| `new_infections` | New HIV infections this year | True incidence |
| `hiv_prevalence` | TRUE HIV prevalence rate | Actual epidemic burden |

**Key Point:** These are the **target metrics** for public health - they represent what we're trying to measure and control.

### DETECTED States (Health System Knowledge)

These metrics represent what the **health system actually knows** based on testing and diagnosis:

| Metric | Description | Depends On |
|--------|-------------|------------|
| `diagnosed` | HIV+ who have been diagnosed | Testing coverage |
| `undiagnosed_hiv` | HIV+ NOT yet diagnosed | **Missed cases** |
| `tested` | People ever tested for HIV | Testing program reach |
| `tested_last_12m` | Tested in last 12 months | Current testing activity |
| `on_art` | On antiretroviral treatment | Linkage to care |
| `virally_suppressed` | Suppressed viral load on ART | Treatment adherence |

**Key Point:** These metrics are **constrained by program capacity** - limited test kits, clinic reach, staff availability.

### Coverage & Detection Metrics

These metrics **quantify the gap** between TRUE and DETECTED states:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| `hiv_prevalence_detected` | diagnosed / population | What surveys measure |
| `testing_coverage` | tested / population | Program reach |
| `diagnosis_rate` | diagnosed / TRUE HIV+ | **First 95 achievement** |
| `undiagnosed_hiv` | TRUE HIV+ - diagnosed | **Missed positives** |
| `missed_cases_pct` | undiagnosed / TRUE HIV+ × 100 | Gap percentage |

### 95-95-95 Cascade: TRUE vs DETECTED Denominators

The **95-95-95 targets** can be measured two ways:

#### Using TRUE Denominator (Epidemiological View)

```
First 95:  diagnosed / TRUE HIV+ ≥ 95%
Second 95: on_art / TRUE HIV+ ≥ 95% of 95% = 90.25%
Third 95:  suppressed / TRUE HIV+ ≥ 95% of 95% of 95% = 85.7%
```

This shows **actual population coverage** but requires knowing true HIV+ count (impossible in reality).

#### Using DETECTED Denominator (Program View - Standard)

```
First 95:  diagnosed / TRUE HIV+ ≥ 95%        (still needs true denominator)
Second 95: on_art / diagnosed ≥ 95%          (achievable with data)
Third 95:  suppressed / on_art ≥ 95%         (achievable with data)
```

This is **what programs can actually measure** from their data systems.

### Model Captures BOTH:

| Metric | Calculation | Notes |
|--------|-------------|-------|
| `art_coverage_true` | on_art / TRUE HIV+ | Cannot measure in reality |
| `art_coverage_detected` | on_art / diagnosed | **Second 95 metric** |
| `suppression_rate_true` | suppressed / TRUE HIV+ | Research metric |
| `suppression_rate_art` | suppressed / on_art | **Third 95 metric** |

---

## Scenarios Being Executed

### 1. S0_baseline (Reference Scenario)

**Status Quo** - maintains 2022 performance levels

```yaml
Testing rate:           29%
ART initiation:         85%
Retention (12 months):  90%
Retention (24 months):  85%
Viral suppression:      75%
Funding multiplier:     1.0
```

**Expected Detection Gaps:**
- Diagnosis rate: ~60-70% by 2030
- Undiagnosed HIV+: 30-40% of true cases
- Testing coverage: ~40% by 2030

---

### 2. S1a_optimistic_funding (+20% Budget)

Increased domestic resource mobilization

```yaml
Funding multiplier:     1.20
Testing rate:           38% (+30%)
ART initiation:         92% (+8%)
Viral suppression:      85% (+10%)
```

**Expected Detection Gaps:**
- Diagnosis rate: ~75-80% by 2030
- Undiagnosed HIV+: 20-25% of true cases
- Improved testing reduces missed cases

---

### 3. S1b_pessimistic_funding (-40% Budget) ⚠️

**CRISIS SCENARIO** - severe international funding cuts starting 2025

```yaml
Funding multiplier:     0.60 (40% cut)
Testing rate:           17% (-41%)
ART initiation:         51% (-40%)
Viral suppression:      50% (-33%)
Treatment interruptions: 25% (5× increase)
KP PrEP coverage:       2% (-80%)
```

**Expected Detection Gaps:**
- Diagnosis rate: **COLLAPSES** to <50% by 2030
- Undiagnosed HIV+: **50-60%** of true cases
- Massive increase in missed positives
- **Epidemic reversal** expected

---

### 4. S2a_intensified_testing

Enhanced testing strategies to close First 95 gap

```yaml
Testing rate:           45% (+55%)
Index testing:          ENABLED
Self-testing:           ENABLED (500K kits/year)
Linkage to care:        90%
```

**Expected Detection Gaps:**
- Diagnosis rate: ~85-90% by 2030
- Undiagnosed HIV+: 10-15% of true cases
- **Best scenario** for closing detection gap

---

### 5. S2b_key_populations

High-intensity interventions for FSW, MSM, PWID

```yaml
KP testing:             95% (quarterly)
KP PrEP coverage:       95%
KP ART coverage:        95%
KP viral suppression:   95%
```

**Expected Detection Gaps:**
- Near-perfect detection in KP groups
- Spillover improves general population detection
- Concentrated epidemic control

---

### 6. S2c_emtct

Elimination of Mother-to-Child Transmission

```yaml
ANC coverage:           98%
PMTCT testing:          98%
PMTCT ART:              98%
Target MTCT:            <5%
```

**Expected Detection Gaps:**
- Near-universal testing in pregnant women
- High detection rate in reproductive age women
- Reduced pediatric missed cases

---

### 7. S2d_youth_focus

Youth & Adolescent (15-24) focused interventions

```yaml
Youth testing:          85%
Youth ART initiation:   90%
Youth PrEP:             40%
Youth retention:        85%
```

**Expected Detection Gaps:**
- High detection in youth (15-24)
- Lower detection in older adults
- Long-term impact on epidemic control

---

### 8. S3a_psn_aspirational

Full PSN 2024-2030 Strategic Plan implementation

```yaml
First 95:               95%
Second 95:              95%
Third 95:               95%
MTCT:                   <5%
PrEP (KP):              95%
VMMC:                   80%
```

**Expected Detection Gaps:**
- Diagnosis rate: **95%** by 2030
- Undiagnosed HIV+: **<5%** of true cases
- **Optimal scenario** for detection
- Near-complete cascade coverage

---

### 9. S3b_geographic

Regional prioritization strategy

```yaml
Priority regions:       Sud, Est, Centre (high prevalence)
Testing boost:          +30% in priority areas
Linkage boost:          +30%
Prevention boost:       +35%
Non-priority:           85% baseline
```

**Expected Detection Gaps:**
- Geographic heterogeneity in detection
- High detection in priority regions
- Lower detection in non-priority areas
- Resource allocation optimization insights

---

## Output Files Structure

### Per-Scenario Outputs

```
results/comprehensive_2070_analysis/
├── S0_baseline/
│   ├── simulation_results.csv          [Primary output - annual time series]
│   ├── metadata.json                    [Scenario configuration]
│   └── detailed_results/                [Age-sex-region stratification]
│
├── S1a_optimistic_funding/
│   └── ...
│
├── S1b_pessimistic_funding/
│   └── ...
│
... [7 more scenarios]
│
└── execution_summary.json               [Aggregate results]
```

### simulation_results.csv Columns

#### Core Tracking
- `year`: Simulation year (1985-2070)
- `total_population`: Total alive agents
- `susceptible`: HIV-negative individuals

#### TRUE HIV States
- `hiv_infections`: TRUE total HIV+ count
- `acute`: Acute infection stage
- `chronic`: Chronic infection stage
- `aids`: AIDS stage
- `new_infections`: TRUE new infections this year
- `hiv_prevalence`: TRUE prevalence rate

#### DETECTED States
- `diagnosed`: HIV+ who are diagnosed
- `undiagnosed_hiv`: **Missed HIV+ cases**
- `tested`: Ever tested
- `tested_last_12m`: Tested in last year
- `on_art`: On ART treatment
- `virally_suppressed`: Suppressed on ART

#### Coverage Metrics
- `hiv_prevalence_detected`: Detected prevalence
- `testing_coverage`: % ever tested
- `diagnosis_rate`: % of TRUE HIV+ diagnosed
- `art_coverage_true`: % of TRUE HIV+ on ART
- `art_coverage_detected`: % of diagnosed on ART
- `suppression_rate_true`: % of TRUE HIV+ suppressed
- `suppression_rate_art`: % on ART suppressed

#### Vital Statistics
- `deaths_hiv`: HIV-related deaths
- `deaths_natural`: Natural deaths
- `births`: Births

---

## Analysis Workflow

### Phase 1: Execution (3-4.5 hours)

```bash
# Run all scenarios
python scripts/run_all_scenarios.py \
  --population 100000 \
  --years 85 \
  --start-year 1985 \
  --output-dir results/comprehensive_2070_analysis
```

**Monitor progress:**
```bash
# Check log file
tail -f execution_log_2070.txt

# Check completed scenarios
ls -lh results/comprehensive_2070_analysis/
```

### Phase 2: Detection Gap Analysis

```bash
# Analyze all scenarios
python scripts/analyze_detection_gaps.py \
  --results-dir results/comprehensive_2070_analysis \
  --output-dir results/comprehensive_2070_analysis/detection_gaps
```

**Outputs:**
- Individual scenario reports (text)
- Comparative visualizations (6 plots)
- Missed cases analysis
- Testing coverage impact assessment

### Phase 3: Custom Analysis

Load results in Python:

```python
import pandas as pd

# Load baseline scenario
df = pd.read_csv('results/comprehensive_2070_analysis/S0_baseline/simulation_results.csv')

# Calculate missed cases over time
df['missed_cases'] = df['undiagnosed_hiv']
df['missed_pct'] = (df['undiagnosed_hiv'] / df['hiv_infections'] * 100)

# Plot TRUE vs DETECTED prevalence
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(df['year'], df['hiv_prevalence'] * 100, label='TRUE Prevalence', linewidth=2)
plt.plot(df['year'], df['hiv_prevalence_detected'] * 100, 
         label='DETECTED Prevalence', linestyle='--', linewidth=2)
plt.fill_between(df['year'], 
                 df['hiv_prevalence'] * 100, 
                 df['hiv_prevalence_detected'] * 100, 
                 alpha=0.3, label='Detection Gap')
plt.xlabel('Year')
plt.ylabel('HIV Prevalence (%)')
plt.title('TRUE vs DETECTED HIV Prevalence - Baseline Scenario')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('true_vs_detected_prevalence.png', dpi=300)
```

---

## Key Research Questions

### 1. Detection Gap Evolution

**Question:** How does the gap between TRUE and DETECTED prevalence change over time?

**Metrics:**
- `hiv_prevalence` - `hiv_prevalence_detected` (absolute gap)
- `undiagnosed_hiv` / `hiv_infections` × 100 (percentage gap)

**Expected Findings:**
- Gap narrows with testing scale-up (1990-2010)
- Gap widens with funding cuts (S1b scenario)
- Nearly closes in aspirational scenario (S3a)

### 2. Impact of Testing Coverage

**Question:** What testing coverage is needed to diagnose 95% of HIV+ individuals?

**Analysis:**
- Plot `diagnosis_rate` vs `testing_coverage` for all scenarios
- Identify threshold coverage for 95% diagnosis
- Calculate return on investment for testing programs

**Expected Findings:**
- Diminishing returns above ~60% testing coverage
- Targeted testing (S2a, S2b) more efficient than universal
- Need ~70-80% coverage to reach 95% diagnosis

### 3. Missed Cases by Scenario

**Question:** How many HIV+ individuals are missed under different funding scenarios?

**Analysis:**
- Compare `undiagnosed_hiv` across scenarios for 2030, 2050, 2070
- Calculate cumulative person-years undiagnosed
- Assess secondary transmission from undiagnosed

**Expected Findings:**
- Baseline: 30-40% missed by 2030
- Pessimistic: 50-60% missed (CRISIS)
- Aspirational: <5% missed (TARGET)

### 4. 95-95-95 Achievement

**Question:** Can 95-95-95 be achieved with limited testing coverage?

**Analysis:**
- Compare `art_coverage_true` vs `art_coverage_detected`
- Calculate "hidden gap" not visible to programs
- Assess whether 95-95-95 (detected) = epidemic control

**Expected Findings:**
- 95-95-95 (detected denominator) possible without universal testing
- But TRUE coverage may be only 70-80% (unseen gap)
- Need First 95 (true) for actual epidemic control

### 5. Funding Cut Impact

**Question:** What is the immediate and long-term impact of 40% funding cuts?

**Analysis:**
- Compare S0 vs S1b trajectories
- Calculate excess undiagnosed cases 2025-2070
- Estimate epidemic reversal timing

**Expected Findings:**
- Immediate collapse in diagnosis rate (95% → 50%)
- Detection gap doubles within 5 years
- Epidemic reversal visible by 2030-2035
- Long-term (2070): prevalence 2-3× higher than baseline

---

## Validation & Quality Control

### Pre-Execution Checks

✅ Model enhanced with TRUE vs DETECTED tracking  
✅ All 9 scenario definitions updated  
✅ Results dictionary includes new metrics  
✅ Analysis scripts created  
✅ Storage space available (~3 GB)

### During Execution

Monitor for:
- Scenario completion messages
- Error messages in log file
- Memory usage (should stay <24 GB)
- Disk space

### Post-Execution Validation

Check each scenario:
```bash
# Verify all scenarios completed
ls results/comprehensive_2070_analysis/ | grep "^S"

# Check file sizes (should be ~200-300 MB each)
du -sh results/comprehensive_2070_analysis/S*

# Verify CSV format
head results/comprehensive_2070_analysis/S0_baseline/simulation_results.csv
```

Validate data:
```python
import pandas as pd

df = pd.read_csv('results/comprehensive_2070_analysis/S0_baseline/simulation_results.csv')

# Check year range
assert df['year'].min() == 1985
assert df['year'].max() == 2070
assert len(df) == 86  # 86 years

# Check TRUE >= DETECTED
assert (df['hiv_infections'] >= df['diagnosed']).all()
assert (df['diagnosed'] >= df['on_art']).all()

# Check undiagnosed calculation
assert (df['undiagnosed_hiv'] == df['hiv_infections'] - df['diagnosed']).all()

print("✓ Data validation passed!")
```

---

## Expected Results Summary

### Baseline Scenario (S0) - 2070 Projections

**TRUE States:**
- HIV prevalence: ~1.5-2.0% (gradual decline continues)
- HIV+ individuals: ~24,000-30,000 (of 11.9M scaled)
- New infections: ~800-1,000/year

**DETECTED States:**
- Diagnosed: ~18,000-22,000 (70-75% of true)
- Undiagnosed: ~6,000-8,000 (**missed cases**)
- On ART: ~15,000-18,000 (60-65% of true)

**Gaps:**
- Detection gap: 25-30% of HIV+ undiagnosed
- Treatment gap: 35-40% of HIV+ not on ART
- Testing coverage: ~50-60% ever tested

### Pessimistic Scenario (S1b) - 2070 Projections ⚠️

**TRUE States:**
- HIV prevalence: ~3.5-4.5% (epidemic reversal)
- HIV+ individuals: ~55,000-70,000
- New infections: ~2,500-3,500/year

**DETECTED States:**
- Diagnosed: ~20,000-30,000 (40-50% of true)
- Undiagnosed: ~30,000-40,000 (**CRISIS - 50%+ missed**)
- On ART: ~10,000-15,000 (20-25% of true)

**Gaps:**
- Detection gap: **50-60%** of HIV+ undiagnosed
- Treatment gap: **75-80%** of HIV+ not on ART
- Testing coverage: ~30-40% ever tested

### Aspirational Scenario (S3a) - 2070 Projections ✅

**TRUE States:**
- HIV prevalence: ~0.3-0.5% (near-elimination)
- HIV+ individuals: ~5,000-8,000
- New infections: ~100-200/year

**DETECTED States:**
- Diagnosed: ~4,800-7,600 (95%+ of true)
- Undiagnosed: ~200-400 (**<5% missed**)
- On ART: ~4,500-7,000 (90%+ of true)

**Gaps:**
- Detection gap: **<5%** of HIV+ undiagnosed
- Treatment gap: **<10%** of HIV+ not on ART
- Testing coverage: ~80-90% ever tested

---

## Citation & Usage

### How to Cite This Analysis

```
HIVEC-CM Model (2025). Comprehensive Policy Scenario Analysis (1985-2070):
TRUE vs DETECTED States Differentiation for Detection Gap Assessment.
Cameroon HIV Epidemic Model, Version 7.0 (Time-Varying Calibrated).
100,000-agent simulation, 9 scenarios.
```

### Data Availability

All simulation results will be available at:
```
results/comprehensive_2070_analysis/
```

Processed analysis outputs:
```
results/comprehensive_2070_analysis/detection_gaps/
```

### Code Availability

Scenario runner:
```
scripts/run_all_scenarios.py
```

Detection gap analyzer:
```
scripts/analyze_detection_gaps.py
```

Model core with TRUE/DETECTED tracking:
```
src/hivec_cm/models/model.py (Lines 750-900)
```

---

## Troubleshooting

### Common Issues

#### 1. Memory Error
```
MemoryError: Unable to allocate array
```

**Solution:** Reduce population to 50,000 or run scenarios individually

#### 2. Slow Execution
```
Scenario taking >45 minutes
```

**Solution:** Check CPU usage, close other applications, reduce time step to 0.2

#### 3. Missing Columns in Output
```
KeyError: 'undiagnosed_hiv'
```

**Solution:** Verify model.py was updated with enhanced tracking, re-run simulation

---

## Next Steps

After this execution completes:

### Immediate (Day 1)
1. ✅ Run detection gap analysis
2. Generate summary visualizations
3. Create policy brief highlighting missed cases
4. Identify optimal testing strategy

### Short-term (Week 1)
1. Detailed scenario comparison analysis
2. Cost-effectiveness of testing coverage
3. Sensitivity analysis on detection parameters
4. Regional heterogeneity analysis

### Medium-term (Month 1)
1. Monte Carlo robustness testing
2. Bayesian calibration with detection data
3. Machine learning for detection optimization
4. Manuscript: "The Hidden Epidemic: Quantifying Undiagnosed HIV in Cameroon"

---

## Contact

**Model:** HIVEC-CM Version 7.0 (Time-Varying Calibrated)  
**Execution:** Comprehensive 1985-2070 Analysis  
**Date:** October 26, 2025  
**Analyst:** Blake Nkemngu  

**Documentation:**
- Calibration: TIME_VARYING_FINAL_REPORT.md
- Model architecture: docs/09_technical/
- Scenario definitions: src/hivec_cm/scenarios/scenario_definitions.py

---

**Status:** ⏳ EXECUTION IN PROGRESS (3-4.5 hours estimated)  
**Check:** `tail -f execution_log_2070.txt`
