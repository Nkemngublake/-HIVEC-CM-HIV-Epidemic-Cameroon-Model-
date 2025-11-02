# Mathematical Foundations of Agent Attributes in HIVEC-CM

**Model:** HIV Epidemic in Cameroon Model (HIVEC-CM)  
**Version:** 4.0  
**Date:** October 19, 2025  
**Type:** Agent-Based Stochastic Epidemic Model

---

## Table of Contents

1. [Demographic Attributes](#1-demographic-attributes)
2. [Behavioral Attributes](#2-behavioral-attributes)
3. [HIV Transmission Probability](#3-hiv-transmission-probability)
4. [Disease Progression](#4-disease-progression)
5. [Mortality Rates](#5-mortality-rates)
6. [Fertility & Birth Rates](#6-fertility--birth-rates)
7. [Mother-to-Child Transmission (MTCT)](#7-mother-to-child-transmission-mtct)
8. [Testing & Cascade Transitions](#8-testing--cascade-transitions)
9. [Enhanced Data Collection Attributes](#9-enhanced-data-collection-attributes)
10. [Stochastic Processes Summary](#10-stochastic-processes-summary)
11. [Key Mathematical Insights](#11-key-mathematical-insights)

---

## 1. DEMOGRAPHIC ATTRIBUTES

### 1.1 Age Assignment at Initialization

**Implementation:**
```python
def _sample_age_structure(self) -> float:
    age_groups = [
        (0, 15, 0.45),   # (min, max, probability)
        (15, 30, 0.25),
        (30, 50, 0.20),
        (50, 65, 0.08),
        (65, 85, 0.02)
    ]
    # Multinomial selection then uniform within range
    age ~ Uniform(age_min, age_max) | age_group ~ Multinomial(p)
```

**Mathematical Expression:**

$$P(\text{age} = a) = \sum_{g} P(g) \cdot \mathbb{1}[a \in g] \cdot \frac{1}{\text{width}(g)}$$

where:
- $g$ = age group
- $\mathbb{1}$ = indicator function
- $\text{width}(g)$ = age range of group $g$

**Age Group Distribution:**

| Age Range | Probability | Population Weight |
|-----------|-------------|------------------|
| 0-14 | 45% | Youth bulge |
| 15-29 | 25% | Young adults |
| 30-49 | 20% | Middle age |
| 50-64 | 8% | Older adults |
| 65+ | 2% | Elderly |

### 1.2 Regional Assignment

**Mathematical Formula:**

$$\text{region}_i \sim \text{Multinomial}(p_{\text{regional}})$$

**Regional Probabilities (CAMPHIA 2017-2018 data):**

| Region | Population % | HIV Risk Multiplier |
|--------|-------------|-------------------|
| Centre | 22% | 1.25 |
| Littoral | 17% | 1.15 |
| Ouest | 13% | 0.85 |
| Nord-Ouest | 12% | 0.75 |
| Sud | 8% | 1.65 |
| Est | 6% | 1.45 |
| Sud-Ouest | 6% | 1.35 |
| Adamaoua | 5% | 0.95 |
| Nord | 5% | 0.55 |
| Extrême-Nord | 4% | 0.45 |
| Others | 2% | 1.00 |

**Regional Risk Multiplier:**

$$r_{\text{region}} \in [0.45, 1.65]$$

Applied to all HIV-related probabilities:

$$P_{\text{HIV}}(\text{region}) = P_{\text{base}} \times r_{\text{region}}$$

---

## 2. BEHAVIORAL ATTRIBUTES

### 2.1 Risk Group Assignment

**Mathematical Expression:**

$$\text{risk\_group}_i \sim \text{Multinomial}(\{p_{\text{low}}, p_{\text{medium}}, p_{\text{high}}\})$$

**Default Distribution:**

| Risk Group | Proportion | Behavior Profile |
|------------|-----------|------------------|
| Low | 70% | Infrequent/protected sex |
| Medium | 25% | Moderate risk behavior |
| High | 5% | High-risk behavior |

**Risk Multipliers:**
- Low: $r_L = 0.5$
- Medium: $r_M = 1.0$
- High: $r_H = 3.0$

### 2.2 Sexual Contact Rate (Partners per Year)

**Complex Multi-Factor Formula:**

```python
base_rate = params.mean_contacts_per_year  # μ_contacts
risk_multiplier = params.risk_group_multipliers[risk_group]  # r
age_multiplier = f(age)  # a(age)
contacts_per_year ~ Gamma(shape=rate/variance, scale=variance)
```

**Mathematical Expression:**

$$C_i = \max(0.1, \text{Gamma}(\alpha, \beta))$$

where:

$$\alpha = \frac{\mu \cdot r \cdot a(age)}{v}$$

$$\beta = v$$

**Parameters:**
- $\mu$ = mean contacts (base rate, typically 1.0-2.0)
- $r$ = risk group multiplier (0.5, 1.0, or 3.0)
- $a(\text{age})$ = age-dependent multiplier
- $v$ = contact variance (controls heterogeneity)

**Age-Dependent Multiplier:**

$$a(\text{age}) = \begin{cases}
0.6 & \text{age} < 20 \\
1.3 & 20 \leq \text{age} < 30 \\
1.0 & 30 \leq \text{age} < 50 \\
0.4 & \text{age} \geq 50
\end{cases}$$

**Example Calculation:**
- 25-year-old, high-risk individual:
  - $\mu = 1.5$, $r = 3.0$, $a = 1.3$, $v = 0.5$
  - $\alpha = \frac{1.5 \times 3.0 \times 1.3}{0.5} = 11.7$
  - Expected contacts: $\alpha \times \beta = 11.7 \times 0.5 = 5.85$ per year

---

## 3. HIV TRANSMISSION PROBABILITY

### 3.1 Per-Contact Transmission Probability

**Multi-Component Formula:**

```python
transmission_prob = (
    base_transmission_rate ×
    stage_multiplier ×
    viral_load_effect ×
    risk_group_multiplier ×
    circumcision_effect ×
    condom_effect ×
    ART_effect
)
```

**Mathematical Expression:**

$$P(\text{transmission} | \text{contact}) = \beta_0 \cdot S \cdot V \cdot R \cdot (1-C_c) \cdot (1-C_p) \cdot (1-A)$$

### 3.2 Component Definitions

**Base Transmission Rate:**
$$\beta_0 \in [0.001, 0.003] \text{ per act}$$

Typical value: $\beta_0 = 0.0015$ (0.15% per unprotected act)

**Stage Multiplier ($S$):**

$$S = \begin{cases}
10.0 & \text{Acute HIV (first 3 months)} \\
1.0 & \text{Chronic HIV (baseline)} \\
2.0 & \text{AIDS (CD4 < 200)}
\end{cases}$$

**Viral Load Effect ($V$):**

$$V = \min\left(2.0, \frac{\text{VL}}{50000}\right)$$

where VL = viral load (copies/mL)

**Risk Group Multiplier ($R$):**
- Applied to susceptible individual
- $R \in \{0.5, 1.0, 3.0\}$

**Circumcision Protection ($C_c$):**
$$C_c = 0.60 \text{ (60% efficacy for males)}$$

**Condom Use Protection ($C_p$):**
$$C_p = 0.85 \text{ (85% efficacy when used consistently)}$$

**ART Effect ($A$):**
$$A = \begin{cases}
0.96 & \text{if VL < 1000 (suppressed)} \\
0.70 & \text{if on ART but unsuppressed} \\
0.0 & \text{if not on ART}
\end{cases}$$

### 3.3 Example Calculations

**Example 1: Acute infection, no protection**
- $\beta_0 = 0.0015$
- $S = 10.0$ (acute)
- $V = 2.0$ (high VL)
- $R = 1.0$, $C_c = 0$, $C_p = 0$, $A = 0$
- $P = 0.0015 \times 10 \times 2 \times 1 \times 1 \times 1 \times 1 = 0.03$ **(3% per act)**

**Example 2: Chronic infection on ART with viral suppression**
- $\beta_0 = 0.0015$
- $S = 1.0$ (chronic)
- $V = 0.04$ (VL = 2000)
- $R = 1.0$, $C_c = 0$, $C_p = 0$, $A = 0.96$
- $P = 0.0015 \times 1 \times 0.04 \times 1 \times 1 \times 1 \times (1-0.96) = 0.0000024$ **(0.00024%)**
  - Essentially zero risk ("Undetectable = Untransmittable")

---

## 4. DISEASE PROGRESSION

### 4.1 CD4 Count Dynamics

**Initial CD4 Count:**

$$\text{CD4}_{\text{init}} \sim \mathcal{N}(750, 150) \text{ cells/μL}$$

**CD4 Decline (Untreated Chronic Infection):**

$$\frac{dCD4}{dt} = -\delta \cdot \mathbb{1}[\text{not on ART}]$$

where:

$$\delta \sim \mathcal{N}(50, 20) \text{ cells/μL per year}$$

**Discrete-Time Update:**

$$\text{CD4}(t+\Delta t) = \max(0, \text{CD4}(t) - \delta \cdot \Delta t)$$

**CD4 Recovery on ART:**

$$\frac{dCD4}{dt} = \gamma \cdot \mathbb{1}[\text{on ART} \land \text{CD4} < 500]$$

where:

$$\gamma \sim \mathcal{N}(30, 10) \text{ cells/μL per year}$$

**Recovery Update:**

$$\text{CD4}(t+\Delta t) = \min(800, \text{CD4}(t) + \gamma \cdot \Delta t)$$

**Full Differential Equation:**

$$\frac{dCD4}{dt} = \begin{cases}
-\delta & \text{if HIV+ and not on ART} \\
+\gamma & \text{if on ART and CD4 < 500} \\
0 & \text{otherwise}
\end{cases}$$

### 4.2 Viral Load Dynamics

**Stage-Specific Viral Load Distributions:**

$$\log_{10}(\text{VL}) \sim \mathcal{N}(\mu_{\text{stage}}, \sigma^2)$$

**Distribution Parameters:**

| HIV Stage | Mean log₁₀(VL) | Std Dev | Mean VL (copies/mL) | Range |
|-----------|---------------|---------|---------------------|-------|
| Acute | 11.0 | 1.0 | 100,000,000 | 60K-200K |
| Chronic (untreated) | 9.0 | 1.0 | 1,000,000,000 | 8K-20K |
| AIDS | 10.0 | 1.0 | 10,000,000,000 | 20K-50K |
| On ART (suppressed) | 1.5 | 0.5 | 32 | <1,000 |
| On ART (unsuppressed) | 8.0 | 1.0 | 100,000,000 | 1K-10K |

**Mathematical Formula:**

$$VL_i = e^{X_i}, \quad X_i \sim \mathcal{N}(\mu_{\text{stage}}, \sigma^2)$$

**Viral Suppression on ART:**

$$P(\text{VL} < 1000 | \text{on ART}) = \alpha_{\text{adherence}}$$

Typical adherence: $\alpha \approx 0.85$ (85%)

### 4.3 HIV Stage Progression

**Stage Transition Diagram:**

```
Susceptible → Acute (3 months) → Chronic (8-12 years) → AIDS → Death
                                       ↓
                                    ART initiation
                                       ↓
                                Suppressed chronic
```

**Acute → Chronic Transition:**
- **Fixed duration:** 3 months (0.25 years)
- **Deterministic:** All acute infections progress to chronic

$$P(\text{acute} \to \text{chronic}) = \mathbb{1}[t_{\text{infection}} > 0.25]$$

**Chronic → AIDS Progression:**

**Exponential distribution with time-varying hazard:**

$$P(\text{chronic} \to \text{AIDS} | t) = 1 - e^{-\lambda t}$$

where:

$$\lambda = \frac{1}{\tau_{\text{chronic}}}$$

**Parameters:**
- $\tau_{\text{chronic}}$ = mean duration in chronic stage
  - Untreated: 10 years
  - On ART with suppression: Indefinite (negligible progression)

**Discrete-Time Progression Probability:**

$$P(\text{progress to AIDS} | \Delta t) = 1 - e^{-\lambda \Delta t} \approx \lambda \Delta t \text{ for small } \Delta t$$

**CD4-Dependent Progression:**

The progression rate accelerates with declining CD4:

$$\lambda(CD4) = \lambda_0 \times \begin{cases}
3.0 & \text{CD4} < 200 \\
1.5 & 200 \leq \text{CD4} < 350 \\
1.0 & \text{CD4} \geq 350
\end{cases}$$

---

## 5. MORTALITY RATES

### 5.1 Age-Specific Natural Mortality

**Piecewise Mortality Function:**

$$\mu_{\text{natural}}(a, t) = \mu_0(a) \times (1 - 0.01 \times (t - 1990))$$

**Base Age-Specific Mortality Rates ($\mu_0(a)$):**

| Age Group | Annual Mortality Rate | Per 1000 |
|-----------|---------------------|----------|
| 0 (infant) | 0.058 | 58 |
| 1-4 | 0.008 | 8 |
| 5-14 | 0.003 | 3 |
| 15-24 | 0.004 | 4 |
| 25-34 | 0.006 | 6 |
| 35-44 | 0.009 | 9 |
| 45-54 | 0.015 | 15 |
| 55-64 | 0.025 | 25 |
| 65+ | 0.045 | 45 |

**Temporal Improvement:**
- 1% reduction per year after 1990
- Reflects improvements in healthcare, sanitation

### 5.2 HIV-Specific Mortality

**Base HIV Stage Mortality:**

$$\mu_{\text{HIV}}^{\text{base}}(s) = \begin{cases}
0.02 & s = \text{acute} \, (2\% \text{ per year}) \\
0.05 & s = \text{chronic} \, (5\% \text{ per year}) \\
0.30 & s = \text{AIDS} \, (30\% \text{ per year})
\end{cases}$$

**ART Effect on HIV Mortality:**

$$\mu_{\text{HIV}}^{\text{ART}} = \mu_{\text{HIV}}^{\text{base}} \times E_{\text{ART}}$$

where:

$$E_{\text{ART}} = \begin{cases}
0.04 & \text{if VL < 1000 (96\% reduction)} \\
0.30 & \text{if on ART but VL ≥ 1000 (70\% reduction)} \\
1.00 & \text{if not on ART (no reduction)}
\end{cases}$$

**CD4-Dependent Mortality Multiplier:**

$$M_{CD4} = \begin{cases}
2.0 & \text{CD4} < 200 \\
1.5 & 200 \leq \text{CD4} < 350 \\
1.0 & \text{CD4} \geq 350
\end{cases}$$

**Total HIV-Specific Mortality:**

$$\mu_{\text{HIV}}(s, CD4, ART) = \mu_{\text{HIV}}^{\text{base}}(s) \times E_{\text{ART}} \times M_{CD4}$$

### 5.3 Combined Total Mortality

**Additive Hazard Model:**

$$\mu_{\text{total}}(t) = \mu_{\text{natural}}(a, t) + \mu_{\text{HIV}}(s, CD4, ART) \times \mathbb{1}[\text{HIV+}]$$

**Survival Probability over Time Interval $\Delta t$:**

$$P(\text{survive } \Delta t) = e^{-\mu_{\text{total}} \Delta t} \approx 1 - \mu_{\text{total}} \Delta t$$

**Example: 35-year-old on ART with CD4=400, VL<1000 in 2020**
- Natural: $\mu_n = 0.009 \times (1 - 0.01 \times 30) = 0.0063$
- HIV base: $\mu_h = 0.05$ (chronic)
- ART effect: $E = 0.04$
- CD4 multiplier: $M = 1.0$
- HIV mortality: $0.05 \times 0.04 \times 1.0 = 0.002$
- **Total: $0.0063 + 0.002 = 0.0083$ (0.83% per year)**

---

## 6. FERTILITY & BIRTH RATES

### 6.1 Age-Specific Fertility Rates (ASFR)

**Time-Varying ASFR:**

$$\text{ASFR}(a, t) = \text{ASFR}_0(a) \times (1 - 0.005 \times (t - 1990))$$

**Base ASFR by Age Group (1985 values):**

| Age Group | ASFR₀ (1985) | ASFR (2100) | Change |
|-----------|-------------|-------------|--------|
| 15-19 | 0.120 | 0.090 | -25% |
| 20-24 | 0.280 | 0.210 | -25% |
| 25-29 | 0.320 | 0.240 | -25% (peak) |
| 30-34 | 0.280 | 0.210 | -25% |
| 35-39 | 0.220 | 0.165 | -25% |
| 40-44 | 0.120 | 0.090 | -25% |
| 45-49 | 0.040 | 0.030 | -25% |

**Total Fertility Rate (TFR):**

$$\text{TFR}(t) = 5 \times \sum_{a \in \{15,20,25,30,35,40,45\}} \text{ASFR}(a, t)$$

**TFR Trajectory:**
- 1985: TFR ≈ 6.5 children per woman
- 2020: TFR ≈ 4.5
- 2050: TFR ≈ 3.0
- 2100: TFR ≈ 2.1 (replacement level)

### 6.2 Stochastic Birth Process

**Expected Births:**

$$\mathbb{E}[B(t)] = \sum_{a=15}^{49} N_a^F(t) \cdot \text{ASFR}(a,t) \cdot \Delta t$$

where:
- $N_a^F(t)$ = number of women aged $a$ at time $t$
- $\Delta t$ = time step (typically 1 year)

**Actual Births (Poisson Process):**

$$B(t) \sim \text{Poisson}(\mathbb{E}[B(t)])$$

**Variance:**

$$\text{Var}[B(t)] = \mathbb{E}[B(t)]$$

This creates realistic demographic stochasticity.

### 6.3 HIV Impact on Fertility

**Fertility Reduction Factors:**

$$\text{ASFR}_{\text{HIV+}} = \text{ASFR}_{\text{base}} \times F_{HIV}$$

where:

$$F_{HIV} = \begin{cases}
0.90 & \text{HIV+ chronic, not on ART} \\
0.95 & \text{HIV+ on ART} \\
0.75 & \text{HIV+ AIDS stage}
\end{cases}$$

---

## 7. MOTHER-TO-CHILD TRANSMISSION (MTCT)

### 7.1 Time-Varying MTCT Rates

**Era-Specific MTCT Probabilities:**

$$P(\text{infant HIV+} | \text{mother HIV+}) = \rho(t, \text{ART}, \text{VLS})$$

**Historical MTCT Rates:**

| Era | Mother's ART Status | Viral Suppression | MTCT Rate |
|-----|-------------------|------------------|-----------|
| **Pre-2004** (No interventions) |
| | Any | N/A | 25% |
| **2004-2009** (PMTCT Option A) |
| | No ART | N/A | 15% |
| | On ART | Suppressed | 2% |
| | On ART | Unsuppressed | 5% |
| **2010-2015** (Option B+) |
| | No ART | N/A | 12% |
| | On ART | Suppressed | 1% |
| | On ART | Unsuppressed | 3% |
| **2016+** (Treat All + Enhanced PMTCT) |
| | No ART | N/A | 10% |
| | On ART | Suppressed | 0.5% |
| | On ART | Unsuppressed | 2% |

**Mathematical Expression:**

$$\rho(t, ART, VLS) = \begin{cases}
0.25 & t < 2004 \\
\rho_{\text{PMTCT}}(t, ART, VLS) & t \geq 2004
\end{cases}$$

where $\rho_{\text{PMTCT}}$ is the era- and treatment-specific rate from table above.

### 7.2 Stochastic MTCT Process

**For each birth to HIV+ mother:**

$$\text{Infant HIV status} \sim \text{Bernoulli}(\rho(t, ART, VLS))$$

**Example Calculation (2020, mother on ART with VL<1000):**
- $t = 2020$ → Use 2016+ guidelines
- Mother on ART: Yes
- Viral suppression: Yes (VL < 1000)
- **MTCT probability: 0.5%**

---

## 8. TESTING & CASCADE TRANSITIONS

### 8.1 HIV Testing Probability

**Time-Varying Base Testing Rates:**

$$\tau(t) = \begin{cases}
0.05 & t < 2004 \\
0.18 & 2004 \leq t < 2010 \\
0.32 & 2010 \leq t < 2018 \\
0.55 & t \geq 2018
\end{cases}$$

**Risk-Adjusted Testing Probability:**

$$P(\text{test in year } t) = \tau(t) \times r_{\text{risk}}$$

where:

$$r_{\text{risk}} = \begin{cases}
0.5 & \text{low risk} \\
1.0 & \text{medium risk} \\
2.0 & \text{high risk}
\end{cases}$$

**Test Accuracy:**

$$P(\text{correct diagnosis} | \text{tested}) = 0.98$$

### 8.2 ART Eligibility Criteria

**CD4 Threshold Evolution:**

$$E_{\text{ART}}(t, CD4) = \begin{cases}
CD4 \leq 200 & t < 2010 \text{ (WHO 2002-2009)} \\
CD4 \leq 350 & 2010 \leq t < 2013 \text{ (WHO 2010)} \\
CD4 \leq 500 & 2013 \leq t < 2016 \text{ (WHO 2013)} \\
\text{True} & t \geq 2016 \text{ (Treat All / Test and Start)}
\end{cases}$$

### 8.3 ART Initiation Probability

**Multi-Factor Initiation Model:**

$$P(\text{start ART} | \text{diagnosed, eligible}) = p_0 \times \phi(t) \times \Delta t$$

where:

**Base initiation probability:** $p_0$ (parameter, typically 0.7)

**Era-specific scaling factor:**

$$\phi(t) = \begin{cases}
0.1 & t < 2004.75 \text{ (pre-price drop, high cost)} \\
0.5 & 2004.75 \leq t < 2010 \text{ (post-price drop)} \\
1.0 & t \geq 2010 \text{ (PEPFAR/Global Fund scale-up)}
\end{cases}$$

**Example: 2015, diagnosed with CD4=300**
- Eligible: Yes (threshold = 350)
- $p_0 = 0.7$
- $\phi(2015) = 1.0$
- Annual probability: $0.7 \times 1.0 = 0.70$ (70%)

### 8.4 Viral Suppression on ART

**After 6 months on ART:**

$$P(\text{VL} < 1000 | \text{on ART for } \geq 6 \text{ months}) = \alpha_{\text{adherence}}$$

**Typical adherence:** $\alpha \approx 0.85$ (85%)

**Factors affecting adherence:**
- Side effects
- Stigma
- Access to care
- Food insecurity
- Mental health

---

## 9. ENHANCED DATA COLLECTION ATTRIBUTES

### 9.1 Phase 1: Transmission Tracking

**Donor Characteristics Captured:**

For each new infection, record:

$$\{D_{id}, D_{stage}, D_{VL}, t_{infection}\}$$

where:
- $D_{id}$ = donor agent ID
- $D_{stage} \in \{\text{acute, chronic, AIDS}\}$
- $D_{VL}$ = donor viral load at transmission
- $t_{infection}$ = calendar year of infection

**Time to Diagnosis:**

$$\Delta t_{\text{infection→diagnosis}} = t_{\text{diagnosis}} - t_{\text{infection}}$$

**Time to ART Initiation:**

$$\Delta t_{\text{diagnosis→ART}} = t_{\text{ART}} - t_{\text{diagnosis}}$$

### 9.2 Phase 2: Co-Infections

**HBV Co-infection (CAMPHIA Regional Data):**

$$P(\text{HBV+}) = p_{\text{region}} \in [0.046, 0.128]$$

**Regional HBV Prevalence:**

| Region | HBV Prevalence |
|--------|---------------|
| Extrême-Nord | 12.8% |
| Nord | 11.5% |
| Adamaoua | 10.2% |
| Est | 9.8% |
| Sud | 8.9% |
| Centre | 7.4% |
| Others | ~6.5% |
| Nord-Ouest | 4.6% |

**TB-HIV Co-infection (Simplified):**

$$\text{TB status} \in \{\text{negative, active, latent, on\_IPT}\}$$

*Note: Full TB transmission model not implemented in current version*

### 9.3 Phase 3: Health Outcomes

**Disability-Adjusted Life Years (DALYs):**

$$\text{DALY} = \text{YLL} + \text{YLD}$$

where:

**Years of Life Lost (YLL):**

$$\text{YLL} = L - a_d$$

- $L$ = standard life expectancy (typically 80 years)
- $a_d$ = age at death

**Years Lived with Disability (YLD):**

$$\text{YLD} = \sum_{t=t_0}^{t_d} w(t) \cdot \Delta t$$

where $w(t)$ = disability weight at time $t$ ∈ [0, 1]

**Disability Weights by HIV Stage:**

| HIV Status | Disability Weight |
|-----------|------------------|
| Susceptible | 0.00 |
| Acute HIV | 0.05 |
| Chronic HIV (untreated) | 0.15 |
| Chronic HIV (on ART, suppressed) | 0.05 |
| AIDS (untreated) | 0.50 |
| AIDS (on ART) | 0.30 |

**Quality-Adjusted Life Years (QALYs):**

$$\text{QALY} = \sum_{t=t_0}^{t_d} (1 - w(t)) \cdot \Delta t$$

---

## 10. STOCHASTIC PROCESSES SUMMARY

| Process | Distribution | Parameters | Interpretation |
|---------|-------------|------------|----------------|
| **Demographics** |
| Age at init | Piecewise Uniform | 5 age groups | Population structure |
| Region | Multinomial | 12 regional probs | Geographic distribution |
| Risk group | Multinomial | {0.7, 0.25, 0.05} | Behavioral heterogeneity |
| **Sexual Behavior** |
| Contacts/year | Gamma | (μ×r×a/v, v) | Partnership formation |
| Partnership duration | Exponential | mean=2 years | Relationship stability |
| **HIV Biology** |
| CD4 initial | Normal | (750, 150) | Immune status |
| CD4 decline | Normal | (50, 20) /year | Disease progression |
| CD4 recovery | Normal | (30, 10) /year | ART effect |
| Viral load | Log-Normal | Stage-specific | Infectiousness |
| **Disease Progression** |
| Acute duration | Fixed | 3 months | Deterministic |
| Chronic→AIDS | Exponential | λ=1/10 years | Stochastic |
| **Vital Events** |
| Births | Poisson | ASFR × women × dt | Demographic stochasticity |
| Deaths | Bernoulli | μ(age, HIV) × dt | Competing risks |
| **Transmission** |
| HIV transmission | Bernoulli | β × factors | Per-contact risk |
| MTCT | Bernoulli | ρ(t, ART, VLS) | Vertical transmission |
| **Cascade** |
| Testing | Bernoulli | τ(t) × risk × dt | Service uptake |
| ART initiation | Bernoulli | p × φ(t) × dt | Treatment access |
| Viral suppression | Bernoulli | α_adherence | Adherence outcome |

---

## 11. KEY MATHEMATICAL INSIGHTS

### 11.1 Multi-Scale Stochasticity

The model incorporates randomness at multiple levels:

1. **Individual-level:** Bernoulli trials
   - Transmission events
   - Testing decisions
   - Death events

2. **Population-level:** Poisson processes
   - Birth cohorts
   - Contact rates

3. **Continuous traits:** Normal/Log-Normal distributions
   - CD4 counts
   - Viral loads
   - Partnership durations

### 11.2 Time-Varying Parameters

Most transition rates are functions of calendar time:

$$\theta(t) = \theta_0 \cdot f(t)$$

Examples:
- **Testing rates:** Step function with policy changes
- **Birth rates:** Linear decline (demographic transition)
- **Mortality:** Exponential improvement (healthcare advances)
- **ART eligibility:** Threshold changes (WHO guidelines)

### 11.3 Multiplicative Risk Structure

Transmission probability uses **product of independent factors**:

$$P = \prod_i (1 - \text{protection}_i) \times \text{base\_risk} \times \prod_j \text{amplifier}_j$$

This allows:
- Separate parameterization of different interventions
- Easy addition of new prevention methods
- Multiplicative (not additive) effects

### 11.4 Threshold-Based Transitions

Many events use **CD4 thresholds**:

$$\text{Event occurs if: } CD4(t) \leq \text{threshold}(t)$$

Examples:
- ART eligibility (time-varying threshold)
- AIDS progression (CD4 < 200)
- Mortality multipliers (CD4 < 350)

### 11.5 Regional Heterogeneity

All HIV-related probabilities modified by regional multiplier:

$$P_{\text{regional}} = P_{\text{base}} \times r_{\text{region}}$$

where $r_{\text{region}} \in [0.45, 1.65]$

This captures:
- Geographic HIV prevalence variation
- Cultural/behavioral differences
- Access to services

### 11.6 Competing Risks

Total mortality is **additive hazard**:

$$\mu_{\text{total}} = \mu_{\text{natural}} + \mu_{\text{HIV}} + \mu_{\text{TB}} + \cdots$$

This ensures:
- Proper survival curves
- Cause-specific mortality tracking
- Life expectancy calculations

---

## VALIDATION & CALIBRATION

### Calibration Targets

1. **HIV Prevalence (Age-Sex-Region):** CAMPHIA 2017-2018
2. **Treatment Cascade (95-95-95):** UNAIDS targets
3. **Birth/Death Rates:** World Bank demographic data
4. **MTCT Rates:** WHO PMTCT guidelines
5. **Testing Coverage:** DHS surveys
6. **ART Coverage:** PEPFAR/Global Fund reports

### Sensitivity Parameters

Key parameters requiring careful calibration:

| Parameter | Range | Impact |
|-----------|-------|--------|
| Base transmission rate ($\beta_0$) | [0.001, 0.003] | Epidemic size |
| Contact rate variance | [0.3, 0.8] | Heterogeneity |
| ART adherence ($\alpha$) | [0.75, 0.95] | Viral suppression |
| Testing scale-up rates | Time-varying | Cascade progression |
| Risk group proportions | [0.05, 0.15] for high | Epidemic concentration |

### Uncertainty Quantification

**Monte Carlo Approach:**
- 20 iterations per scenario
- 95% confidence intervals
- Sensitivity analyses on key parameters

**Sources of Uncertainty:**
1. Parameter values (e.g., transmission rate)
2. Stochastic processes (random events)
3. Initial conditions (age structure, prevalence)
4. Future scenarios (policy changes)

---

## IMPLEMENTATION NOTES

### Computational Considerations

**Time Step:** $\Delta t = 1$ year (annual updates)
- Fine enough for epidemic dynamics
- Computationally tractable for 115-year simulations

**Population Size:** 10,000 agents
- Balances computational cost vs. stochasticity
- Sufficient for stable prevalence estimates

**Parallel Processing:** 8 CPU cores
- Monte Carlo iterations run in parallel
- ~40-60 minutes per scenario

### Code Structure

**Key Classes:**
- `Individual`: Agent attributes and methods
- `Model`: Population dynamics and interactions
- `Parameters`: Configuration and calibration values
- `ParameterMapper`: Time-varying parameter interpolation

**Data Collection:**
- Annual aggregate statistics
- Individual-level event histories
- 17 enhanced indicator types (Phases 1-3)

---

## REFERENCES

### Scientific Basis

1. **HIV Natural History:**
   - Acute infection duration: 3 months (Fiebig stages)
   - Chronic duration: 8-12 years median (CASCADE collaboration)
   - CD4 decline: 50-80 cells/μL/year (MACS cohort)

2. **Transmission Probability:**
   - Per-act transmission: 0.08-0.3% (Boily et al., 2009)
   - Acute phase multiplier: 10× (Hollingsworth et al., 2008)
   - ART effect: 96% reduction at VL<1000 (HPTN 052)

3. **Treatment Effects:**
   - Viral suppression: 85-90% (IeDEA collaboration)
   - CD4 recovery: 30-50 cells/μL/year (CASCADE)
   - Mortality reduction: 80-90% (Zwahlen et al., 2009)

4. **PMTCT:**
   - Option B+ effectiveness: 98-99% (WHO guidelines)
   - Historical MTCT: 25-35% untreated (De Cock et al., 2000)

### Data Sources

- **CAMPHIA 2017-2018:** HIV prevalence, regional variation, HBV
- **World Bank:** Demographic rates, life expectancy
- **UNAIDS:** Treatment cascade, 95-95-95 targets
- **WHO:** ART guidelines, PMTCT protocols
- **PEPFAR:** Service delivery, program data

---

**Document prepared:** October 19, 2025  
**Model version:** HIVEC-CM v4.0  
**Simulation period:** 1985-2100 (115 years)  
**Scenarios analyzed:** 4 (baseline, optimistic funding, pessimistic funding, PSN aspirational)  
**Monte Carlo iterations:** 20 per scenario  
**Total simulations:** 80 runs (4 scenarios × 20 iterations)
