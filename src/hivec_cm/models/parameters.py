import json
from dataclasses import dataclass
from typing import Dict, Union

@dataclass
class ModelParameters:
    """
    Parameters for the HIV/AIDS epidemic model.
    All rates are annual unless specified otherwise.
    """
    # Population parameters
    initial_population: int
    # For backward compatibility: allow scalar or structured dict with series
    birth_rate: Union[float, Dict]
    natural_death_rate: Union[float, Dict]
    life_expectancy: Union[float, Dict]
    
    # HIV transmission parameters
    base_transmission_rate: float
    initial_hiv_prevalence: float
    acute_multiplier: float
    chronic_multiplier: float
    aids_multiplier: float
    
    # Disease progression parameters
    acute_duration_months: float
    chronic_duration_years: float
    aids_duration_years: float
    
    # Behavioral and social parameters
    mean_contacts_per_year: float
    contact_variance: float
    risk_group_proportions: Dict[str, float]
    risk_group_multipliers: Dict[str, float]
    
    # Intervention parameters
    art_start_year: int
    art_efficacy_transmission: float
    art_efficacy_progression: float
    art_mortality_reduction: float
    
    # Testing and treatment parameters
    testing_rate_early: float
    testing_rate_late: float
    treatment_initiation_prob: float
    treatment_adherence: float
    
    # Mortality parameters
    hiv_mortality_multiplier: Dict[str, float]
    
    # Scenario parameters
    funding_cut_scenario: bool
    funding_cut_year: int
    
    # Time-varying transmission parameters (with defaults)
    use_time_varying_transmission: bool = True
    emergence_phase_multiplier: float = 0.80
    emergence_phase_end: float = 1990
    growth_phase_multiplier: float = 1.20
    growth_phase_end: float = 2005
    decline_phase_multiplier: float = 1.0
    
    # Optional magnitudes for funding-cut effects referenced in the model
    funding_cut_magnitude: float = 0.0
    kp_prevention_cut_magnitude: float = 0.0


def load_parameters(path: str) -> ModelParameters:
    """Loads model parameters from a JSON file."""
    with open(path, 'r') as f:
        config = json.load(f)
    
    params = config['parameters']
    
    return ModelParameters(
        initial_population=params['population']['initial_population'],
        birth_rate=params['population']['birth_rate'],
        natural_death_rate=params['population']['natural_death_rate'],
        life_expectancy=params['population'].get('life_expectancy', {}),
        base_transmission_rate=(
            params['transmission']['base_transmission_rate']
        ),
        initial_hiv_prevalence=(
            params['transmission']['initial_hiv_prevalence']
        ),
        acute_multiplier=params['transmission']['acute_multiplier'],
        chronic_multiplier=params['transmission']['chronic_multiplier'],
        aids_multiplier=params['transmission']['aids_multiplier'],
        acute_duration_months=(
            params['disease_progression']['acute_duration_months']
        ),
        chronic_duration_years=(
            params['disease_progression']['chronic_duration_years']
        ),
        aids_duration_years=(
            params['disease_progression']['aids_duration_years']
        ),
        mean_contacts_per_year=(
            params['social_behavioral']['mean_contacts_per_year']
        ),
        contact_variance=params['social_behavioral']['contact_variance'],
        risk_group_proportions=(
            params['social_behavioral']['risk_group_proportions']
        ),
        risk_group_multipliers=(
            params['social_behavioral']['risk_group_multipliers']
        ),
        art_start_year=params['interventions']['art_start_year'],
        art_efficacy_transmission=(
            params['interventions']['art_efficacy_transmission']
        ),
        art_efficacy_progression=(
            params['interventions']['art_efficacy_progression']
        ),
        art_mortality_reduction=(
            params['interventions']['art_mortality_reduction']
        ),
        testing_rate_early=params['interventions']['testing_rate_early'],
        testing_rate_late=params['interventions']['testing_rate_late'],
        treatment_initiation_prob=(
            params['interventions']['treatment_initiation_prob']
        ),
        treatment_adherence=params['interventions']['treatment_adherence'],
        hiv_mortality_multiplier=(
            params['mortality']['hiv_mortality_multiplier']
        ),
        funding_cut_scenario=params['scenario']['funding_cut_scenario'],
        funding_cut_year=params['scenario']['funding_cut_year'],
        # Time-varying transmission parameters
        use_time_varying_transmission=params['transmission'].get(
            'use_time_varying_transmission', True
        ),
        emergence_phase_multiplier=params['transmission'].get(
            'emergence_phase_multiplier', 0.80
        ),
        emergence_phase_end=params['transmission'].get(
            'emergence_phase_end', 1990
        ),
        growth_phase_multiplier=params['transmission'].get(
            'growth_phase_multiplier', 1.20
        ),
        growth_phase_end=params['transmission'].get(
            'growth_phase_end', 2005
        ),
        decline_phase_multiplier=params['transmission'].get(
            'decline_phase_multiplier', 1.0
        ),
        funding_cut_magnitude=(
            params.get('scenario', {}).get('funding_cut_magnitude', 0.0)
        ),
        kp_prevention_cut_magnitude=(
            params.get('scenario', {}).get('kp_prevention_cut_magnitude', 0.0)
        ),
    )
