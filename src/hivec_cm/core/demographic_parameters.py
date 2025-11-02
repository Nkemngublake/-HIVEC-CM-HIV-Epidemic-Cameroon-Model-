"""
Enhanced demographic parameters for Cameroon HIV epidemic model.
Includes age-specific fertility/mortality and regional distributions.
"""

from typing import Dict
import numpy as np

# ============================================================================
# REGIONAL DATA FROM CAMPHIA 2017-2018 SURVEY
# Source: Cameroon Population-based HIV Impact Assessment
# ============================================================================

# Cameroon regional population distribution (2020 estimates)
# Based on Institut National de la Statistique (INS) Cameroon data
# Note: CAMPHIA separates Yaoundé and Douala as distinct regions
REGIONAL_DISTRIBUTION = {
    "Adamaoua": 0.057,      # 5.7%
    "Centre": 0.097,        # 9.7% (excluding Yaoundé)
    "Yaoundé": 0.080,       # 8.0% (capital city)
    "Est": 0.038,           # 3.8%
    "Extrême-Nord": 0.187,  # 18.7%
    "Littoral": 0.067,      # 6.7% (excluding Douala)
    "Douala": 0.080,        # 8.0% (economic capital)
    "Nord": 0.102,          # 10.2%
    "Nord-Ouest": 0.085,    # 8.5%
    "Sud": 0.028,           # 2.8%
    "Sud-Ouest": 0.072,     # 7.2%
    "Ouest": 0.107          # 10.7%
}

# Regional HIV Prevalence (adults 15-64 years)
# Source: CAMPHIA 2017-2018, Table 12.1
REGIONAL_HIV_PREVALENCE = {
    "Adamaoua": 0.049,      # 4.9%
    "Centre": 0.058,        # 5.8%
    "Yaoundé": 0.044,       # 4.4%
    "Est": 0.059,           # 5.9%
    "Extrême-Nord": 0.015,  # 1.5%
    "Littoral": 0.031,      # 3.1%
    "Douala": 0.033,        # 3.3%
    "Nord": 0.016,          # 1.6%
    "Nord-Ouest": 0.051,    # 5.1%
    "Sud": 0.063,           # 6.3% (highest)
    "Sud-Ouest": 0.036,     # 3.6%
    "Ouest": 0.027          # 2.7%
}

# National HIV prevalence (for reference)
NATIONAL_HIV_PREVALENCE = 0.037  # 3.7% (adults 15-64)

# Regional HIV Risk Multipliers (relative to national average)
# Derived from CAMPHIA prevalence data
REGIONAL_HIV_RISK = {
    region: prev / NATIONAL_HIV_PREVALENCE 
    for region, prev in REGIONAL_HIV_PREVALENCE.items()
}

# Regional Viral Load Suppression (<1000 copies/mL) among PLHIV
# Source: CAMPHIA 2017-2018, Table 14.8
REGIONAL_VIRAL_SUPPRESSION = {
    "Adamaoua": 0.341,      # 34.1%
    "Centre": 0.435,        # 43.5%
    "Yaoundé": 0.411,       # 41.1%
    "Est": 0.454,           # 45.4%
    "Extrême-Nord": 0.378,  # 37.8%
    "Littoral": 0.400,      # 40.0% (estimated, suppressed in report)
    "Douala": 0.451,        # 45.1%
    "Nord": 0.276,          # 27.6% (lowest)
    "Nord-Ouest": 0.609,    # 60.9% (highest)
    "Sud": 0.344,           # 34.4%
    "Sud-Ouest": 0.338,     # 33.8%
    "Ouest": 0.629          # 62.9% (second highest)
}

# Regional HIV Testing Rates (adults 15-64 years)
# Source: CAMPHIA 2017-2018, Table 13.1
REGIONAL_TESTING_EVER = {
    "Adamaoua": 0.475,      # 47.5%
    "Centre": 0.649,        # 64.9%
    "Yaoundé": 0.720,       # 72.0%
    "Est": 0.573,           # 57.3%
    "Extrême-Nord": 0.240,  # 24.0% (lowest)
    "Littoral": 0.688,      # 68.8%
    "Douala": 0.765,        # 76.5% (highest)
    "Nord": 0.268,          # 26.8%
    "Nord-Ouest": 0.717,    # 71.7%
    "Sud": 0.717,           # 71.7%
    "Sud-Ouest": 0.691,     # 69.1%
    "Ouest": 0.651          # 65.1%
}

