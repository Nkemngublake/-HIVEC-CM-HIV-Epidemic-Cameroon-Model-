"""
HIVEC-CM Disease Parameters
Biological and epidemiological constants that are independent of policy interventions.

These parameters represent the natural history of HIV infection and should NOT be 
modified by scenario parameters or policy interventions.
"""

# Viral Load Dynamics
VIRAL_LOAD_PARAMETERS = {
    "acute_phase": {
        "duration_days": 90,
        "peak_viral_load": 1000000,  # 6 log10 copies/mL
        "infectivity_multiplier": 10.0,  # Highly infectious during acute phase
        "description": "Acute HIV infection characteristics"
    },
    "chronic_phase": {
        "initial_viral_load": 10000,  # 4 log10 copies/mL
        "progression_rate_per_year": 0.15,
        "aids_threshold_vl": 500000,  # 5.7 log10 copies/mL
        "duration_years_median": 10,
        "description": "Chronic phase without treatment"
    },
    "aids_phase": {
        "viral_load_range": [500000, 10000000],
        "mortality_rate_per_year": 0.30,
        "description": "Advanced HIV without treatment"
    }
}

# Transmission Probabilities
TRANSMISSION_PARAMETERS = {
    "heterosexual": {
        "per_act_base_probability": 0.0008,
        "male_to_female_multiplier": 1.5,
        "female_to_male_multiplier": 1.0,
        "source": "Pinkerton SD, Abramson PR (1997); Boily et al (2009)"
    },
    "viral_load_effect": {
        "undetectable_vl": {
            "threshold": 200,  # copies/mL
            "transmission_multiplier": 0.01  # 99% reduction
        },
        "suppressed_vl": {
            "threshold": 1000,  # copies/mL
            "transmission_multiplier": 0.05  # 95% reduction
        },
        "unsuppressed_vl": {
            "threshold": 100000,  # copies/mL
            "transmission_multiplier": 1.0  # No reduction
        },
        "high_vl": {
            "threshold": 100000,  # copies/mL and above
            "transmission_multiplier": 2.0  # Increased risk
        },
        "acute_phase": {
            "transmission_multiplier": 10.0  # Highly infectious
        }
    },
    "circumcision": {
        "male_protection": 0.60,  # 60% reduction in male acquisition
        "source": "Cochrane systematic review 2009"
    },
    "condom_efficacy": {
        "consistent_use": 0.95,  # 95% reduction
        "typical_use": 0.80,  # 80% reduction
        "source": "Cochrane review, Weller & Davis 2002"
    }
}

# ART Treatment Effects (Biological)
ART_BIOLOGICAL_EFFECTS = {
    "viral_suppression": {
        "time_to_suppression_months": 6,
        "suppression_threshold": 1000,  # copies/mL
        "undetectable_threshold": 200,  # copies/mL
        "success_rate_first_line": 0.85,
        "description": "Time and thresholds for viral suppression on ART"
    },
    "mortality_reduction": {
        "on_art_suppressed": 0.96,  # 96% reduction vs untreated AIDS
        "on_art_not_suppressed": 0.70,  # 70% reduction
        "cd4_dependent": True,
        "source": "Antiretroviral Therapy Cohort Collaboration 2017"
    },
    "immune_reconstitution": {
        "cd4_recovery_rate": 50,  # cells/μL per year on suppressive ART
        "maximal_cd4_recovery": 500,  # typical plateau
        "description": "CD4 count recovery on ART"
    }
}

# Mother-to-Child Transmission (Biological Base Rates)
MTCT_BIOLOGICAL_RATES = {
    "no_intervention": {
        "in_utero": 0.05,
        "intrapartum": 0.15,
        "breastfeeding": 0.15,
        "total": 0.35,
        "source": "De Cock et al 2000"
    },
    "by_maternal_viral_load": {
        "undetectable": 0.01,  # <1% with undetectable VL
        "suppressed": 0.02,  # <2% with suppressed VL
        "unsuppressed": 0.15,
        "high_vl": 0.30,
        "source": "HPTN 052, PARTNER studies"
    },
    "breastfeeding": {
        "per_month_risk_no_art": 0.01,
        "per_month_risk_on_art": 0.001,
        "duration_months": 12,
        "source": "Simplified WHO model"
    }
}

# Disease Progression (Natural History)
DISEASE_PROGRESSION = {
    "acute_to_chronic": {
        "duration_days": 90,
        "automatic": True
    },
    "chronic_to_aids": {
        "median_time_years": 10,
        "variance": 3,  # years (log-normal distribution)
        "cd4_threshold": 200,  # cells/μL
        "vl_threshold": 500000  # copies/mL
    },
    "aids_mortality": {
        "no_art": {
            "median_survival_months": 12,
            "1_year_mortality": 0.30,
            "2_year_mortality": 0.50
        },
        "on_art": {
            "1_year_mortality": 0.05,
            "5_year_mortality": 0.10,
            "cd4_dependent": True
        }
    }
}

# Age and Sex Specific Parameters (Biological)
DEMOGRAPHIC_BIOLOGICAL = {
    "age_mixing": {
        "male_preference_younger_female": 5,  # years
        "female_preference_older_male": 3,  # years
        "age_gap_std": 7,  # standard deviation
        "source": "DHS Cameroon age-mixing patterns"
    },
    "sexual_debut": {
        "male_median": 17.5,
        "female_median": 16.5,
        "std": 2.0,
        "source": "Cameroon DHS"
    },
    "fertility": {
        "peak_age_female": [20, 35],
        "fertility_rate_by_age": {
            "15_19": 0.12,
            "20_24": 0.20,
            "25_29": 0.22,
            "30_34": 0.18,
            "35_39": 0.12,
            "40_44": 0.05,
            "45_49": 0.01
        },
        "source": "World Bank Cameroon fertility rates"
    }
}

# Partnership and Network Parameters
PARTNERSHIP_PARAMETERS = {
    "formation_rates": {
        "youth_15_24": 0.30,  # per year
        "adult_25_49": 0.20,
        "older_50_plus": 0.10
    },
    "dissolution_rates": {
        "short_term": 2.0,  # per year (mean duration 6 months)
        "long_term": 0.1,  # per year (mean duration 10 years)
        "marriage": 0.02  # per year (mean duration 50 years)
    },
    "concurrency": {
        "male_probability": 0.15,
        "female_probability": 0.05,
        "key_population_male": 0.30,
        "source": "Cameroon behavioral surveys"
    },
    "contact_frequency": {
        "married": 8,  # acts per month
        "cohabiting": 6,
        "regular": 4,
        "casual": 2,
        "source": "African sexual behavior surveys"
    }
}

# These are the ONLY parameters that should be in this file
# All policy-related parameters (testing rates, ART coverage, etc.) 
# should be in parameters_v4_calibrated.json and accessed via ParameterMapper
