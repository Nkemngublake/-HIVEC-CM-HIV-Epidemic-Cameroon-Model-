# HIVEC-CM Parameter Architecture: Merge vs Separate

## Visual Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HIVEC-CM PARAMETER SYSTEM                         │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐  ┌──────────────────────────────┐
│   MERGE THESE (Policy/History)   │  │  KEEP SEPARATE (Biology)     │
│   ✅ Calibration & Scenarios     │  │  ❌ Disease Mechanics        │
└──────────────────────────────────┘  └──────────────────────────────┘
                │                                    │
                │                                    │
                ▼                                    ▼
┌───────────────────────────────────┐  ┌──────────────────────────────┐
│ config/parameters_v4.json         │  │ src/core/disease_params.py   │
│                                   │  │                              │
│ • Birth/death rates (WB)          │  │ • Viral load progression     │
│ • HIV prevalence (UNAIDS)         │  │ • Transmission probability   │
│ • CAMPHIA cascade data            │  │ • Disease stages             │
│ • Condom coverage timeline        │  │ • ART viral suppression      │
│ • Testing scale-up curve          │  │ • MTCT base rates            │
│ • ART rollout (2004+)             │  │ • Mortality by VL            │
│ • PMTCT program history           │  │                              │
│ • Scenario modifications          │  │ (Scientific constants)       │
│                                   │  │                              │
│ (Historical + Policy data)        │  │                              │
└───────────────┬───────────────────┘  └────────────┬─────────────────┘
                │                                    │
                │                                    │
                └──────────┬───────────────────────┬─┘
                           │                       │
                           ▼                       ▼
              ┌────────────────────────────────────────┐
              │   src/calibration/parameter_mapper.py  │
              │                                        │
              │   ParameterMapper (Bridge Class)       │
              │   • Loads calibrated history           │
              │   • Applies scenario modifications     │
              │   • Smooth transition at 2024          │
              │   • Provides year-specific values      │
              └────────────┬───────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │   src/models/model.py      │
              │                            │
              │   HIVEC-CM Agent Model     │
              │   • Uses mapper for policy │
              │   • Uses disease_params    │
              │     for biology            │
              └────────────────────────────┘
```

## Data Flow Example: Year 2030

### Policy Parameter (Condom Coverage)
```
parameters_v4.json:
  condom_coverage:
    historical: {1985-2024}
    scenarios:
      optimistic: 0.75
      pessimistic: 0.50
             ↓
parameter_mapper.get_condom_coverage(2030):
  if scenario == optimistic:
    return smooth_transition(0.65 → 0.75)
             ↓
model.py:
  condom_rate = self.mapper.get_condom_coverage(year)
  # Uses scenario-specific value
```

### Disease Parameter (Transmission Probability)
```
disease_parameters.py:
  TRANSMISSION_PROB = {
    'base': 0.0008,
    'vl_effect': {...}
  }
             ↓
model.py:
  trans_prob = self.disease_params.calculate_transmission(
    viral_load=person.vl,
    protection=condom_used
  )
  # Uses scientific constant, independent of scenarios
```

## Decision Tree: Where Does This Parameter Go?

```
Parameter to classify
        │
        ▼
    ┌───────────────────────────────────┐
    │ Does it change with policy?       │
    │ (funding, programs, interventions)│
    └─────────┬──────────────┬──────────┘
              │              │
          YES │              │ NO
              │              │
              ▼              ▼
    ┌──────────────┐  ┌─────────────────┐
    │   MERGE      │  │  Is it about    │
    │   INTO       │  │  disease/biology?│
    │   UNIFIED    │  └────┬───────┬────┘
    │   PARAMS     │       │       │
    └──────────────┘   YES │       │ NO
                           │       │
                           ▼       ▼
                    ┌──────────┐ ┌──────────┐
                    │  KEEP    │ │  MERGE   │
                    │ SEPARATE │ │   INTO   │
                    │  (CORE)  │ │  PARAMS  │
                    └──────────┘ └──────────┘
