# Saint Seya Detailed Simulation - Data Collection Specification

**Date:** November 2, 2025  
**Simulation:** Saint Seya Detailed (Rerun with comprehensive data capture)  
**Output:** `results/Saint_Seya_Simulation_Detailed/`

## Overview

This is a complete rerun of the Saint Seya simulation with **enhanced data collection** to capture ALL stratified results that the model generates but were not previously saved.

## Configuration

- **Time Period:** 1985-2070 (85 years)
- **Population:** 10,000 agents
- **Scenarios:** All 9 policy scenarios
- **Data Collection:** COMPREHENSIVE (all detailed results)

## Detailed Data Being Captured

### 1. **Age-Sex Stratification**
Location: `detailed_results.json` + `detailed_age_sex_results.csv`

**Age Groups:**
- 0-14 years (children)
- 15-24 years (youth)
- 25-49 years (adults)
- 50+ years (older adults)

**By Sex:**
- Male
- Female

**Metrics:**
- HIV prevalence by age-sex group
- HIV incidence by age-sex group
- Population distribution
- New infections by group

### 2. **Regional Stratification**
Location: `detailed_results.json` + `detailed_age_sex_results.csv`

**10 Regions of Cameroon:**
- Adamaoua
- Centre
- Est
- Extrême-Nord
- Littoral
- Nord
- Nord-Ouest
- Ouest
- Sud
- Sud-Ouest

**For Each Region:**
- HIV prevalence by age-sex group
- Population distribution
- Treatment coverage
- Testing rates

### 3. **Settlement Type Stratification**
Location: `detailed_results.json`

**Settlement Types:**
- Urban
- Rural

**Metrics:**
- HIV prevalence by settlement type
- Access to services
- Testing coverage
- ART coverage

### 4. **Key Population Data**
Location: `detailed_results.json`

**Key Populations:**
- Female Sex Workers (FSW)
- Men who have Sex with Men (MSM)
- People Who Inject Drugs (PWID)
- General Population

**Metrics:**
- Population sizes
- HIV prevalence
- Service coverage
- PrEP uptake

### 5. **Treatment Cascade Data**
Location: `simulation_results.csv` + `detailed_results.json`

**Cascade Stages:**
- Total PLHIV
- Diagnosed (know their status)
- Linked to care
- On ART
- Virally suppressed

**Coverage Metrics:**
- Diagnosis coverage (90% target)
- Treatment coverage (95% target)
- Viral suppression (95% target)
- 90-90-90 and 95-95-95 progress

### 6. **Testing & Diagnosis Data**
Location: `simulation_results.csv` + `detailed_results.json`

**Testing Metrics:**
- Tests performed per year
- Positivity rate
- Testing coverage achieved
- Undiagnosed PLHIV count
- Missed diagnoses

**By Group:**
- General population
- Key populations
- Pregnant women (PMTCT)
- Youth

### 7. **Mother-to-Child Transmission (MTCT)**
Location: `detailed_results.json`

**Metrics:**
- HIV+ pregnant women
- Women on ART during pregnancy
- PMTCT coverage
- Infant infections prevented
- MTCT rate

### 8. **Mortality Data**
Location: `simulation_results.csv`

**Deaths:**
- HIV-related deaths (by year)
- Natural deaths
- Deaths by age group
- Deaths by disease stage (acute, chronic, AIDS)

### 9. **Demographic Data**
Location: `simulation_results.csv`

**Population Dynamics:**
- Total population by year
- Births
- Deaths (HIV + natural)
- Population growth rate
- Age structure evolution

### 10. **Disease Progression Data**
Location: `simulation_results.csv` + `detailed_results.json`

**HIV Stages:**
- Susceptible
- Acute infection
- Chronic infection
- AIDS stage

**Progression Tracking:**
- Time to diagnosis
- Time to treatment initiation
- Disease stage at diagnosis

## File Structure

```
results/Saint_Seya_Simulation_Detailed/
├── S0_baseline/
│   ├── simulation_results.csv           # Annual aggregate data
│   ├── detailed_results.json            # Complete stratified data (all dimensions)
│   ├── detailed_age_sex_results.csv    # Flattened age-sex-region data
│   └── metadata.json                    # Scenario configuration
├── S1a_optimistic_funding/
│   └── (same file structure)
├── S1b_pessimistic_funding/
│   └── (same file structure)
... (all 9 scenarios)
```

