# Executive Summary: Parameter Merge Proposal for HIVEC-CM

**Date**: January 9, 2025  
**Model**: HIVEC-CM (HIV Epidemic Cameroon Model)  
**Issue**: Parameter organization and scenario integration

---

## Problem Statement

The HIVEC-CM model currently has:
1. **Hardcoded time-dependent curves** in model logic (condom use, testing rates, ART scale-up)
2. **Scenario parameters** defined but requiring better integration
3. **Calibration data** scattered across multiple files
4. **No clear separation** between policy parameters and disease biology

---

## Proposed Solution

### Create a Three-Tier Parameter Architecture:

```
1️⃣  UNIFIED CALIBRATION FILE
    → config/parameters_v4_calibrated.json
    → Contains: Historical data, program coverage, scenario modifications
    
2️⃣  PARAMETER MAPPER CLASS
    → src/hivec_cm/calibration/parameter_mapper.py
    → Bridges: Scenario definitions ↔ Model behavior
    
3️⃣  SEPARATE DISEASE PARAMETERS
    → src/hivec_cm/core/disease_parameters.py
    → Contains: Viral load progression, transmission mechanics
```

---

## Key Principle

### **MERGE** (Policy & History)
- Historical demographic data
- Program coverage timelines
- Calibration targets
- Scenario policy parameters

### **KEEP SEPARATE** (Biology & Mechanics)
- Viral load progression
- Transmission probabilities
- Disease natural history
- Treatment biological effects

---

## What Gets Merged

### Into `parameters_v4_calibrated.json`:

**Historical Calibration:**
- ✅ Birth/death rates (World Bank 1960-2023)
- ✅ HIV prevalence targets (UNAIDS 1990-2022)
- ✅ CAMPHIA survey indicators (2017)
- ✅ Population demographics

**Program Timelines:**
- ✅ Condom distribution scale-up (1985-2024)
- ✅ HIV testing expansion (1985-2024)
- ✅ ART program rollout (2004-2024)
- ✅ PMTCT coverage (1990-2024)

**Scenario Modifications:**
- ✅ Funding multipliers
- ✅ Policy targets (testing, ART, prevention)
- ✅ Coverage adjustments

---

## What Stays Separate

### In `disease_parameters.py`:

**Disease Biology:**
- ❌ Viral load progression curves
- ❌ Disease stage definitions
- ❌ Acute/chronic/AIDS thresholds

**Transmission:**
- ❌ Per-act transmission probability
- ❌ Viral load effect on infectivity
- ❌ Contact patterns

**Treatment Effects:**
- ❌ ART viral suppression dynamics
- ❌ Mortality reduction by viral load
- ❌ MTCT base rates (biological)

---

## The Bridge: ParameterMapper

**Purpose**: Translate scenario parameters into model behavior

**Key Functions:**
- `get_condom_coverage(year)` → Returns historical calibration pre-2024, scenario-specific post-2024
- `get_testing_rate(year)` → Smooth transition from history to scenario targets
- `get_art_initiation_rate(year)` → Policy-driven treatment access
- `apply_funding_multiplier(value, category)` → Scale parameters by funding level

**Result**: Model uses one interface for all policy parameters, scenarios automatically apply

---

## Implementation Roadmap

### Phase 1: Consolidate (1 day)
- [ ] Merge all calibration data into parameters_v4_calibrated.json
- [ ] Document sources and time periods
- [ ] Add UNAIDS/CAMPHIA targets

### Phase 2: Create Mapper (1 day)
- [ ] Implement ParameterMapper class
- [ ] Handle historical → scenario transitions
- [ ] Add funding multiplier logic

### Phase 3: Refactor Model (1 day)
- [ ] Replace hardcoded curves with mapper calls
- [ ] Move disease parameters to separate file
- [ ] Update all parameter references

### Phase 4: Validate (1 day)
- [ ] Test 1985-2022 matches UNAIDS targets
- [ ] Verify scenarios produce different results
- [ ] Run full Monte Carlo validation

**Total Estimated Time: 4 days**

---

## Expected Benefits

### ✅ **Maintainability**
- One source of truth for parameters
- Clear documentation of sources
- Easy to update calibration data

### ✅ **Scenario Flexibility**
- Easy to add new scenarios
- Clear policy → model behavior mapping
- Funding effects properly distributed

### ✅ **Scientific Validity**
- Disease mechanics preserved
- Calibration to historical data
- Separation of policy vs biology

### ✅ **Transparency**
- Parameter sources documented
- Changes tracked in version control
- Reproducible results

---

## Risk Mitigation

### Risk: Breaking existing functionality
**Mitigation**: 
- Keep old code as fallback
- Comprehensive testing before/after
- Staged rollout

### Risk: Parameter mismatch
**Mitigation**:
- Validation against UNAIDS targets
- Scenario differentiation tests
- Monte Carlo reproducibility checks

### Risk: Complexity increase
**Mitigation**:
- Clear documentation
- Simple interfaces (ParameterMapper)
- Examples and tutorials

---

## Success Criteria

✅ **Calibration Accuracy**: Model matches UNAIDS prevalence 1990-2022 within 15%  
✅ **Scenario Differentiation**: Funding scenarios produce >10% difference in 2030+ outcomes  
✅ **Code Quality**: All tests pass, documentation complete  
✅ **Reproducibility**: Monte Carlo runs complete successfully with consistent results

---

## Deliverables

1. **parameters_v4_calibrated.json** - Unified parameter file with sources
2. **ParameterMapper class** - Bridge between scenarios and model
3. **disease_parameters.py** - Separated biological constants
4. **Refactored model.py** - Uses mapper for policy parameters
5. **Validation report** - Demonstrates calibration accuracy
6. **Documentation** - Architecture guide and examples

---

## Recommendation

**PROCEED** with parameter merge using proposed architecture.

**Rationale**:
- Clear separation of concerns (policy vs biology)
- Preserves model scientific validity
- Enables better scenario analysis
- Improves long-term maintainability
- Low risk with proper testing

**Next Step**: Review `CALIBRATION_MERGE_PROMPT.md` for detailed implementation instructions.

---

## Documentation Files Created

1. **CALIBRATION_MERGE_PROMPT.md** - Complete implementation guide (7500+ words)
2. **PARAMETER_MERGE_QUICKREF.md** - Quick reference checklist
3. **PARAMETER_ARCHITECTURE.md** - Visual architecture diagrams
4. **This file** - Executive summary for decision-making

---

**Contact**: Ready to implement when approved. Estimated 4-day effort with minimal risk.
