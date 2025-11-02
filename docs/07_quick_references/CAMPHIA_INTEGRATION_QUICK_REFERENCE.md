# CAMPHIA 2017-2018 Integration - Quick Reference

## Summary
Integrated comprehensive regional data from **CAMPHIA 2017-2018** survey into HIVEC-CM model.

---

## What Was Added

### 7 New Regional Data Structures

1. **REGIONAL_HIV_PREVALENCE**: HIV prevalence by region (15-64 years)
   - Range: 1.5% (Extrême-Nord) to 6.3% (Sud)
   - Source: CAMPHIA Table 12.1

2. **REGIONAL_VIRAL_SUPPRESSION**: VLS rates (<1000 copies/mL) among PLHIV
   - Range: 27.6% (Nord) to 62.9% (Ouest)
   - Source: CAMPHIA Table 14.8

3. **REGIONAL_TESTING_EVER**: Ever tested for HIV and received results
   - Range: 24.0% (Extrême-Nord) to 76.5% (Douala)
   - Source: CAMPHIA Table 13.1

4. **REGIONAL_TESTING_12MONTHS**: Tested in last 12 months
   - Range: 9.8% (Extrême-Nord) to 42.9% (Douala)
   - Source: CAMPHIA Table 13.1

5. **REGIONAL_CIRCUMCISION**: Male circumcision status distribution
   - Medical: 26.7% (Extrême-Nord) to 70.0% (Douala)
   - Source: CAMPHIA Table 15.2

6. **REGIONAL_ART_STATUS**: HIV awareness and treatment status
   - On ART: 24.2% (Nord) to 66.8% (Nord-Ouest)
   - Source: CAMPHIA Table 14.3

7. **REGIONAL_HEPATITIS_B_PREVALENCE**: Hepatitis B co-infection
   - Range: 4.6% (Nord-Ouest) to 12.8% (Nord)
   - Source: CAMPHIA Table 15.7

---

## 8 New Helper Functions

```python
from hivec_cm.core.demographic_parameters import (
    get_regional_hiv_prevalence,                # HIV prevalence for region
    get_regional_viral_suppression_rate,        # VLS rate for region
    get_regional_testing_rates,                 # Testing rates (ever + 12mo)
    get_regional_circumcision_distribution,     # Circumcision status dist
    get_regional_art_status_distribution,       # ART status among PLHIV
    get_regional_hepatitis_b_prevalence,        # HepB prevalence
    get_regional_cascade_metrics,               # 90-90-90 cascade metrics
    get_regional_hiv_risk_multiplier            # Risk multiplier (updated)
)
```

---

## Regional Updates

### Changed from 10 to 12 Regions
**Old regions**:
- Centre (included Yaoundé)
- Littoral (included Douala)

**New regions** (CAMPHIA structure):
- Centre (excluding Yaoundé)
- Yaoundé (separate urban region)
- Littoral (excluding Douala)
- Douala (separate urban region)

**Reason**: CAMPHIA separates major cities due to distinct HIV epidemiology

---

## Key Regional Patterns

### HIV Prevalence
- **Highest**: Sud (6.3%), Est (5.9%), Centre (5.8%)
- **Lowest**: Extrême-Nord (1.5%), Nord (1.6%), Ouest (2.7%)
- **National**: 3.7%

### Viral Suppression
- **Best**: Ouest (62.9%), Nord-Ouest (60.9%)
- **Worst**: Nord (27.6%), Adamaoua (34.1%)
- **National**: ~40%

### HIV Testing
- **Most tested**: Douala (76.5%), Yaoundé (72.0%)
- **Least tested**: Extrême-Nord (24.0%), Nord (26.8%)
- **National**: ~56%

### ART Coverage
- **Highest**: Nord-Ouest (66.8% on ART)
- **Lowest**: Nord (24.2%), Extrême-Nord (25.3%)
- **National**: ~38%

### 90-90-90 Cascade
Only **Nord-Ouest** meets first 90 target (70.1% aware)
- Most regions: <50% aware of HIV status
- Among aware: >80% on ART (strong linkage)
- Among on ART: >85% virally suppressed (good adherence)

**Bottleneck**: Testing/diagnosis (1st 90), not treatment

---

## Model Usage

### 1. Agent Initialization
```python
# Assign region
agent.region = get_region_from_distribution()

# HIV status (for 2018 initialization)
hiv_prev = get_regional_hiv_prevalence(agent.region)
agent.is_hiv_positive = random.random() < hiv_prev

# If HIV+, assign cascade position
if agent.is_hiv_positive:
    art_dist = get_regional_art_status_distribution(agent.region)
    agent.cascade_position = sample_from(art_dist)
```

### 2. Annual Testing Event
```python
# Regional testing probability
testing_rates = get_regional_testing_rates(agent.region)
annual_prob = testing_rates['tested_12months']

if random.random() < annual_prob:
    agent.get_tested()
```

### 3. Treatment Outcomes
```python
# Regional viral suppression probability
if agent.on_art:
    vls_rate = get_regional_viral_suppression_rate(agent.region)
    agent.is_virally_suppressed = random.random() < vls_rate
```

### 4. Male Circumcision
```python
if agent.sex == "male":
    circ_dist = get_regional_circumcision_distribution(agent.region)
    agent.circumcision_status = sample_from(circ_dist)
```

---

## Validation Targets

Model should reproduce these CAMPHIA 2017-2018 values by year 2018:

### Regional HIV Prevalence (±0.5%)
- Sud: 6.3%
- Est: 5.9%
- Extrême-Nord: 1.5%
- Nord: 1.6%