REGIONAL_TESTING_12MONTHS = {
    "Adamaoua": 0.219,      # 21.9%
    "Centre": 0.297,        # 29.7%
    "Yaoundé": 0.374,       # 37.4% (highest)
    "Est": 0.291,           # 29.1%
    "Extrême-Nord": 0.098,  # 9.8% (lowest)
    "Littoral": 0.330,      # 33.0%
    "Douala": 0.429,        # 42.9%
    "Nord": 0.101,          # 10.1%
    "Nord-Ouest": 0.337,    # 33.7%
    "Sud": 0.342,           # 34.2%
    "Sud-Ouest": 0.326,     # 32.6%
    "Ouest": 0.316          # 31.6%
}

# Regional Male Circumcision Status (males 15-64 years)
# Source: CAMPHIA 2017-2018, Table 15.2
REGIONAL_CIRCUMCISION = {
    "Adamaoua": {
        "medical": 0.351,         # 35.1%
        "non_medical": 0.594,     # 59.4%
        "uncircumcised": 0.055    # Adjusted to sum to 1.0
    },
    "Centre": {
        "medical": 0.642,
        "non_medical": 0.258,
        "uncircumcised": 0.100    # Adjusted to sum to 1.0
    },
    "Yaoundé": {
        "medical": 0.671,
        "non_medical": 0.153,
        "uncircumcised": 0.176    # Adjusted to sum to 1.0
    },
    "Est": {
        "medical": 0.400,
        "non_medical": 0.527,
        "uncircumcised": 0.073    # Adjusted to sum to 1.0
    },
    "Extrême-Nord": {
        "medical": 0.267,
        "non_medical": 0.443,
        "uncircumcised": 0.290    # 28.2% (adjusted for consistency)
    },
    "Littoral": {
        "medical": 0.673,
        "non_medical": 0.170,
        "uncircumcised": 0.157    # Adjusted to sum to 1.0
    },
    "Douala": {
        "medical": 0.700,         # 70.0% (highest medical)
        "non_medical": 0.137,
        "uncircumcised": 0.163    # Adjusted to sum to 1.0
    },
    "Nord": {
        "medical": 0.301,
        "non_medical": 0.509,
        "uncircumcised": 0.190    # Adjusted to sum to 1.0
    },
    "Nord-Ouest": {
        "medical": 0.640,
        "non_medical": 0.169,
        "uncircumcised": 0.191    # Adjusted to sum to 1.0
    },
    "Sud": {
        "medical": 0.589,
        "non_medical": 0.312,
        "uncircumcised": 0.099    # Adjusted to sum to 1.0
    },
    "Sud-Ouest": {
        "medical": 0.653,
        "non_medical": 0.151,
        "uncircumcised": 0.196    # Adjusted to sum to 1.0
    },
    "Ouest": {
        "medical": 0.652,
        "non_medical": 0.174,
        "uncircumcised": 0.174    # Adjusted to sum to 1.0
    }
}

# Regional ART Status among PLHIV (15-64 years)
# Source: CAMPHIA 2017-2018, Table 14.3
REGIONAL_ART_STATUS = {
    "Adamaoua": {
        "unaware": 0.641,       # 64.1%
        "aware_not_on_art": 0.025,  # 2.5%
        "on_art": 0.334         # 33.4%
    },
    "Centre": {
        "unaware": 0.570,
        "aware_not_on_art": 0.057,
        "on_art": 0.374
    },
    "Yaoundé": {
        "unaware": 0.508,
        "aware_not_on_art": 0.053,
        "on_art": 0.439
    },
    "Est": {
        "unaware": 0.488,
        "aware_not_on_art": 0.028,
        "on_art": 0.484         # 48.4%
    },
    "Extrême-Nord": {
        "unaware": 0.705,       # 70.5% (highest)
        "aware_not_on_art": 0.042,
        "on_art": 0.253         # 25.3% (lowest)
    },
    "Littoral": {
        "unaware": 0.550,       # Estimated (suppressed in report)
        "aware_not_on_art": 0.050,
        "on_art": 0.400
    },
    "Douala": {
        "unaware": 0.546,
        "aware_not_on_art": 0.027,
        "on_art": 0.427
    },
    "Nord": {
        "unaware": 0.700,
        "aware_not_on_art": 0.058,
        "on_art": 0.242
    },
    "Nord-Ouest": {
        "unaware": 0.299,       # 29.9% (lowest)
        "aware_not_on_art": 0.033,
        "on_art": 0.668         # 66.8% (highest)
    },
    "Sud": {
        "unaware": 0.532,
        "aware_not_on_art": 0.046,
        "on_art": 0.422
    },
    "Sud-Ouest": {
        "unaware": 0.518,
        "aware_not_on_art": 0.080,
        "on_art": 0.401
    },
    "Ouest": {
        "unaware": 0.517,
        "aware_not_on_art": 0.019,
        "on_art": 0.464
    }
}

