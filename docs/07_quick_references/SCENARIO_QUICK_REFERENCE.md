# HIVEC-CM Scenario Framework Quick Reference

## Framework Status: ✅ COMPLETE

All 9 PSN 2024-2030 aligned scenarios are fully defined and ready for model integration.

---

## Available Scenarios

### Baseline
- **S0_baseline**: Current trends continue (reference scenario)

### Financial Scenarios
- **S1a_optimistic_funding**: +20% budget increase
- **S1b_pessimistic_funding**: -20% budget cut

### Programmatic Scenarios
- **S2a_intensified_testing**: Scale-up testing to close diagnosis gap
- **S2b_key_populations**: High-intensity FSW/MSM/PWID interventions
- **S2c_emtct**: Enhanced PMTCT for <5% MTCT target
- **S2d_youth_focus**: Youth-friendly services (ages 15-24)

### Combination Scenarios
- **S3a_psn_aspirational**: Full PSN 2024-2030 implementation (95-95-95+)
- **S3b_geographic**: Geographic prioritization strategy

---

## Quick Usage

### List All Scenarios
```bash
python scripts/run_scenario_comparison.py --list-scenarios
```

### Run a Scenario
```bash
python scripts/run_scenario_comparison.py --scenario S3a_psn_aspirational
```

### Run with Baseline Comparison
```bash
python scripts/run_scenario_comparison.py --scenario S1a_optimistic_funding --compare-baseline
```

### Custom Parameters
```bash
python scripts/run_scenario_comparison.py --scenario S2a_intensified_testing --iterations 500 --output-dir results/custom
```

---

## Scenario Files

- **Definitions**: `src/hivec_cm/scenarios/scenario_definitions.py`
- **Runner Script**: `scripts/run_scenario_comparison.py`
- **Module Init**: `src/hivec_cm/scenarios/__init__.py`
- **Progress Tracker**: `PSN_SCENARIO_PROGRESS.md`

---

## Next Steps (Model Integration)

1. **Parameter Mapping**: Map scenario parameters to HIVEC-CM model parameters
2. **Model Integration**: Integrate scenarios into simulation execution
3. **Comparison Framework**: Build baseline vs scenario comparison tools
4. **Validation**: Test all scenarios with full model runs

---

## Key Policy Questions

| Scenario | Policy Question |
|----------|----------------|
| S0 | What happens if we maintain current programming? |
| S1a | If Cameroon increases domestic investment, what is the potential acceleration? |
| S1b | What would be the impact if PEPFAR/Global Fund reduces contribution? |
| S2a | What is the most effective strategy to close the diagnosis gap? |
| S2b | What impact would focused KP interventions have nationally? |
| S2c | What combination of interventions achieves eTME target? |
| S2d | What is the long-term impact of improving youth cascade performance? |
| S3a | If the 2024-2030 plan is fully implemented, what will 2030 look like? |
| S3b | Is it more effective to concentrate in high-prevalence regions or urban centers? |

---

## Contact & Support

For questions about scenario implementation or model integration, refer to:
- `PSN_SCENARIO_PROGRESS.md` for detailed progress tracking
- `ENHANCEMENT_SUMMARY.md` for model enhancements
- `MODEL_VALIDATION_README.md` for launch instructions
