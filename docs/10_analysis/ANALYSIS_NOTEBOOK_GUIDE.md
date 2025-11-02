# Publication Analysis Notebook - Quick Reference

## 📓 Notebook: `analysis_publication_ready.ipynb`

### Overview
Comprehensive epidemiological analysis of HIVEC-CM Monte Carlo simulation results comparing 4 policy scenarios (1985-2100) for academic publication.

---

## 📊 Notebook Structure

### Section 1: Import Libraries
- Pandas, NumPy for data manipulation
- Matplotlib, Seaborn for visualization
- SciPy, Statsmodels for statistical analysis
- Publication-quality plotting defaults

### Section 2: Load Data
- Automated loading from `results/full_scale_1985_2100/`
- 4 scenarios × 6 CSV types
- Data structure inspection

### Section 3: Data Preprocessing
- Uncertainty quantification function
- Decade/era categorization
- Scenario color scheme definition
- Key analysis years: [1985, 1995, 2005, 2015, 2023, 2030, 2050, 2075, 2100]

### Section 4: Descriptive Statistics
- HIV incidence summary (by scenario, era, sex)
- Peak incidence timing
- Prevalence trends (2023, 2030, 2050, 2100)

### Section 5: Temporal Trend Analysis
- Annual incidence trends with 95% CI
- Percent reduction from 2023 baseline
- Projections to 2030, 2050, 2100

### Section 6: Treatment Cascade (95-95-95)
- Cascade indicator trends (diagnosed, on ART, suppressed)
- Target achievement by 2030
- First year to achieve 95-95-95 by scenario

### Section 7: Statistical Testing
- ANOVA comparing scenarios (2030, 2050)
- Post-hoc Tukey HSD tests
- Pairwise t-tests vs baseline
- Effect sizes (Cohen's d)

### Section 8: Publication Visualizations

#### **Figure 1: HIV Incidence Trajectories (1985-2100)**
- Line plots with 95% CI ribbons
- All 4 scenarios overlaid
- Key intervention milestones marked
- Ages 15-49, total population

#### **Figure 2: Treatment Cascade Progress**
- 2×2 panel (one per scenario)
- Three cascade indicators: diagnosed, on ART, suppressed
- 95% target line
- 2000-2100 timeframe

#### **Figure 3: Age-Sex Stratified Incidence**
- Heatmaps for 2023, 2030, 2050
- Age groups × sex × scenarios
- Reveals disparities by demographics

#### **Figure 4: 2030 Scenario Comparison**
- Bar charts comparing key metrics
- Incidence, prevalence, cascade indicators
- Direct scenario comparisons

### Section 9: Key Metrics
- Cumulative infections (2023-2050)
- Infections averted vs baseline
- Time to epidemic control (incidence < 1/1,000)
- Years from 2023 to achieve control

### Section 10: Export Results
- Tables → `results/publication_outputs/tables/`
- Data → `results/publication_outputs/data/`
- Figure instructions for high-res export

### Section 11: Key Findings Summary
- Executive summary of major findings
- Policy implications
- Study strengths and limitations
- Recommended next steps

---

## 🎯 Key Outputs

### Tables Exported
1. `incidence_trends_summary.csv` - Annual incidence with uncertainty
2. `cascade_trends_summary.csv` - 95-95-95 indicator trends
3. `incidence_reduction_table.csv` - % reduction by scenario/year
4. `95-95-95_achievement_table.csv` - Target achievement years
5. `statistical_comparisons.csv` - T-tests vs baseline
6. `public_health_impact.csv` - Infections averted
7. `epidemic_control_timing.csv` - Year control achieved

### Figures Generated
- Figure 1: Incidence trajectories with uncertainty
- Figure 2: Treatment cascade 4-panel
- Figure 3: Age-sex heatmaps
- Figure 4: 2030 comparison bars

---

## 🔬 Statistical Methods

### Uncertainty Quantification
- Monte Carlo mean across 20 iterations
- 95% CI: 2.5th and 97.5th percentiles
- Median, standard deviation, min/max

### Hypothesis Testing
- One-way ANOVA for multi-scenario comparison
- Tukey HSD for pairwise post-hoc tests
- Independent t-tests vs baseline
- Significance level: α = 0.05

### Effect Sizes
- Cohen's d for standardized differences
- Interpretation: <0.2 (small), 0.2-0.8 (medium), >0.8 (large)

---

## 💡 Usage Instructions

### To Run the Notebook:
```bash
jupyter notebook analysis_publication_ready.ipynb
```

### To Save Figures in High Resolution:
```python
plt.savefig('results/publication_outputs/figures/figure1.png', dpi=300, bbox_inches='tight')
plt.savefig('results/publication_outputs/figures/figure1.pdf', bbox_inches='tight')
```

### To Export Additional Custom Tables:
```python
custom_df.to_csv('results/publication_outputs/tables/custom_table.csv', index=False)
```

---

## 📋 Analysis Checklist

### Data Quality
- ✅ All CSV files loaded successfully
- ✅ No missing critical data
- ✅ Consistent scenario naming
- ✅ Complete temporal coverage (1985-2100)

### Statistical Rigor
- ✅ Appropriate uncertainty quantification
- ✅ Multiple hypothesis correction considered
- ✅ Effect sizes calculated
- ✅ Assumptions validated

### Visualization Quality
- ✅ Publication-ready formatting (300 DPI)
- ✅ Clear legends and labels
- ✅ Colorblind-friendly palette
- ✅ 95% CI displayed
- ✅ Proper axis scaling

### Interpretation
- ✅ Key findings summarized
- ✅ Policy implications identified
- ✅ Limitations acknowledged
- ✅ Next steps recommended

---

## 🎓 For Manuscript Preparation

### Methods Section Should Include:
1. Model description (HIVEC-CM agent-based)
2. Scenario definitions (4 policy alternatives)
3. Simulation parameters (10k agents, 20 iterations, 1985-2100)
4. Enhanced data collection (17 indicators)
5. Statistical analysis approach (ANOVA, t-tests, effect sizes)
6. Uncertainty quantification method (Monte Carlo, 95% CI)

### Results Section Should Cover:
1. Epidemic trajectory projections (Figure 1)
2. 95-95-95 target achievement (Figure 2, Table 4)
3. Age-sex stratified outcomes (Figure 3)
4. Scenario comparison (Figure 4)
5. Public health impact (infections averted, Table 6)
6. Statistical significance (Tables 5, 7)

### Discussion Points:
- Funding levels critical for epidemic control
- 95-95-95 targets achievable with PSN scenario
- Age-sex disparities persist across scenarios
- Early intervention investment shows compounding benefits
- Long-term commitment needed beyond 2030

---

## 📞 Support

For questions about:
- **Notebook execution**: Check that all CSV files are in correct locations
- **Statistical methods**: Review Section 7 and statsmodels documentation
- **Figure customization**: Modify matplotlib parameters in Section 1
- **Additional analyses**: Use provided functions as templates

---

**Created:** October 15, 2025  
**Model Version:** HIVEC-CM v4.0  
**Simulation:** 1985-2100, 20 iterations, 10,000 agents  
**Scenarios:** S0_baseline, S1a_optimistic, S1b_pessimistic, S3a_psn_aspirational