# Regional Hepatitis B Prevalence (adults 15-64 years)
# Source: CAMPHIA 2017-2018, Table 15.7
REGIONAL_HEPATITIS_B_PREVALENCE = {
    "Adamaoua": 0.083,      # 8.3%
    "Centre": 0.068,        # 6.8%
    "Yaoundé": 0.055,       # 5.5%
    "Est": 0.126,           # 12.6% (highest)
    "Extrême-Nord": 0.094,  # 9.4%
    "Littoral": 0.082,      # 8.2%
    "Douala": 0.081,        # 8.1%
    "Nord": 0.128,          # 12.8% (highest)
    "Nord-Ouest": 0.046,    # 4.6% (lowest)
    "Sud": 0.109,           # 10.9%
    "Sud-Ouest": 0.060,     # 6.0%
    "Ouest": 0.087          # 8.7%
}

# Age-specific fertility rates (births per woman per year) by 5-year age groups
# Based on Cameroon DHS 2018
AGE_SPECIFIC_FERTILITY_RATES = {
    # Age group start: fertility rate
    15: 0.118,   # 15-19 years: 118 per 1000 women
    20: 0.261,   # 20-24 years: 261 per 1000 women
    25: 0.295,   # 25-29 years: 295 per 1000 women (peak fertility)
    30: 0.263,   # 30-34 years: 263 per 1000 women
    35: 0.204,   # 35-39 years: 204 per 1000 women
    40: 0.104,   # 40-44 years: 104 per 1000 women
    45: 0.032    # 45-49 years: 32 per 1000 women
}

# Total fertility rate (TFR) trends for Cameroon
# Historical data from World Bank
FERTILITY_RATE_TRENDS = {
    1985: 6.50,  # Start of HIV epidemic
    1990: 6.30,
    1995: 5.95,
    2000: 5.60,
    2005: 5.30,
    2010: 5.05,
    2015: 4.80,
    2018: 4.60,  # DHS 2018
    2020: 4.50,
    2025: 4.20,  # Projected
    2030: 3.90,
    2040: 3.40,
    2050: 3.00,
    2075: 2.50,
    2100: 2.10   # Convergence to replacement level
}

# Age-specific mortality rates (deaths per person per year)
# Based on WHO life tables for Cameroon and UN population division
# Accounts for all-cause mortality EXCLUDING HIV
AGE_SPECIFIC_MORTALITY_RATES = {
    # Age: natural death rate (non-HIV)
    0: 0.058,    # Infant mortality rate (5.8%)
    1: 0.012,    # 1-4 years
    5: 0.003,    # 5-9 years
    10: 0.003,   # 10-14 years (kept same as 5-9 for monotonicity)
    15: 0.0032,  # 15-19 years
    20: 0.0035,  # 20-24 years
    25: 0.004,   # 25-29 years
    30: 0.005,   # 30-34 years
    35: 0.007,   # 35-39 years
    40: 0.010,   # 40-44 years
    45: 0.014,   # 45-49 years
    50: 0.020,   # 50-54 years
    55: 0.028,   # 55-59 years
    60: 0.040,   # 60-64 years
    65: 0.055,   # 65-69 years
    70: 0.080,   # 70-74 years
    75: 0.115,   # 75-79 years
    80: 0.165,   # 80+ years
}