## Data Formats

### simulation_results.csv
Standard time series with ~28 columns:
- year, total_population, susceptible
- true_hiv_positive, true_prevalence
- detected_hiv_positive, diagnosed
- true_on_art, true_virally_suppressed
- true_art_coverage, detected_art_coverage
- deaths_hiv, deaths_natural, births
- testing metrics, diagnosis metrics

### detailed_results.json
Nested JSON with full stratification:
```json
{
  "1985": {
    "age_sex_prevalence": {
      "0-14": {"male": 0.001, "female": 0.001},
      "15-24": {"male": 0.025, "female": 0.035},
      ...
    },
    "regional_age_sex_prevalence": {
      "Centre": {
        "15-24": {"male": 0.028, "female": 0.038},
        ...
      },
      ...
    },
    "settlement_prevalence": {"urban": 0.045, "rural": 0.025},
    "key_population_data": {...},
    "treatment_cascade": {...},
    "mtct_data": {...}
  },
  "1986": {...},
  ...
}
```

### detailed_age_sex_results.csv
Flattened long format for easy analysis:
```csv
year,type,age_group,sex,region,value
1985,prevalence,15-24,male,,0.025
1985,prevalence,15-24,female,,0.035
1985,regional_prevalence,15-24,male,Centre,0.028
...
```

## Data Size Estimates

- **simulation_results.csv:** ~10 KB per scenario (86 rows)
- **detailed_results.json:** ~500 KB - 2 MB per scenario (full nested data)
- **detailed_age_sex_results.csv:** ~200-500 KB per scenario (flattened format)
- **Total per scenario:** ~1-3 MB
- **Total all 9 scenarios:** ~10-30 MB

## What's Different from Previous Run

### Previous Run (Saint_Seya_Simulation):
❌ Only saved `simulation_results.csv` (aggregate data)  
❌ No age-sex stratification saved  
❌ No regional breakdown saved  
❌ No settlement type data saved  
❌ Model collected the data but didn't save it

### Current Run (Saint_Seya_Simulation_Detailed):
✅ Saves ALL data model collects  
✅ Age-sex stratification (4 age groups × 2 sexes)  
✅ Regional stratification (10 regions × age × sex)  
✅ Settlement type data (urban/rural)  
✅ Key population breakdowns  
✅ Complete treatment cascade  
✅ MTCT detailed metrics  
✅ Multiple output formats (JSON + CSV)

## Use Cases for Detailed Data

### 1. Age-Targeted Interventions
Analyze which age groups have highest burden:
```python
df = pd.read_csv("detailed_age_sex_results.csv")
youth = df[(df.age_group == "15-24") & (df.type == "prevalence")]
```

### 2. Regional Prioritization
Identify high-burden regions:
```python
regional = df[df.type == "regional_prevalence"]
high_burden = regional.groupby("region")["value"].mean().sort_values()
```

### 3. Gender Analysis
Compare male vs female epidemic:
```python
gender_gap = df.pivot_table(values="value", index="year", 
                            columns="sex", aggfunc="mean")
```

### 4. Urban-Rural Disparities
Settlement-based analysis from JSON data

### 5. Key Population Targeting
FSW, MSM, PWID specific interventions

## Expected Completion

- **Started:** ~3:30 AM
- **Per Scenario:** ~2 minutes
- **Total Time:** ~18 minutes
- **Expected Done:** ~3:48 AM

## Monitoring

**Live Monitor:**
```bash
python scripts/monitor_saint_seya.py --output-dir results/Saint_Seya_Simulation_Detailed
```

**Check Progress:**
```bash
ls -la results/Saint_Seya_Simulation_Detailed/*/detailed_results.json
```

**View Log:**
```bash
tail -f saint_seya_detailed_simulation.log
```

---

**Status:** 🔄 Currently Running  
**Monitor Active:** Yes  
**Detailed Data Collection:** ENABLED ✅