```

## Examples by Category

### Category 1: Historical Calibration → MERGE
```
✅ Birth rates (World Bank)
✅ Death rates (WHO)
✅ HIV prevalence targets (UNAIDS)
✅ Cascade indicators (CAMPHIA)
✅ Population demographics
```

### Category 2: Program Coverage → MERGE
```
✅ Condom distribution timeline
✅ Testing rate scale-up
✅ ART program rollout
✅ PMTCT coverage expansion
✅ Prevention program reach
```

### Category 3: Scenario Policies → MERGE
```
✅ Funding multipliers
✅ Testing rate targets
✅ ART initiation goals
✅ Prevention coverage targets
✅ Treatment interruption rates
```

### Category 4: Disease Biology → SEPARATE
```
❌ Viral load progression curves
❌ Transmission probability formulas
❌ Disease stage definitions
❌ Mortality by CD4/VL
❌ Acute/chronic/AIDS thresholds
```

### Category 5: Treatment Effects → SEPARATE
```
❌ ART viral suppression dynamics
❌ Time to viral suppression
❌ Mortality reduction by VL
❌ MTCT base rates (biological)
❌ Transmission reduction by VL
```

### Category 6: Network/Mixing → SEPARATE
```
❌ Sexual contact patterns
❌ Partnership formation rules
❌ Age/sex mixing preferences
❌ Concurrency probabilities
```

## The Key Test

**Ask yourself**: "If I change this parameter, am I..."

1. **Modeling a different policy/intervention?** → MERGE
2. **Changing historical calibration data?** → MERGE
3. **Altering how HIV biology works?** → SEPARATE
4. **Modifying transmission mechanics?** → SEPARATE

## Common Mistakes to Avoid

❌ **WRONG**: Put transmission probability in scenario parameters
   - This is biology, not policy
   - Transmission probability is scientific constant
   
✅ **RIGHT**: Put condom distribution coverage in scenario parameters
   - This IS a policy intervention
   - Coverage changes with funding/programs

❌ **WRONG**: Make viral load progression scenario-dependent
   - Disease progression is biological
   - Doesn't change with policy
   
✅ **RIGHT**: Make ART initiation rate scenario-dependent
   - Access to treatment IS policy
   - Changes with funding/programs

❌ **WRONG**: Scenario affects base MTCT rate (biology)
   
✅ **RIGHT**: Scenario affects PMTCT coverage (policy)

## Summary Table

| Parameter Type | Location | Reason |
|----------------|----------|--------|
| Birth rates | parameters_v4.json | Historical data |
| HIV prevalence targets | parameters_v4.json | Calibration |
| Condom coverage | parameters_v4.json | Policy/program |
| Testing rates | parameters_v4.json | Policy/program |
| ART scale-up | parameters_v4.json | Policy/program |
| Funding multiplier | scenario_definitions.py | Policy |
| Viral load progression | disease_parameters.py | Biology |
| Transmission probability | disease_parameters.py | Biology |
| Disease stages | disease_parameters.py | Biology |
| ART suppression dynamics | disease_parameters.py | Biology |
| MTCT base rate | disease_parameters.py | Biology |

## Final Principle

```
┌─────────────────────────────────────────────┐
│  IF IT'S ABOUT WHAT PEOPLE DO:              │
│  (policy, programs, behavior)                │
│  → Merge into unified parameter system       │
│                                              │
│  IF IT'S ABOUT WHAT HIV DOES:               │
│  (disease progression, transmission)         │
│  → Keep in separate disease parameters       │
└─────────────────────────────────────────────┘
```

---

**This separation ensures:**
- Scientific validity (disease mechanics unchanged)
- Policy flexibility (easy to modify interventions)
- Clear maintenance (know where to find parameters)
- Proper calibration (history vs scenarios distinct)