# Life expectancy trends (years) - for mortality improvement calculations
# From World Bank data
LIFE_EXPECTANCY_TRENDS = {
    1985: 51.5,
    1990: 53.8,
    1995: 52.5,  # Decline due to HIV
    2000: 50.2,  # HIV impact peak
    2005: 51.8,
    2010: 55.4,  # Recovery with ART
    2015: 58.5,
    2018: 59.3,
    2020: 59.8,
    2025: 62.0,  # Projected
    2030: 64.5,
    2040: 68.0,
    2050: 71.0,
    2075: 75.0,
    2100: 78.0
}

# Mortality improvement factors over time
# Captures improvements in healthcare, nutrition, sanitation
MORTALITY_IMPROVEMENT_RATE = 0.012  # 1.2% annual improvement


def get_age_specific_fertility_rate(age: float, year: float) -> float:
    """
    Get age-specific fertility rate for given age and year.
    
    Args:
        age: Age of woman in years
        year: Calendar year
        
    Returns:
        Annual fertility rate for that age
    """
    if age < 15 or age >= 50:
        return 0.0
    
    # Get base rate from age group
    age_group = int(age // 5) * 5
    if age_group not in AGE_SPECIFIC_FERTILITY_RATES:
        age_group = min(AGE_SPECIFIC_FERTILITY_RATES.keys(), 
                       key=lambda x: abs(x - age_group))
    
    base_rate = AGE_SPECIFIC_FERTILITY_RATES[age_group]
    
    # Adjust for overall TFR trend
    tfr_1985 = FERTILITY_RATE_TRENDS[1985]
    tfr_current = np.interp(year, 
                           list(FERTILITY_RATE_TRENDS.keys()),
                           list(FERTILITY_RATE_TRENDS.values()))
    tfr_ratio = tfr_current / tfr_1985
    
    adjusted_rate = base_rate * tfr_ratio
    
    return float(adjusted_rate)


def get_age_specific_mortality_rate(age: float, year: float, 
                                    hiv_status: str = "susceptible") -> float:
    """
    Get age-specific natural mortality rate (non-HIV).
    
    Args:
        age: Age in years
        year: Calendar year
        hiv_status: HIV status (only returns natural mortality for susceptible)
        
    Returns:
        Annual natural death rate
    """
    # This function returns ONLY natural (non-HIV) mortality
    # HIV-related mortality is handled separately
    
    # Find closest age bracket
    age_brackets = sorted(AGE_SPECIFIC_MORTALITY_RATES.keys())
    age_group = age_brackets[0]
    for bracket in age_brackets:
        if age >= bracket:
            age_group = bracket
        else:
            break
    
    base_rate = AGE_SPECIFIC_MORTALITY_RATES[age_group]
    
    # Apply mortality improvement over time
    years_since_1985 = max(0, year - 1985)
    improvement_factor = (1 - MORTALITY_IMPROVEMENT_RATE) ** years_since_1985
    
    # Cap improvement to prevent unrealistic low mortality
    improvement_factor = max(0.5, improvement_factor)
    
    adjusted_rate = base_rate * improvement_factor
    
    return float(adjusted_rate)


def get_regional_assignment_probabilities() -> Dict[str, float]:
    """
    Get probability distribution for assigning agents to regions.
    
    Returns:
        Dictionary of region names to probabilities
    """
    return REGIONAL_DISTRIBUTION.copy()


def get_regional_hiv_risk_multiplier(region: str) -> float:
    """
    Get HIV transmission risk multiplier for a region.
    
    Args:
        region: Name of Cameroon region
        
    Returns:
        Risk multiplier (1.0 = national average)
    """
    return REGIONAL_HIV_RISK.get(region, 1.0)


def get_regional_hiv_prevalence(region: str) -> float:
    """
    Get baseline HIV prevalence for a region (CAMPHIA 2017-2018).
    
    Args:
        region: Name of Cameroon region
        
    Returns:
        HIV prevalence proportion (0-1)
    """
    return REGIONAL_HIV_PREVALENCE.get(region, NATIONAL_HIV_PREVALENCE)


def get_regional_viral_suppression_rate(region: str) -> float:
    """
    Get viral suppression rate (<1000 copies/mL) among PLHIV in a region.
    
    Args:
        region: Name of Cameroon region
        
    Returns:
        Viral suppression proportion (0-1)
    """
    return REGIONAL_VIRAL_SUPPRESSION.get(region, 0.40)


def get_regional_testing_rates(region: str) -> Dict[str, float]:
    """
    Get HIV testing rates for a region.
    
    Args:
        region: Name of Cameroon region
        
    Returns:
        Dictionary with 'ever_tested' and 'tested_12months' rates
    """
    return {
        'ever_tested': REGIONAL_TESTING_EVER.get(region, 0.50),
        'tested_12months': REGIONAL_TESTING_12MONTHS.get(region, 0.25)
    }


def get_regional_circumcision_distribution(region: str) -> Dict[str, float]:
    """
    Get male circumcision status distribution for a region.
    
    Args:
        region: Name of Cameroon region
        
    Returns:
        Dictionary with 'medical', 'non_medical', 'uncircumcised' proportions
    """
    default = {"medical": 0.50, "non_medical": 0.30, "uncircumcised": 0.20}
    return REGIONAL_CIRCUMCISION.get(region, default)


def get_regional_art_status_distribution(region: str) -> Dict[str, float]:
    """
    Get ART status distribution among PLHIV in a region.
    
    Args:
        region: Name of Cameroon region
        
    Returns:
        Dictionary with 'unaware', 'aware_not_on_art', 'on_art' proportions
    """
    default = {"unaware": 0.60, "aware_not_on_art": 0.05, "on_art": 0.35}
    return REGIONAL_ART_STATUS.get(region, default)


def get_regional_hepatitis_b_prevalence(region: str) -> float:
    """
    Get Hepatitis B prevalence for a region.
    
    Args:
        region: Name of Cameroon region
        
    Returns:
        Hepatitis B prevalence proportion (0-1)
    """
    return REGIONAL_HEPATITIS_B_PREVALENCE.get(region, 0.08)


def get_regional_cascade_metrics(region: str, year: float = 2018) -> Dict[str, float]:
    """
    Calculate 90-90-90 cascade metrics for a region based on CAMPHIA data.
    
    Args:
        region: Name of Cameroon region
        year: Calendar year (for future projection adjustments)
        
    Returns:
        Dictionary with cascade metrics
    """
    art_status = get_regional_art_status_distribution(region)
    vls_rate = get_regional_viral_suppression_rate(region)
    
    # Calculate cascade from CAMPHIA data
    aware_proportion = 1.0 - art_status['unaware']  # % aware of status
    on_art_among_aware = art_status['on_art'] / aware_proportion if aware_proportion > 0 else 0
    
    # Note: VLS is measured among all PLHIV in CAMPHIA
    # To get VLS among those on ART, we need to adjust
    on_art_proportion = art_status['on_art']
    vls_among_on_art = vls_rate / on_art_proportion if on_art_proportion > 0 else 0
    vls_among_on_art = min(vls_among_on_art, 1.0)  # Cap at 100%
    
    return {
        'first_90': aware_proportion,           # % aware of HIV status
        'second_90': on_art_among_aware,        # % on ART among aware
        'third_90': vls_among_on_art,           # % virally suppressed among on ART
        'overall_vls': vls_rate                 # % virally suppressed among all PLHIV
    }





def validate_demographic_consistency():
    """Validate that demographic parameters are internally consistent."""
    
    # Check regional distribution sums to 1.0
    total_regional = sum(REGIONAL_DISTRIBUTION.values())
    assert abs(total_regional - 1.0) < 0.001, \
        f"Regional distribution sums to {total_regional}, not 1.0"
    
    # Check all regions present in all regional data structures
    regions = set(REGIONAL_DISTRIBUTION.keys())
    assert regions == set(REGIONAL_HIV_PREVALENCE.keys()), \
        "Regions mismatch between distribution and prevalence"
    assert regions == set(REGIONAL_VIRAL_SUPPRESSION.keys()), \
        "Regions mismatch in viral suppression data"
    assert regions == set(REGIONAL_TESTING_EVER.keys()), \
        "Regions mismatch in testing data"
    assert regions == set(REGIONAL_CIRCUMCISION.keys()), \
        "Regions mismatch in circumcision data"
    assert regions == set(REGIONAL_ART_STATUS.keys()), \
        "Regions mismatch in ART status data"
    
    # Check circumcision proportions sum to ~1.0 for each region
    for region, circ_data in REGIONAL_CIRCUMCISION.items():
        total = sum(circ_data.values())
        assert abs(total - 1.0) < 0.10, \
            f"Circumcision proportions for {region} sum to {total:.3f}"
    
    # Check ART status proportions sum to ~1.0 for each region
    for region, art_data in REGIONAL_ART_STATUS.items():
        total = sum(art_data.values())
        assert abs(total - 1.0) < 0.10, \
            f"ART status proportions for {region} sum to {total:.3f}"
    
    # Check fertility rates are reasonable
    total_fertility = sum(AGE_SPECIFIC_FERTILITY_RATES.values()) * 5
    assert 3.0 < total_fertility < 8.0, \
        f"Implied TFR {total_fertility} outside reasonable range"
    
    # Check mortality rates are reasonable (not monotonic due to infant mortality)
    # But should be monotonic after childhood
    ages = sorted(AGE_SPECIFIC_MORTALITY_RATES.keys())
    childhood_ages = [a for a in ages if a >= 5]
    for i in range(len(childhood_ages) - 1):
        assert AGE_SPECIFIC_MORTALITY_RATES[childhood_ages[i]] <= \
               AGE_SPECIFIC_MORTALITY_RATES[childhood_ages[i+1]], \
               f"Mortality not monotonic after childhood at age {childhood_ages[i]}"
    
    # Check infant mortality is higher than child mortality (ages 1-5)
    assert AGE_SPECIFIC_MORTALITY_RATES[0] > AGE_SPECIFIC_MORTALITY_RATES[5], \
        "Infant mortality should be higher than child mortality"
    
    print("✅ Demographic parameters validated successfully")
    print(f"   - {len(regions)} regions with complete CAMPHIA 2017-2018 data")
    print(f"   - HIV prevalence range: {min(REGIONAL_HIV_PREVALENCE.values()):.1%} - {max(REGIONAL_HIV_PREVALENCE.values()):.1%}")
    print(f"   - VLS range: {min(REGIONAL_VIRAL_SUPPRESSION.values()):.1%} - {max(REGIONAL_VIRAL_SUPPRESSION.values()):.1%}")
    return True





if __name__ == "__main__":
    # Validation test
    validate_demographic_consistency()
    
    # Example usage
    print("\n" + "="*70)
    print("DEMOGRAPHIC PARAMETERS - EXAMPLE OUTPUTS")
    print("="*70)
    
    print("\n1. Age-Specific Vital Rates:")
    print(f"   Fertility rate for 25-year-old in 2020: "
          f"{get_age_specific_fertility_rate(25, 2020):.4f}")
    print(f"   Mortality rate for 40-year-old in 2020: "
          f"{get_age_specific_mortality_rate(40, 2020):.6f}")
    
    print("\n2. Regional Distribution:")
    print(f"   Total regions: {len(REGIONAL_DISTRIBUTION)}")
    for region, prop in sorted(REGIONAL_DISTRIBUTION.items(), 
                               key=lambda x: x[1], reverse=True)[:5]:
        print(f"   - {region}: {prop:.1%}")
    
    print("\n3. Regional HIV Prevalence (CAMPHIA 2017-2018):")
    for region, prev in sorted(REGIONAL_HIV_PREVALENCE.items(), 
                               key=lambda x: x[1], reverse=True)[:5]:
        print(f"   - {region}: {prev:.1%}")
    
    print("\n4. Regional Viral Suppression Rates:")
    for region, vls in sorted(REGIONAL_VIRAL_SUPPRESSION.items(), 
                              key=lambda x: x[1], reverse=True)[:5]:
        print(f"   - {region}: {vls:.1%}")
    
    print("\n5. Example Regional Cascade (Yaoundé):")
    cascade = get_regional_cascade_metrics("Yaoundé")
    print(f"   - 1st 90 (Aware): {cascade['first_90']:.1%}")
    print(f"   - 2nd 90 (On ART): {cascade['second_90']:.1%}")
    print(f"   - 3rd 90 (VLS): {cascade['third_90']:.1%}")
    print(f"   - Overall VLS: {cascade['overall_vls']:.1%}")
    
    print("\n6. Example Circumcision Distribution (Douala):")
    circ = get_regional_circumcision_distribution("Douala")
    print(f"   - Medical: {circ['medical']:.1%}")
    print(f"   - Non-medical: {circ['non_medical']:.1%}")
    print(f"   - Uncircumcised: {circ['uncircumcised']:.1%}")
    
    print("\n" + "="*70)

