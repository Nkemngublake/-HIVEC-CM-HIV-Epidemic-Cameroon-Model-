"""
HIVEC-CM Scenario Definitions
Cameroon HIV Epidemic Model - Policy Scenario Framework

Based on PSN 2024-2030 Strategic Plan
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BaselineScenario:
    """
    Scenario 0: Baseline Projection (Status Quo)
    
    Models the future trajectory if current trends, policies, and funding
    levels continue without significant change (2022 performance levels).
    
    Policy Question: What will the HIV epidemic look like by 2030 if we
    continue with the level of effort observed in 2022?
    """
    name: str = "Baseline"
    scenario_id: str = "S0_baseline"
    description: str = "Status quo - current trends continue"
    
    # Testing parameters (2022 levels)
    general_testing_rate: float = 0.29  # 29% tested in last 12 months
    index_testing_enabled: bool = False
    self_testing_enabled: bool = False
    
    # Treatment cascade (2022 performance)
    art_initiation_rate: float = 0.85
    art_retention_12m: float = 0.90
    art_retention_24m: float = 0.85
    viral_suppression_rate: float = 0.75
    
    # Prevention coverage (current levels)
    condom_distribution_coverage: float = 0.45
    prep_coverage_kp: float = 0.10  # 10% of key populations
    
    # PMTCT cascade (2022 performance)
    anc_coverage: float = 0.85
    pmtct_testing_rate: float = 0.80
    pmtct_art_coverage: float = 0.75
    mtct_rate: float = 0.101  # 10.1% at 6 weeks
    
    # Supply chain
    treatment_interruption_rate: float = 0.05  # 5% experience stockouts
    
    # Funding level (baseline = 1.0)
    funding_multiplier: float = 1.0


@dataclass
class OptimisticFundingScenario:
    """
    Scenario 1a: Optimistic Funding (Increased Domestic Investment)
    
    Models increased domestic resource mobilization (15-25% budget increase).
    
    Policy Question: If Cameroon successfully increases domestic investment,
    what is the potential acceleration in epidemic control?
    """
    name: str = "Optimistic Funding"
    scenario_id: str = "S1a_optimistic_funding"
    description: str = "15-25% budget increase through domestic mobilization"
    
    # Funding increase
    funding_multiplier: float = 1.20  # 20% increase
    
    # Enhanced testing (more campaigns)
    general_testing_rate: float = 0.38  # +30% from baseline
    testing_campaign_frequency: int = 6  # Bi-monthly campaigns
    
    # Improved ART services (more support staff)
    art_initiation_rate: float = 0.92  # +8%
    art_retention_12m: float = 0.95  # +5%
    art_retention_24m: float = 0.92  # +7%
    viral_suppression_rate: float = 0.85  # +10%
    
    # Expanded prevention
    condom_distribution_coverage: float = 0.60  # +33%
    prep_coverage_kp: float = 0.30  # 3x increase
    
    # Robust supply chain
    treatment_interruption_rate: float = 0.02  # -60% stockouts
    
    # Enhanced PMTCT
    anc_coverage: float = 0.92
    pmtct_art_coverage: float = 0.88


@dataclass
class PessimisticFundingScenario:
    """
    Scenario 1b: Pessimistic Funding (International Funding Reduction)
    
    Models 40% budget reduction in 2025 due to severe international funding cuts.
    
    Policy Question: What would be the impact if PEPFAR or Global Fund
    drastically reduces contribution by 40% starting in 2025?
    """
    name: str = "Pessimistic Funding"
    scenario_id: str = "S1b_pessimistic_funding"
    description: str = "40% budget cut from international funding reduction (2025)"
    
    # Funding reduction - DRASTIC 40% cut starting 2025
    funding_multiplier: float = 0.60  # 40% decrease
    funding_cut_year: int = 2025
    
    # Severely reduced testing (40% reduction from baseline)
    general_testing_rate: float = 0.17  # -41% from baseline (0.29 → 0.17)
    testing_campaign_frequency: int = 1  # Annual only (was 2)
    
    # Severely degraded treatment services (40% reduction impact)
    art_initiation_rate: float = 0.51  # -40% from baseline (0.85 → 0.51)
    art_retention_12m: float = 0.70  # -22% from baseline (0.90 → 0.70)
    art_retention_24m: float = 0.60  # -29% from baseline (0.85 → 0.60)
    viral_suppression_rate: float = 0.50  # -33% from baseline (0.75 → 0.50)
    
    # Severely reduced prevention (40% cuts)
    condom_distribution_coverage: float = 0.27  # -40% from baseline (0.45 → 0.27)
    prep_coverage_kp: float = 0.02  # -80% from baseline (0.10 → 0.02) - KP drastically underfunded
    
    # Major supply chain challenges
    treatment_interruption_rate: float = 0.25  # 5x increase in stockouts (0.05 → 0.25)
    drug_stockout_duration_days: int = 45  # Extended stockouts
    
    # Weakened PMTCT services
    anc_coverage: float = 0.70  # -18% from baseline
    pmtct_art_coverage: float = 0.50  # -33% from baseline
    
    # Key Populations catastrophically underfunded
    kp_service_availability: float = 0.30  # Only 30% of KP services remain
    kp_testing_reduction: float = 0.65  # 65% reduction in KP testing
    kp_outreach_workers: float = 0.25  # 75% reduction in peer outreach staff


@dataclass
class IntensifiedTestingScenario:
    """
    Scenario 2a: Closing the "First 95" Gap (Intensified Testing)
    
    Models scale-up of testing strategies to diagnose remaining unaware PLHIV.
    
    Policy Question: What is the most effective strategy to close the
    diagnosis gap?
    """
    name: str = "Intensified Testing"
    scenario_id: str = "S2a_intensified_testing"
    description: str = "Scale-up index testing, self-testing, and campaigns"
    
    # Enhanced general testing
    general_testing_rate: float = 0.45  # +55% from baseline
    testing_campaign_frequency: int = 12  # Monthly campaigns
    
    # Index case testing
    index_testing_enabled: bool = True
    partners_traced_per_index: float = 1.5
    partner_testing_acceptance: float = 0.75
    index_testing_yield: float = 0.40  # 40% positivity
    
    # HIV self-testing
    self_testing_enabled: bool = True
    self_test_annual_distribution: int = 500000
    self_test_uptake_rate: float = 0.65
    confirmatory_testing_rate: float = 0.80
    
    # Improved linkage
    linkage_to_care_rate: float = 0.90  # 90% link within 1 month
    
    # Target: Achieve First 95
    diagnosis_target: float = 0.95


@dataclass
class KeyPopulationScenario:
    """
    Scenario 2b: Targeting Key & Vulnerable Populations
    
    High-intensity focused intervention for Key Populations (FSW, MSM, PWID).
    
    Policy Question: What impact would focused KP interventions have on
    the national epidemic?
    """
    name: str = "Key Population Focus"
    scenario_id: str = "S2b_key_populations"
    description: str = "High-intensity package for key populations"
    
    # Key population definitions
    key_population_groups: List[str] = field(default_factory=lambda: [
        'fsw',  # Female sex workers
        'msm',  # Men who have sex with men
        'pwid'  # People who inject drugs
    ])
    
    # KP-specific parameters (95% coverage targets)
    kp_testing_rate: float = 0.95  # Test every 3 months
    kp_prep_coverage: float = 0.95  # 95% on PrEP
    kp_condom_use: float = 0.95  # 95% consistent use
    kp_art_coverage: float = 0.95  # 95% of HIV+ on ART
    kp_viral_suppression: float = 0.95  # 95% suppressed
    
    # Enhanced linkage for KP
    kp_linkage_to_care: float = 0.95
    kp_retention_rate: float = 0.95
    
    # Peer support and community mobilization
    peer_navigator_coverage: float = 0.80
    community_mobilization_effect: float = 0.30  # 30% risk reduction


@dataclass
class PMTCTScenario:
    """
    Scenario 2c: Achieving eTME (Elimination of Mother-to-Child Transmission)
    
    Models interventions to reduce MTCT from 10.1% to <5%.
    
    Policy Question: What combination of interventions achieves eTME target?
    """
    name: str = "eTME Achievement"
    scenario_id: str = "S2c_emtct"
    description: str = "Achieve <5% MTCT through enhanced PMTCT cascade"
    
    # Enhanced ANC
    anc_coverage: float = 0.98  # 98% attend ANC
    anc_first_trimester: float = 0.75  # 75% in 1st trimester
    
    # Universal testing in ANC
    pmtct_hiv_testing: float = 0.98
    pmtct_syphilis_testing: float = 0.98
    pmtct_hepb_testing: float = 0.98
    
    # Universal ART for HIV+ pregnant women
    pmtct_art_initiation: float = 0.98  # Start within 1 week
    pmtct_art_adherence: float = 0.95
    pmtct_viral_suppression: float = 0.95
    
    # Enhanced infant follow-up
    eid_testing_at_6weeks: float = 0.98
    eid_testing_at_18months: float = 0.95
    infant_prophylaxis_coverage: float = 0.98
    
    # Target MTCT rate
    mtct_target: float = 0.05  # <5%
    
    # Option B+ implementation
    lifelong_art_for_mothers: bool = True


@dataclass
class YouthAdolescentScenario:
    """
    Scenario 2d: Focusing on Youth & Adolescents (15-24 years)
    
    Improves cascade performance among youth, especially young women.
    
    Policy Question: What is the long-term impact of improving youth
    cascade performance?
    """
    name: str = "Youth & Adolescent Focus"
    scenario_id: str = "S2d_youth_focus"
    description: str = "Improve 90-90-90 cascade for ages 15-24"
    
    # Age group focus
    target_age_min: int = 15
    target_age_max: int = 24
    
    # Youth-friendly services
    youth_testing_rate: float = 0.85  # Much higher than general
    youth_self_test_coverage: float = 0.60
    
    # Enhanced linkage and retention
    youth_art_initiation: float = 0.90
    youth_retention_12m: float = 0.88
    youth_retention_24m: float = 0.85
    youth_viral_suppression: float = 0.85
    
    # Prevention for youth
    youth_prep_coverage: float = 0.40
    youth_condom_use: float = 0.70
    youth_sex_education: bool = True
    
    # Differentiated service delivery
    youth_dsd_model: bool = True  # Peer support groups
    youth_mhealth_support: bool = True  # SMS reminders


@dataclass
class PSNAspirationalScenario:
    """
    Scenario 3a: The PSN 2024-2030 Aspirational Goal
    
    Full implementation of strategic plan achieving all targets.
    
    Policy Question: If the 2024-2030 plan is fully implemented,
    what will the epidemic look like in 2030?
    """
    name: str = "PSN 2024-2030 Full Implementation"
    scenario_id: str = "S3a_psn_aspirational"
    description: str = "All PSN targets met - 95-95-95, eTME, prevention"
    
    # 95-95-95 achievement
    first_95_diagnosis: float = 0.95
    second_95_on_art: float = 0.95
    third_95_suppressed: float = 0.95
    
    # eTME achievement
    mtct_rate: float = 0.04  # <5%
    
    # Prevention coverage
    prep_coverage_kp: float = 0.95
    prep_coverage_youth: float = 0.40
    condom_use_general: float = 0.65
    vmmc_coverage: float = 0.80
    
    # Enhanced testing
    testing_coverage_annual: float = 0.60
    index_testing_scaled: bool = True
    self_testing_scaled: bool = True
    
    # Youth cascade
    youth_diagnosis: float = 0.90
    youth_art_coverage: float = 0.88
    youth_suppression: float = 0.85
    
    # Geographic reach
    rural_service_access: float = 0.90
    urban_service_access: float = 0.95
    
    # Quality of care
    treatment_interruption_rate: float = 0.01
    same_day_art_initiation: float = 0.80


@dataclass
class GeographicPrioritizationScenario:
    """
    Scenario 3b: Geographic Prioritization
    
    Tests concentrated resources in high-prevalence regions vs urban centers.
    
    Policy Question: Is it more effective to concentrate in high-prevalence
    regions or high-population urban centers?
    """
    name: str = "Geographic Prioritization"
    scenario_id: str = "S3b_geographic"
    description: str = "Concentrated resources in specific regions"
    
    # Prioritization strategy
    strategy: str = "high_prevalence"  # or "urban_centers" or "balanced"
    
    # High prevalence regions
    high_prevalence_regions: List[str] = field(default_factory=lambda: [
        'Sud', 'Est', 'Centre'
    ])
    
    # Urban centers
    urban_centers: List[str] = field(default_factory=lambda: [
        'Douala', 'Yaoundé'
    ])
    
    # Intervention package for priority areas (30% boost)
    priority_testing_boost: float = 0.30
    priority_linkage_boost: float = 0.30
    priority_retention_boost: float = 0.25
    priority_prevention_boost: float = 0.35
    
    # Maintenance for non-priority areas
    non_priority_service_level: float = 0.85  # 85% of baseline


# Scenario registry for easy access
SCENARIO_REGISTRY = {
    "S0_baseline": BaselineScenario,
    "S1a_optimistic_funding": OptimisticFundingScenario,
    "S1b_pessimistic_funding": PessimisticFundingScenario,
    "S2a_intensified_testing": IntensifiedTestingScenario,
    "S2b_key_populations": KeyPopulationScenario,
    "S2c_emtct": PMTCTScenario,
    "S2d_youth_focus": YouthAdolescentScenario,
    "S3a_psn_aspirational": PSNAspirationalScenario,
    "S3b_geographic": GeographicPrioritizationScenario
}


def get_scenario(scenario_id: str):
    """
    Retrieve scenario configuration by ID.
    
    Args:
        scenario_id: Scenario identifier (e.g., 'S1a_optimistic_funding')
    
    Returns:
        Scenario dataclass instance
    """
    if scenario_id not in SCENARIO_REGISTRY:
        raise ValueError(
            f"Unknown scenario: {scenario_id}. "
            f"Available: {list(SCENARIO_REGISTRY.keys())}"
        )
    
    return SCENARIO_REGISTRY[scenario_id]()


def list_scenarios():
    """List all available scenarios with descriptions."""
    scenarios = []
    for scenario_id, scenario_class in SCENARIO_REGISTRY.items():
        instance = scenario_class()
        scenarios.append({
            'id': scenario_id,
            'name': instance.name,
            'description': instance.description
        })
    return scenarios
