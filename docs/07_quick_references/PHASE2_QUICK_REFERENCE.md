# Phase 2 Quick Reference - Testing & Co-infections

**Status**: ✅ Validated (4/4 tests passed)

---

## 5 New CSV Files

| File | Indicators | Key Metrics |
|------|-----------|-------------|
| `testing_frequency.csv` | 8 | First-time testers, repeat testers, annual patterns |
| `testing_yield.csv` | Variable | Positivity by risk group, age-sex |
| `knowledge_of_status.csv` | 6 | Aware/unaware, time to diagnosis, 90-90-90 |
| `tb_hiv_coinfection.csv` | 8 | TB burden, IPT coverage, screening rates |
| `hepatitis_coinfection.csv` | 7 | HBV-HIV, HCV-HIV, regional CAMPHIA data |

---

## New Individual Attributes (11)

```python
# Testing tracking
self.total_tests_lifetime = 0
self.tests_last_12_months = 0
self.last_negative_test_year = None
self.aware_of_status = False

# TB-HIV
self.tb_status = "negative"
self.on_ipt = False
self.tb_screened_this_year = False

# Hepatitis (CAMPHIA-informed)
self.hbv_status = self._assign_hbv_status()  # Regional prevalence
self.hcv_status = "negative"

# Treatment
self.adherence_level = 0.95
self.drug_resistance = False
```

---

## New Model Methods (5)

1. **`_calculate_testing_frequency()`** - Testing patterns (8 metrics)
2. **`_calculate_testing_yield()`** - Positivity rates by strata
3. **`_calculate_knowledge_of_status()`** - Awareness tracking (6 metrics)
4. **`_calculate_tb_hiv_coinfection()`** - TB burden & IPT (8 metrics)
5. **`_calculate_hepatitis_coinfection()`** - HBV/HCV (7 metrics + regional)

---

## Key Use Cases

### 90-90-90 First Target
```python
# Load knowledge data
df = pd.read_csv('knowledge_of_status.csv')
awareness = df.groupby('year')['proportion_aware'].mean()
```

### Testing Efficiency
```python
# Load testing yield
yield_df = pd.read_csv('testing_yield.csv')
high_yield = yield_df[yield_df['yield_pct'] > 5.0]
```

### TB-HIV Monitoring
```python
# Load TB-HIV data
tb_df = pd.read_csv('tb_hiv_coinfection.csv')
ipt_coverage = tb_df.groupby('year')['ipt_coverage_pct'].mean()
```

### Regional Hepatitis
```python
# Load hepatitis data
hep_df = pd.read_csv('hepatitis_coinfection.csv')
hbv_by_region = hep_df.groupby(['year', 'region'])['hbv_hiv_coinfection'].sum()
```

---

## CAMPHIA Integration

**HBV Regional Prevalence** (used in `_assign_hbv_status()`):
- North: 10.8% (highest)
- Adamaoua: 9.1%
- Douala: 1.7% (lowest)
- National average: ~6%

Source: CAMPHIA 2017-2018

---

## Files Modified

1. **`src/hivec_cm/models/individual.py`**
   - Lines 85-109: Added 11 Phase 2 attributes
   - Lines 141-151: Added `_assign_hbv_status()` method

2. **`src/hivec_cm/models/model.py`**
   - Lines 1570-1833: Added 5 data collection methods (~263 lines)
   - Lines 817-858: Updated `_collect_detailed_indicators()`

3. **`scripts/run_enhanced_montecarlo.py`**
   - Lines 122-126: Added Phase 2 keys to `flattened_data`
   - Lines 435-528: Added 5 extraction blocks

---

## Validation

**Test**: `test_phase2_enhanced_data.py`

```
✅ Individual Attributes (11/11)
✅ Model Methods (5/5)
✅ Export Infrastructure (5/5)
✅ HBV CAMPHIA Integration
```

---

## Next: Phase 3

**Demographics & Prevention** (6 dimensions):
- Life years lost & DALYs
- Orphanhood
- AIDS-defining illnesses
- VMMC uptake
- PrEP coverage
- Fertility patterns

---

**Total Progress**: 11 CSV types, 95+ indicators, Phases 1-2 complete