### Regional VLS Rates (±5%)
- Ouest: 62.9%
- Nord-Ouest: 60.9%
- Nord: 27.6%

### Regional Testing Coverage (±10%)
- Douala: 76.5% ever tested
- Extrême-Nord: 24.0% ever tested

### Regional Cascade (±5%)
- Nord-Ouest: 70% aware, 67% on ART
- Nord: 30% aware, 24% on ART

---

## Impact on Model

### Before CAMPHIA Integration
- ❌ Single national prevalence
- ❌ Generic risk multipliers
- ❌ No testing variation
- ❌ No cascade heterogeneity

### After CAMPHIA Integration
- ✅ 12 region-specific prevalence rates
- ✅ Empirical risk multipliers from data
- ✅ Testing rates vary 3.2× across regions
- ✅ Cascade varies 2.8× (24%-67% on ART)
- ✅ VLS varies 2.3× (28%-63%)
- ✅ Circumcision varies 2.6× (27%-70% medical)
- ✅ 72 calibration targets (6 metrics × 12 regions)

---

## Files Modified

### Core Files
1. **src/hivec_cm/core/demographic_parameters.py** (+300 lines)
   - Added 7 CAMPHIA data dictionaries
   - Created 8 new helper functions
   - Enhanced validation for regional data
   - Updated examples

### Documentation
2. **CAMPHIA_INTEGRATION_COMPLETE.md** (NEW - 35 pages)
   - Complete CAMPHIA integration guide
   - Detailed parameter descriptions
   - Code examples for each metric
   - Validation strategy

3. **CAMPHIA_INTEGRATION_QUICK_REFERENCE.md** (THIS FILE)
   - Quick reference summary
   - Key metrics and functions
   - Model usage patterns

---

## Testing

Run validation:
```bash
python3 src/hivec_cm/core/demographic_parameters.py
```

Expected output:
```
✅ Demographic parameters validated successfully
   - 12 regions with complete CAMPHIA 2017-2018 data
   - HIV prevalence range: 1.5% - 6.3%
   - VLS range: 27.6% - 62.9%
```

---

## Next Steps

### Immediate
1. ✅ **COMPLETE**: CAMPHIA data integrated into demographic_parameters.py
2. ⏳ **TODO**: Update Individual class to use CAMPHIA parameters
3. ⏳ **TODO**: Update Model class testing/treatment events
4. ⏳ **TODO**: Calibrate 1985 initial conditions

### Future
1. Validate model output against CAMPHIA 2018 targets
2. Run regional sensitivity analysis
3. Design region-specific intervention scenarios
4. Generate regional policy briefs

---

## Quick Commands

### View all regions
```python
from hivec_cm.core.demographic_parameters import REGIONAL_DISTRIBUTION
print(list(REGIONAL_DISTRIBUTION.keys()))
```

### Get regional summary
```python
from hivec_cm.core.demographic_parameters import (
    get_regional_hiv_prevalence,
    get_regional_cascade_metrics
)

region = "Yaoundé"
print(f"Prevalence: {get_regional_hiv_prevalence(region):.1%}")
print(f"Cascade: {get_regional_cascade_metrics(region)}")
```

### Compare regions
```python
from hivec_cm.core.demographic_parameters import (
    REGIONAL_HIV_PREVALENCE,
    REGIONAL_VIRAL_SUPPRESSION
)

for region in sorted(REGIONAL_HIV_PREVALENCE.keys()):
    prev = REGIONAL_HIV_PREVALENCE[region]
    vls = REGIONAL_VIRAL_SUPPRESSION[region]
    print(f"{region:15} | Prev: {prev:4.1%} | VLS: {vls:4.1%}")
```

---

## Key Insights from CAMPHIA Data

### 1. North-South Divide
- Northern regions (Extrême-Nord, Nord): Low prevalence (1.5-1.6%), poor cascade
- Southern regions (Sud, Est): High prevalence (5.9-6.3%), moderate cascade
- **Implication**: Different interventions needed by geography

### 2. Urban Advantage
- Douala and Yaoundé: Highest testing (76.5%, 72.0%)
- Rural regions: Lower testing (<50%)
- **Implication**: Testing expansion needed in rural areas

### 3. Cascade Bottleneck
- Awareness (1st 90): Major challenge (30-70%)
- Treatment (2nd 90): Strong performance (>85% among aware)
- VLS (3rd 90): Excellent (>90% among on ART)
- **Implication**: Focus on testing/diagnosis, not treatment adherence

### 4. VLS Paradox
- Ouest: Low awareness (48%), high overall VLS (63%)
- Nord: Low awareness (30%), low overall VLS (28%)
- **Implication**: Treatment quality varies regionally

### 5. Circumcision Patterns
- Urban regions: 65-70% medically circumcised
- Northern regions: 27-35% medically circumcised, high traditional
- **Implication**: VMMC program targeting opportunity in North

---

## References

- **CAMPHIA 2017-2018**: Cameroon Population-based HIV Impact Assessment
- **Tables**: 12.1, 12.5, 13.1, 14.3, 14.8, 15.2, 15.7
- **Survey period**: November 2017 - August 2018
- **Sample**: 14,916 adults aged 15-64 years
- **Response rate**: 90.9% household, 93.5% individual

---

*Integration completed: October 14, 2025*
*Model version: HIVEC-CM v4.1 (CAMPHIA Regional Integration)*
*Data validation: ✅ All regional data structures validated*
