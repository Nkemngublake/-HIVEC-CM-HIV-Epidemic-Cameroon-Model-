# Quick Reference: Parameter Merge Strategy

## The Core Principle

**MERGE**: Anything about **policy, programs, or historical data**  
**KEEP SEPARATE**: Anything about **biology, disease mechanics, or transmission**

---

## What Goes Where

### 📊 Unified Parameters File (`config/parameters_v4_calibrated.json`)

**Historical Calibration Data:**
- Birth rates (World Bank 1960-2023) ✅
- Death rates by year ✅
- HIV prevalence targets (UNAIDS 1990-2022) ✅
- CAMPHIA 2017 survey data ✅

**Program Coverage Time Series:**
- Condom distribution (1985-2024) ✅
- HIV testing scale-up (1985-2024) ✅
- ART program rollout (2004-2024) ✅
- PMTCT coverage (1990-2024) ✅

**Scenario Modifications:**
- Baseline/Optimistic/Pessimistic funding ✅
- Policy parameter targets ✅
- Funding multipliers ✅

### 🔬 Separate Disease Parameters (`src/hivec_cm/core/disease_parameters.py`)

**Viral Load & Progression:**
- Acute phase dynamics ❌ (keep separate)
- Chronic progression rates ❌
- AIDS threshold ❌

**Transmission:**
- Per-act transmission probability ❌
- Viral load effect on infectivity ❌
- Contact patterns ❌

**Treatment Effects:**
- ART viral suppression dynamics ❌
- Mortality reduction by VL ❌
- MTCT base rates (biological) ❌

---

## The Bridge: ParameterMapper Class

```python
# src/hivec_cm/calibration/parameter_mapper.py

class ParameterMapper:
    """
    Translates scenario parameters into model behavior.
    Uses historical calibration before 2024.
    Applies scenario modifications after 2024.
    """
    
    def get_condom_coverage(self, year):
        if year < 2024:
            return historical_calibration[year]
        else:
            return scenario_modified_value
```

**This class connects:**
- Scenario definitions → Model behavior
- Historical data → Pre-2024 simulation
- Policy parameters → Future projections

---

## File Structure

```
config/
└── parameters_v4_calibrated.json    # All policy & historical data

src/hivec_cm/
├── core/
│   └── disease_parameters.py        # Biological constants
├── calibration/
│   └── parameter_mapper.py          # Bridge scenarios to model
└── scenarios/
    └── scenario_definitions.py       # Policy scenarios
```

---

## Implementation Checklist

- [ ] Consolidate calibration data into parameters_v4_calibrated.json
- [ ] Create ParameterMapper class
- [ ] Move disease parameters to separate file
- [ ] Refactor model.py to use mapper for policy parameters
- [ ] Validate against UNAIDS targets (1990-2022)
- [ ] Test scenario differentiation (>10% difference in outcomes)

---

## Key Insight

**The model currently has hardcoded time-dependent curves for policy parameters.**

These should be:
1. Extracted to parameters.json (with sources/citations)
2. Accessed via ParameterMapper
3. Modified by scenarios for future years only

**Disease progression and transmission mechanics stay in code** - they're scientific constants, not policy variables.

---

See `CALIBRATION_MERGE_PROMPT.md` for complete implementation details.
