
import numpy as np
import pandas as pd
import logging
from typing import List, Optional, Callable, Dict, Any
from numpy.random import default_rng, Generator
from hivec_cm.utils.accel import NUMBA_AVAILABLE, poisson_counts_numba
import time

from .parameters import ModelParameters
from .individual import Individual
from hivec_cm.calibration.parameter_mapper import ParameterMapper
from hivec_cm.core.disease_parameters import (
    VIRAL_LOAD_PARAMETERS,
    TRANSMISSION_PARAMETERS,
    ART_BIOLOGICAL_EFFECTS,
    MTCT_BIOLOGICAL_RATES,
    DISEASE_PROGRESSION,
    DEMOGRAPHIC_BIOLOGICAL,
    PARTNERSHIP_PARAMETERS
)
from hivec_cm.core.demographic_parameters import (
    get_age_specific_fertility_rate,
    get_age_specific_mortality_rate,
    get_regional_assignment_probabilities
)

logger = logging.getLogger(__name__)


class EnhancedHIVModel:
    """HIVEC CM enhanced model with improved calibration."""

    def __init__(
        self,
        params: ModelParameters,
        calibration_data: Optional[pd.DataFrame] = None,
        start_year: int = 1990,
        seed: Optional[int] = None,
        rng: Optional[Generator] = None,
        *,
        use_numba: Optional[bool] = None,
        mixing_method: str = "binned",
        on_year_result: Optional[Callable[[Dict[str, Any]], None]] = None,
        scenario_params: Optional[Any] = None,
        calibration_file: str = "config/parameters_v4_calibrated.json",
        transition_year: int = 2024,
        transition_duration: int = 2
    ):
        self.params = params
        self.calibration_data = calibration_data
        self.population: List[Individual] = []
        self.agent_id_counter = 0
        self.start_year = int(start_year)
        self.current_year = float(self.start_year)
        self.rng: Generator = rng or default_rng(seed)
        self.use_numba: bool = NUMBA_AVAILABLE if use_numba is None else bool(use_numba)
        self.mixing_method: str = mixing_method if mixing_method in ("binned", "scan") else "binned"
        self._accel_seed: int = int(seed or 0)
        self._on_year_result = on_year_result
        self._stop_requested: bool = False
        self._pause_requested: bool = False
        self._run_total_years: float = 0.0

        # ParameterMapper for policy/history parameters
        self.mapper = ParameterMapper(
            calibration_file=calibration_file,
            scenario_params=scenario_params,
            transition_year=transition_year,
            transition_duration=transition_duration
        )

        # Disease parameters (biological constants)
        self.disease_params = {
            "viral_load": VIRAL_LOAD_PARAMETERS,
            "transmission": TRANSMISSION_PARAMETERS,
            "art_effects": ART_BIOLOGICAL_EFFECTS,
            "mtct": MTCT_BIOLOGICAL_RATES,
            "progression": DISEASE_PROGRESSION,
            "demographic": DEMOGRAPHIC_BIOLOGICAL,
            "partnership": PARTNERSHIP_PARAMETERS
        }

        # Annual counters
        self.deaths_hiv_this_year = 0
        self.deaths_natural_this_year = 0
        self.births_this_year = 0

        # Results storage - Enhanced with TRUE vs DETECTED values
        # TRUE values = actual epidemiological state (ground truth)
        # DETECTED values = what the health system observes (based on testing coverage)
        self.results = {
            # Basic demographics
            'year': [], 'total_population': [], 'susceptible': [],
            
            # TRUE HIV STATUS (ground truth - independent of testing)
            'true_hiv_positive': [],  # Total HIV+ (acute + chronic + aids)
            'true_acute': [],
            'true_chronic': [],
            'true_aids': [],
            'true_new_infections': [],  # Actual new infections this year
            'true_hiv_prevalence': [],  # Actual prevalence (may differ from detected)
            
            # DETECTED/DIAGNOSED (what health system knows based on testing coverage)
            'detected_hiv_positive': [],  # Those who tested positive
            'diagnosed': [],  # Those who know their status
            'tested_ever': [],  # Ever received HIV test
            'tested_this_year': [],  # Tested in last 12 months
            'detected_prevalence': [],  # Prevalence based on testing (may underestimate)
            
            # UNDETECTED GAP (key metrics for missed diagnoses)
            'undiagnosed_hiv_positive': [],  # HIV+ but unaware
            'undiagnosed_rate': [],  # Proportion of HIV+ who don't know status
            'missed_diagnoses': [],  # Could have been detected but weren't (due to coverage)
            
            # Treatment cascade (TRUE state vs KNOWN state)
            'true_on_art': [],  # Actually on ART
            'true_virally_suppressed': [],  # Actually suppressed
            'true_art_coverage': [],  # ART coverage of TRUE HIV+ population
            'detected_art_coverage': [],  # ART coverage of DETECTED HIV+ population
            
            # Deaths and births
            'deaths_hiv': [],
            'deaths_natural': [],
            'births': [],
            
            # Testing system performance
            'testing_coverage_achieved': [],  # Actual % tested
            'testing_capacity_used': [],  # % of test kits used
            'tests_performed_this_year': [],  # Total tests conducted
            'positive_tests_this_year': [],  # True positives found
            'false_negative_rate': [],  # % HIV+ who tested but got false negative
        }
        
        # Enhanced detailed results storage for age-sex stratified analysis
        self.detailed_results = {}

        self._initialize_population()
        logger.info(
            "Initialized model with %d individuals",
            len(self.population),
        )
    
    def _initialize_population(self):
        """Initialize population with demographic structure and geographic distribution."""
        # Get regional distribution for proper population allocation
        regional_probs = get_regional_assignment_probabilities()
        
        for _ in range(self.params.initial_population):
            # Age structure based on Cameroon demographics
            age = self._sample_age_structure()
            gender = self.rng.choice(['M', 'F'])
            
            # Individual constructor now handles region assignment internally
            individual = Individual(
                self.agent_id_counter, age, gender, self.params, rng=self.rng
            )
            self.agent_id_counter += 1
            
            # Assign urban/rural residence
            individual.residence = self._assign_residence()
            individual.last_test_year = None
            individual.viral_load_suppressed = False
            
            # Seed initial HIV infections - Enhanced for realistic starting prevalence
            # Apply regional HIV risk multiplier
            regional_hiv_prevalence = (
                self.params.initial_hiv_prevalence * 
                individual.regional_hiv_risk_multiplier
            )
            
            if age >= 15 and self.rng.random() < regional_hiv_prevalence:
                individual.hiv_status = "chronic"
                individual.infection_time = float(self.rng.uniform(0, 3))
                individual.viral_load = self._assign_initial_viral_load(individual)
                
                # Some individuals already in acute or AIDS stage
                stage_prob = self.rng.random()
                if stage_prob < 0.05:  # 5% in acute stage
                    individual.hiv_status = "acute"
                    individual.infection_time = float(self.rng.uniform(0, 0.25))
                    individual.viral_load = self.rng.lognormal(11, 1)  # Very high VL
                elif stage_prob > 0.85:  # 15% in AIDS stage
                    individual.hiv_status = "aids"
                    individual.infection_time = float(self.rng.uniform(5, 10))
                    individual.viral_load = self.rng.lognormal(10, 1)  # High VL
            
            self.population.append(individual)
    
    def _assign_residence(self) -> str:
        """Assign urban/rural residence based on Cameroon demographics."""
        # Cameroon: ~55% urban, 45% rural
        return self.rng.choice(['urban', 'rural'], p=[0.55, 0.45])
    
    def _assign_region(self) -> str:
        """Assign region with population-weighted probabilities."""
        regions = ['Centre', 'Sud', 'Est', 'Nord', 'Ouest', 'Adamaoua', 
                   'Nord-Ouest', 'Sud-Ouest', 'Extrême-Nord', 'Littoral']
        # Population weights approximating Cameroon distribution
        weights = [0.22, 0.08, 0.06, 0.12, 0.09, 0.05, 0.08, 0.07, 0.18, 0.05]
        return self.rng.choice(regions, p=weights)
    
    def _assign_initial_viral_load(self, individual: Individual) -> float:
        """Assign initial viral load based on HIV status and treatment."""
        if individual.hiv_status == "susceptible":
            return 0.0
        elif individual.hiv_status == "acute":
            return self.rng.lognormal(11, 1)  # Very high: ~60,000-200,000
        elif individual.on_art and individual.viral_load_suppressed:
            return self.rng.lognormal(2, 0.5)  # Suppressed: <1000
        else:
            return self.rng.lognormal(9, 1)   # Chronic untreated: ~8,000-20,000
    
    def _sample_age_structure(self) -> float:
        """Sample age from realistic Cameroon age structure."""
        # Simplified age distribution for Cameroon
        age_groups = [
            (0, 15, 0.45),   # Children
            (15, 30, 0.25),  # Young adults
            (30, 50, 0.20),  # Adults
            (50, 65, 0.08),  # Older adults
            (65, 85, 0.02)   # Elderly
        ]
        
        # Select age group
        probs = [group[2] for group in age_groups]
        selected_group = int(self.rng.choice(len(age_groups), p=probs))
        min_age, max_age, _ = age_groups[selected_group]
        
        return float(self.rng.uniform(min_age, max_age))
    
    def get_time_varying_transmission_rate(self, year: float) -> float:
        """
        Get year-specific transmission rate based on epidemic phase.
        
        Cameroon HIV epidemic had three distinct phases:
        - 1985-1990: Emergence phase (slow growth, R₀ ≈ 1.2-1.5)
        - 1990-2005: Growth phase (rapid expansion, R₀ ≈ 2.0-3.0)
        - 2005-2023: Decline phase (ART scale-up, R₀ < 1.0)
        
        This method adjusts transmission rate to match these dynamics.
        """
        base_rate = self.params.base_transmission_rate
        
        # Check if time-varying transmission is enabled
        if hasattr(self.params, 'use_time_varying_transmission') and not self.params.use_time_varying_transmission:
            return base_rate
        
        # Get phase multipliers from params or use defaults
        emergence_multiplier = getattr(self.params, 'emergence_phase_multiplier', 0.80)
        growth_multiplier = getattr(self.params, 'growth_phase_multiplier', 1.20)
        
        # Define phase boundaries
        emergence_end = getattr(self.params, 'emergence_phase_end', 1990)
        growth_end = getattr(self.params, 'growth_phase_end', 2005)
        
        if year < emergence_end:
            # Emergence phase (1985-1990): Lower transmission
            return base_rate * emergence_multiplier
        elif year < growth_end:
            # Growth phase (1990-2005): Higher transmission
            return base_rate * growth_multiplier
        else:
            # Decline phase (2005+): Base rate (ART suppression handled separately)
            # Natural decline in transmission due to awareness, behavior change
            decline_multiplier = getattr(self.params, 'decline_phase_multiplier', 1.0)
            return base_rate * decline_multiplier
    
    def run_simulation(self, years: int = 35, dt: float = 0.1) -> pd.DataFrame:
        """Run the complete HIV epidemic simulation."""
        logger.info(f"Starting simulation for {years} years")

        # Align start year with any externally set current_year prior to run
        if int(self.current_year) != self.start_year:
            self.start_year = int(self.current_year)

        # Record initial state before starting the simulation loop
        self._record_results(int(self.current_year))

        steps = int(years / dt)
        self._run_total_years = float(years)
        
        for step in range(steps):
            self.current_year = self.start_year + (step * dt)
            if self._stop_requested:
                logger.info("Stop requested; terminating simulation loop early")
                break
            # Pause handling
            while self._pause_requested and not self._stop_requested:
                time.sleep(0.05)
            
            # Update all individuals
            for individual in self.population[:]:
                if individual.alive:
                    individual.update(dt, self.current_year)
            
            # Population-level processes
            self._transmission_events(dt)
            self._mortality_events(dt)
            self._birth_events(dt)
            
            # Record results annually
            if step % int(1/dt) == 0:
                self._record_results(int(self.current_year))
                
            # Progress reporting
            progress_interval = max(1, steps // 10)
            if step % progress_interval == 0:
                progress = (step / steps) * 100
                logger.info(f"Simulation progress: {progress:.1f}%")
        
        logger.info("Simulation completed")
        return pd.DataFrame(self.results)

    def request_stop(self) -> None:
        """Request cooperative stop of the simulation loop."""
        self._stop_requested = True

    def request_pause(self) -> None:
        """Request pause; loop waits until resume or stop."""
        self._pause_requested = True

    def resume(self) -> None:
        """Resume from a paused state."""
        self._pause_requested = False
    
    def _poisson_counts(self, lams: np.ndarray) -> np.ndarray:
        """Vectorized Poisson sampling with optional Numba acceleration."""
        if lams.size == 0:
            return np.zeros(0, dtype=np.int64)
        if self.use_numba:
            # Derive a deterministic seed per call to keep runs stable-ish when seeded
            step_seed = (self._accel_seed + int((self.current_year - self.start_year) * 1000)) % (2**31 - 1)
            return poisson_counts_numba(lams.astype(np.float64), int(step_seed))
        return self.rng.poisson(lams)

    def _transmission_events(self, dt: float):
        if self.mixing_method == "binned":
            return self._transmission_events_binned(dt)
        else:
            return self._transmission_events_scan(dt)

    def _transmission_events_binned(self, dt: float):
        """Handle HIV transmission using age/risk binned partner selection."""
        susceptible = [
            p for p in self.population
            if p.alive and p.hiv_status == "susceptible" and p.age >= 15
        ]
        infected = [
            p for p in self.population
            if p.alive and p.hiv_status in ["acute", "chronic", "aids"]
        ]

        if not infected or not susceptible:
            return

        # Build infected pools by age bin and risk group for fast sampling
        bin_size = 5
        def age_bin(age: float) -> int:
            return int(age // bin_size)

        infected_bins: dict[tuple[int, str], list] = {}
        for partner in infected:
            key = (age_bin(partner.age), partner.risk_group)
            infected_bins.setdefault(key, []).append(partner)

        # Precompute neighbor bin offsets and weights for assortative mixing
        neighbor_offsets = [-2, -1, 0, 1, 2]
        neighbor_weights = np.array([0.2, 0.5, 1.0, 0.5, 0.2], dtype=float)
        neighbor_weights /= neighbor_weights.sum()

        risk_groups = list(self.params.risk_group_proportions.keys())

        # Vectorized contact draws
        lams = np.array([max(0.0, p.contacts_per_year * dt) for p in susceptible], dtype=float)
        contact_counts = self._poisson_counts(lams)

        for idx, person in enumerate(susceptible):
            base_bin = age_bin(person.age)
            contacts = int(contact_counts[idx])

            for _ in range(contacts):
                # Pick an age bin with assortative preference
                chosen_offset = int(self.rng.choice(neighbor_offsets, p=neighbor_weights))
                chosen_bin = base_bin + chosen_offset

                # Choose partner risk group (prefer same)
                same_rg_weight = 0.7
                other_weight = (1.0 - same_rg_weight) / max(1, len(risk_groups) - 1)
                rg_weights = []
                for rg in risk_groups:
                    rg_weights.append(same_rg_weight if rg == person.risk_group else other_weight)
                rg_weights = np.array(rg_weights, dtype=float)
                rg_weights /= rg_weights.sum()
                chosen_rg = str(self.rng.choice(risk_groups, p=rg_weights))

                pool = infected_bins.get((chosen_bin, chosen_rg))
                # Fallbacks if pool empty
                if not pool:
                    # try any risk group in chosen bin
                    merged = []
                    for rg in risk_groups:
                        merged.extend(infected_bins.get((chosen_bin, rg), ()))
                    pool = merged
                if not pool:
                    # global fallback
                    pool = infected

                partner = pool[int(self.rng.integers(len(pool)))] if pool else None
                if not partner:
                    continue

                # Get time-varying transmission rate
                time_varying_rate = self.get_time_varying_transmission_rate(self.current_year)
                transmission_prob = partner.get_infectivity(self.current_year, time_varying_rate)

                # Transmission probability modifiers
                risk_multiplier = person.params.risk_group_multipliers[person.risk_group]
                if (
                    self.params.funding_cut_scenario
                    and self.current_year >= self.params.funding_cut_year
                    and person.risk_group in ['medium', 'high']
                ):
                    # Increase risk by reducing prevention
                    risk_multiplier *= (1.0 + self.params.kp_prevention_cut_magnitude)

                transmission_prob *= risk_multiplier

                # Circumcision effect (males)
                if person.gender == 'M' and self.rng.random() < 0.3:  # 30% circumcised
                    transmission_prob *= 0.4

                # Condom use effect
                if self.rng.random() < self._get_condom_use_rate(self.current_year):
                    transmission_prob *= 0.15  # 85% efficacy

                if self.rng.random() < transmission_prob:
                    # PHASE 1 ENHANCEMENT: Track transmission details
                    person.hiv_status = "acute"
                    person.infection_time = 0.0
                    person.cd4_count = self.rng.normal(600, 100)
                    person.transmission_donor_id = partner.id
                    person.transmission_donor_stage = partner.hiv_status
                    person.transmission_donor_viral_load = partner.viral_load
                    person.transmission_year = self.current_year
                    break

    def _transmission_events_scan(self, dt: float):
        """Baseline scanning partner selection (pre-binning) for benchmarking."""
        susceptible = [
            p for p in self.population
            if p.alive and p.hiv_status == "susceptible" and p.age >= 15
        ]
        infected = [
            p for p in self.population
            if p.alive and p.hiv_status in ["acute", "chronic", "aids"]
        ]

        if not infected or not susceptible:
            return

        # Vectorized contact draws for susceptible
        lams = np.array([max(0.0, p.contacts_per_year * dt) for p in susceptible], dtype=float)
        contact_counts = self._poisson_counts(lams)

        for idx, person in enumerate(susceptible):
            contacts = int(contact_counts[idx])
            for _ in range(contacts):
                partner = self._select_partner(person, infected)
                if not partner:
                    continue
                
                # Get time-varying transmission rate
                time_varying_rate = self.get_time_varying_transmission_rate(self.current_year)
                transmission_prob = partner.get_infectivity(self.current_year, time_varying_rate)

                risk_multiplier = person.params.risk_group_multipliers[person.risk_group]
                if (
                    self.params.funding_cut_scenario
                    and self.current_year >= self.params.funding_cut_year
                    and person.risk_group in ['medium', 'high']
                ):
                    risk_multiplier *= (1.0 + self.params.kp_prevention_cut_magnitude)

                transmission_prob *= risk_multiplier

                if person.gender == 'M' and self.rng.random() < 0.3:
                    transmission_prob *= 0.4

                if self.rng.random() < self._get_condom_use_rate(self.current_year):
                    transmission_prob *= 0.15

                if self.rng.random() < transmission_prob:
                    # PHASE 1 ENHANCEMENT: Track transmission details
                    person.hiv_status = "acute"
                    person.infection_time = 0.0
                    person.cd4_count = self.rng.normal(600, 100)
                    person.transmission_donor_id = partner.id
                    person.transmission_donor_stage = partner.hiv_status
                    person.transmission_donor_viral_load = partner.viral_load
                    person.transmission_year = self.current_year
                    break
    
    def _select_partner(
        self,
        person: Individual,
        infected: List[Individual],
    ) -> Optional[Individual]:
        """Select sexual partner with assortative mixing."""
        if not infected:
            return None
        
        # Age assortative mixing
        age_preferences = []
        for partner in infected:
            age_diff = abs(person.age - partner.age)
            if age_diff <= 5:
                weight = 1.0
            elif age_diff <= 10:
                weight = 0.5
            elif age_diff <= 20:
                weight = 0.2
            else:
                weight = 0.05
            age_preferences.append(weight)
        
        # Normalize weights
        total_weight = sum(age_preferences)
        if total_weight == 0:
            return infected[int(self.rng.integers(len(infected)))]
        
        # Use numpy choice with indices
        probs = [w / total_weight for w in age_preferences]
        chosen_index = int(self.rng.choice(len(infected), p=probs))
        return infected[chosen_index]
    
    def _get_condom_use_rate(self, year: float) -> float:
        """Get condom use rate from ParameterMapper."""
        return self.mapper.get_condom_coverage(year)
    
    def _mortality_events(self, dt: float):
        """Handle mortality with age-specific natural rates and HIV-specific mortality."""
        
        for individual in self.population[:]:
            if not individual.alive:
                continue
            
            # Age-specific natural (non-HIV) mortality
            natural_death_rate = get_age_specific_mortality_rate(
                individual.age,
                self.current_year
            )
            
            # HIV-specific mortality (separate from natural)
            hiv_death_rate = 0.0
            
            if individual.hiv_status != "susceptible":
                # Base HIV mortality by disease stage
                stage_mortality = {
                    "acute": 0.02,      # 2% annual mortality in acute phase
                    "chronic": 0.05,    # 5% annual mortality in chronic phase
                    "aids": 0.30        # 30% annual mortality in AIDS stage
                }
                
                hiv_death_rate = stage_mortality.get(individual.hiv_status, 0.0)
                
                # ART dramatically reduces HIV mortality
                if individual.on_art:
                    if individual.viral_load_suppressed:
                        # 96% mortality reduction with viral suppression
                        hiv_death_rate *= 0.04
                    else:
                        # 70% reduction even without suppression
                        hiv_death_rate *= 0.30
                
                # CD4 count effect (lower CD4 = higher mortality)
                if hasattr(individual, 'cd4_count'):
                    if individual.cd4_count < 200:
                        hiv_death_rate *= 2.0  # Double mortality risk
                    elif individual.cd4_count < 350:
                        hiv_death_rate *= 1.5
            
            # Combined mortality rate
            total_death_rate = natural_death_rate + hiv_death_rate
            
            # Stochastic death event
            if self.rng.random() < total_death_rate * dt:
                individual.alive = False
                
                # Classify death cause (for tracking)
                if hiv_death_rate > natural_death_rate:
                    cause = "HIV"
                    self.deaths_hiv_this_year += 1
                else:
                    cause = "Natural"
                    self.deaths_natural_this_year += 1
                individual.death_cause = cause
                self.population.remove(individual)
    
    def _birth_events(self, dt: float):
        """Handle births with age-specific fertility and mother-to-child transmission."""
        # Group women by age brackets (5-year groups)
        fertile_age_groups = [15, 20, 25, 30, 35, 40, 45]
        
        total_births = 0
        
        for age_start in fertile_age_groups:
            age_end = age_start + 5
            
            # Get women in this age group
            women_in_group = [
                p for p in self.population
                if p.alive and p.gender == 'F' 
                and age_start <= p.age < age_end
            ]
            
            if not women_in_group:
                continue
            
            # Get age-specific fertility rate for this group
            # Use midpoint of age group for rate lookup
            mid_age = age_start + 2.5
            fertility_rate = get_age_specific_fertility_rate(mid_age, self.current_year)
            
            # Calculate expected births for this age group
            expected_births = len(women_in_group) * fertility_rate * dt
            
            # Sample actual births from Poisson distribution
            births_in_group = int(self.rng.poisson(expected_births))
            total_births += births_in_group
            
            # Create babies for this age group
            for _ in range(births_in_group):
                mother = women_in_group[int(self.rng.integers(len(women_in_group)))]
                gender = self.rng.choice(['M', 'F'])
                
                # Baby inherits mother's region
                baby = Individual(
                    self.agent_id_counter, 
                    0, 
                    gender, 
                    self.params, 
                    rng=self.rng,
                    region=mother.region
                )
                self.agent_id_counter += 1

                # Mother-to-child transmission with evolving PMTCT guidelines
                if mother.hiv_status in ["acute", "chronic", "aids"]:
                    # Enhanced PMTCT rates based on viral load and ART status
                    if self.current_year < 2004:
                        mtct_rate = 0.25  # Pre-PMTCT era
                    elif self.current_year < 2010:
                        if mother.on_art and mother.viral_load_suppressed:
                            mtct_rate = 0.02  # Suppressed on ART
                        elif mother.on_art:
                            mtct_rate = 0.05  # On ART but not suppressed
                        else:
                            mtct_rate = 0.15  # No treatment
                    elif self.current_year < 2016:
                        if mother.on_art and mother.viral_load_suppressed:
                            mtct_rate = 0.01  # Option B+
                        elif mother.on_art:
                            mtct_rate = 0.03
                        else:
                            mtct_rate = 0.12
                    else:
                        # "Treat All" era with improved PMTCT
                        if mother.on_art and mother.viral_load_suppressed:
                            mtct_rate = 0.005  # <1% transmission
                        elif mother.on_art:
                            mtct_rate = 0.02
                        else:
                            mtct_rate = 0.10

                    if self.rng.random() < mtct_rate:
                        baby.hiv_status = "chronic"
                        baby.infection_time = 0.0
                        baby.viral_load = self.rng.lognormal(8, 1)  # Moderate VL in infants

                self.population.append(baby)
        
        self.births_this_year += int(total_births)

    def _get_series_value(self, series_dict, year: float) -> float:
        """Interpolate from year->value mapping. Clamps outside range."""
        # Normalize to numeric years and values
        items = [(float(k), float(v)) for k, v in series_dict.items()]
        items.sort(key=lambda x: x[0])
        years = [y for y, _ in items]
        values = [v for _, v in items]
        if year <= years[0]:
            return values[0]
        if year >= years[-1]:
            return values[-1]
        return float(np.interp(year, years, values))

    def _get_series_value_with_projection(
        self,
        series_dict,
        year: float,
        *,
        bound_min: float | None = None,
        bound_max: float | None = None,
        le_series: dict | None = None,
        taper_horizon_years: float = 30.0,
        projection_method: str = "auto",
    ) -> float:
        """Get series value with linear projection beyond last year.

        - For year within range: linear interpolation.
        - For year beyond last: linear trend from last 10 years. If le_series
          is provided (for death rate), blend trend toward an LE-implied target
          using k/LE with a linear weight that reaches 1.0 over
          taper_horizon_years.
        - Clamp to [bound_min, bound_max] when provided.
        """
        # Normalize series
        items = [(float(k), float(v)) for k, v in series_dict.items()]
        items.sort(key=lambda x: x[0])
        years = np.array([y for y, _ in items], dtype=float)
        values = np.array([v for _, v in items], dtype=float)

        if year <= years[0]:
            val = float(values[0])
        elif year <= years[-1]:
            val = float(np.interp(year, years, values))
        else:
            # Handle projection methods beyond last observed year
            y1 = years[-1]
            v1 = values[-1]

            method = (projection_method or "auto").lower()
            if method == "flat":
                val = float(v1)
            else:
                # Linear trend from last window
                window = min(10, len(years) - 1) if len(years) > 1 else 1
                y0 = years[-window - 1] if len(years) > window else years[0]
                v0 = float(np.interp(y0, years, values))
                slope = (v1 - v0) / max(1e-9, (y1 - y0))
                trend = v1 + slope * (year - y1)

                use_le = (method in ("le_taper", "auto")) and le_series
                if use_le:
                    # Compute k from last known year and project LE
                    try:
                        le_items = [
                            (float(k), float(v)) for k, v in le_series.items()  # type: ignore[arg-type]
                        ]
                        le_items.sort(key=lambda x: x[0])
                        le_years = np.array([y for y, _ in le_items], dtype=float)
                        le_vals = np.array([v for _, v in le_items], dtype=float)
                        le_last = float(le_vals[-1])
                        k = max(1e-9, float(v1) * max(1e-6, le_last))
                        le_window = min(10, len(le_years) - 1) if len(le_years) > 1 else 1
                        le_y0 = le_years[-le_window - 1] if len(le_years) > le_window else le_years[0]
                        le_v0 = float(np.interp(le_y0, le_years, le_vals))
                        le_y1 = le_years[-1]
                        le_v1 = le_vals[-1]
                        le_slope = (le_v1 - le_v0) / max(1e-9, (le_y1 - le_y0))
                        le_proj = le_v1 + le_slope * (year - le_y1)
                        le_proj = float(np.clip(le_proj, 40.0, 85.0))
                        target = k / le_proj
                    except Exception:
                        target = trend

                    # Blend toward target over taper horizon
                    w = np.clip((year - y1) / max(1.0, taper_horizon_years), 0.0, 1.0)
                    val = float((1.0 - w) * trend + w * target)
                else:
                    val = float(trend)

        if bound_min is not None:
            val = max(bound_min, val)
        if bound_max is not None:
            val = min(bound_max, val)
        return float(val)

    def _get_natural_death_rate(self, year: float) -> float:
        """Get natural death rate from ParameterMapper."""
        return self.mapper.get_death_rate(year)

    def _get_birth_rate(self, year: float) -> float:
        """Get birth rate from ParameterMapper."""
        return self.mapper.get_birth_rate(year)
    
    def _record_results(self, year: int):
        """
        Record comprehensive simulation results separating TRUE vs DETECTED values.
        
        TRUE values = actual epidemiological state (ground truth)
        DETECTED values = what health system observes based on testing coverage
        """
        alive = [p for p in self.population if p.alive]
        total_pop = len(alive)

        # ==================== TRUE VALUES (GROUND TRUTH) ====================
        # These represent the actual epidemiological state, independent of testing
        
        susceptible = len([p for p in alive if p.hiv_status == "susceptible"])
        true_acute = len([p for p in alive if p.hiv_status == "acute"])
        true_chronic = len([p for p in alive if p.hiv_status == "chronic"])
        true_aids = len([p for p in alive if p.hiv_status == "aids"])
        
        true_hiv_positive = true_acute + true_chronic + true_aids
        true_hiv_prevalence = (true_hiv_positive / total_pop) if total_pop > 0 else 0

        # New infections (infected within last year) - TRUE count
        true_new_infections = len([
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"]
            and p.infection_time < 1.0
        ])

        # TRUE treatment status
        true_on_art = len([p for p in alive if p.on_art])
        true_virally_suppressed = len([
            p for p in alive 
            if p.on_art and hasattr(p, 'viral_load_suppressed') and p.viral_load_suppressed
        ])
        true_art_coverage = (true_on_art / true_hiv_positive) if true_hiv_positive > 0 else 0

        # ==================== DETECTED VALUES (HEALTH SYSTEM VIEW) ====================
        # These represent what the health system knows based on testing coverage
        
        # People who have ever been tested
        tested_ever = len([p for p in alive if hasattr(p, 'tested') and p.tested])
        
        # People tested in last 12 months
        tested_this_year = len([
            p for p in alive
            if hasattr(p, 'last_test_year') and p.last_test_year is not None
            and (year - p.last_test_year) <= 1.0
        ])
        
        # Diagnosed = knows HIV+ status (has been tested AND received positive result)
        diagnosed = len([p for p in alive if hasattr(p, 'diagnosed') and p.diagnosed])
        
        # Detected HIV+ = subset of diagnosed who are truly HIV+
        detected_hiv_positive = len([
            p for p in alive 
            if p.hiv_status in ["acute", "chronic", "aids"] 
            and hasattr(p, 'diagnosed') and p.diagnosed
        ])
        
        detected_prevalence = (detected_hiv_positive / total_pop) if total_pop > 0 else 0
        detected_art_coverage = (true_on_art / detected_hiv_positive) if detected_hiv_positive > 0 else 0

        # ==================== UNDETECTED GAP (MISSED DIAGNOSES) ====================
        # Critical metrics showing the gap between reality and what health system knows
        
        undiagnosed_hiv_positive = true_hiv_positive - detected_hiv_positive
        undiagnosed_rate = (undiagnosed_hiv_positive / true_hiv_positive) if true_hiv_positive > 0 else 0
        
        # Missed diagnoses = HIV+ people who could have been detected if testing coverage was 100%
        # This accounts for both:
        # 1. People never tested
        # 2. People tested but result not received/recorded
        hiv_positive_never_tested = len([
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"]
            and (not hasattr(p, 'tested') or not p.tested)
        ])
        
        hiv_positive_tested_not_diagnosed = len([
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"]
            and hasattr(p, 'tested') and p.tested
            and (not hasattr(p, 'diagnosed') or not p.diagnosed)
        ])
        
        missed_diagnoses = hiv_positive_never_tested + hiv_positive_tested_not_diagnosed

        # ==================== TESTING SYSTEM PERFORMANCE ====================
        
        # Actual testing coverage achieved
        testing_coverage_achieved = (tested_this_year / total_pop) if total_pop > 0 else 0
        
        # Tests performed and positive results (for yield calculation)
        tests_performed = tested_this_year
        positive_tests = detected_hiv_positive  # Approximation: newly diagnosed this year
        
        # False negative rate (testing failures)
        # HIV+ people tested but not diagnosed = testing system failures
        false_negative_rate = (hiv_positive_tested_not_diagnosed / true_hiv_positive) if true_hiv_positive > 0 else 0

        # ==================== STORE ALL RESULTS ====================
        
        self.results['year'].append(year)
        self.results['total_population'].append(total_pop)
        self.results['susceptible'].append(susceptible)
        
        # TRUE values (ground truth)
        self.results['true_hiv_positive'].append(true_hiv_positive)
        self.results['true_acute'].append(true_acute)
        self.results['true_chronic'].append(true_chronic)
        self.results['true_aids'].append(true_aids)
        self.results['true_new_infections'].append(true_new_infections)
        self.results['true_hiv_prevalence'].append(true_hiv_prevalence)
        self.results['true_on_art'].append(true_on_art)
        self.results['true_virally_suppressed'].append(true_virally_suppressed)
        self.results['true_art_coverage'].append(true_art_coverage)
        
        # DETECTED values (health system view)
        self.results['detected_hiv_positive'].append(detected_hiv_positive)
        self.results['diagnosed'].append(diagnosed)
        self.results['tested_ever'].append(tested_ever)
        self.results['tested_this_year'].append(tested_this_year)
        self.results['detected_prevalence'].append(detected_prevalence)
        self.results['detected_art_coverage'].append(detected_art_coverage)
        
        # UNDETECTED gap
        self.results['undiagnosed_hiv_positive'].append(undiagnosed_hiv_positive)
        self.results['undiagnosed_rate'].append(undiagnosed_rate)
        self.results['missed_diagnoses'].append(missed_diagnoses)
        
        # Testing system performance
        self.results['testing_coverage_achieved'].append(testing_coverage_achieved)
        self.results['testing_capacity_used'].append(testing_coverage_achieved)  # Same for now
        self.results['tests_performed_this_year'].append(tests_performed)
        self.results['positive_tests_this_year'].append(positive_tests)
        self.results['false_negative_rate'].append(false_negative_rate)
        
        # Deaths and births
        self.results['deaths_hiv'].append(self.deaths_hiv_this_year)
        self.results['deaths_natural'].append(self.deaths_natural_this_year)
        self.results['births'].append(self.births_this_year)

        # Record detailed age-sex stratified results
        self.detailed_results[year] = self._collect_detailed_indicators(alive)

        # Optional streaming callback per-year
        if self._on_year_result is not None:
            try:
                last_idx = len(self.results['year']) - 1
                row = {
                    k: self.results[k][last_idx]
                    for k in self.results
                }
                # Include progress if possible
                try:
                    if self._run_total_years > 0:
                        progress = (row['year'] - self.start_year) / self._run_total_years
                    else:
                        progress = None
                except Exception:
                    progress = None
                if progress is not None:
                    row['progress'] = max(0.0, min(1.0, float(progress)))
                self._on_year_result(row)
            except Exception:
                # Swallow callback errors to avoid impacting the core model
                pass

        # Reset annual counters
        self.deaths_hiv_this_year = 0
        self.deaths_natural_this_year = 0
        self.births_this_year = 0
    
    def _collect_detailed_indicators(self, alive: List[Individual]) -> Dict:
        """Collect comprehensive age-sex-region stratified HIV indicators."""
        
        # A) Core epidemiologic outputs
        age_sex_prevalence = self._calculate_age_sex_prevalence(alive)
        age_sex_incidence = self._calculate_age_sex_incidence(alive)
        adult_prevalence_aggregates = self._calculate_adult_prevalence_aggregates(alive)
        
        # B) HIV treatment cascade / 95-95-95
        treatment_cascade_95_95_95 = self._calculate_treatment_cascade_95_95_95(alive)
        
        # C) Testing & knowledge of status
        testing_coverage = self._calculate_testing_coverage(alive)
        
        # D) PMTCT indicators
        pmtct_indicators = self._calculate_pmtct_indicators(alive)
        
        # E) Population structure
        population_structure = self._calculate_population_structure(alive)
        
        # F) REGIONAL DATA - New comprehensive regional stratification
        regional_prevalence = self._calculate_regional_prevalence(alive)
        regional_cascade = self._calculate_regional_cascade(alive)
        regional_demographics = self._calculate_regional_demographics(alive)
        regional_age_sex_prevalence = self._calculate_regional_age_sex_prevalence(alive)
        
        # G) PHASE 1 ENHANCED DATA COLLECTION
        transmission_by_stage = self._calculate_transmission_by_stage(alive)
        transmission_by_viral_load = self._calculate_transmission_by_viral_load(alive)
        cascade_transitions = self._calculate_cascade_transitions(alive)
        late_diagnosis_indicators = self._calculate_late_diagnosis(alive)
        testing_modality_data = self._calculate_testing_modalities(alive)
        time_to_milestones = self._calculate_time_to_milestones(alive)
        
        # H) PHASE 2: TESTING & CO-INFECTIONS DATA COLLECTION
        testing_frequency = self._calculate_testing_frequency(alive)
        testing_yield = self._calculate_testing_yield(alive)
        knowledge_of_status = self._calculate_knowledge_of_status(alive)
        tb_hiv_coinfection = self._calculate_tb_hiv_coinfection(alive)
        hepatitis_coinfection = self._calculate_hepatitis_coinfection(alive)
        
        # I) PHASE 3: DEMOGRAPHICS & PREVENTION DATA COLLECTION
        life_years_dalys = self._calculate_life_years_dalys(alive)
        orphanhood = self._calculate_orphanhood(alive)
        aids_defining_illnesses = self._calculate_aids_defining_illnesses(alive)
        vmmc_coverage = self._calculate_vmmc_coverage(alive)
        prep_coverage = self._calculate_prep_coverage(alive)
        fertility_patterns = self._calculate_fertility_patterns(alive)
        
        return {
            'age_sex_prevalence': age_sex_prevalence,
            'age_sex_incidence': age_sex_incidence,
            'adult_prevalence_aggregates': adult_prevalence_aggregates,
            'treatment_cascade_95_95_95': treatment_cascade_95_95_95,
            'testing_coverage': testing_coverage,
            'pmtct_indicators': pmtct_indicators,
            'population_structure': population_structure,
            # Regional data
            'regional_prevalence': regional_prevalence,
            'regional_cascade': regional_cascade,
            'regional_demographics': regional_demographics,
            'regional_age_sex_prevalence': regional_age_sex_prevalence,
            # Phase 1 enhanced data
            'transmission_by_stage': transmission_by_stage,
            'transmission_by_viral_load': transmission_by_viral_load,
            'cascade_transitions': cascade_transitions,
            'late_diagnosis_indicators': late_diagnosis_indicators,
            'testing_modality_data': testing_modality_data,
            'time_to_milestones': time_to_milestones,
            # Phase 2: Testing & co-infections
            'testing_frequency': testing_frequency,
            'testing_yield': testing_yield,
            'knowledge_of_status': knowledge_of_status,
            'tb_hiv_coinfection': tb_hiv_coinfection,
            'hepatitis_coinfection': hepatitis_coinfection,
            # Phase 3: Demographics & prevention
            'life_years_dalys': life_years_dalys,
            'orphanhood': orphanhood,
            'aids_defining_illnesses': aids_defining_illnesses,
            'vmmc_coverage': vmmc_coverage,
            'prep_coverage': prep_coverage,
            'fertility_patterns': fertility_patterns
        }
    
    def _calculate_age_sex_prevalence(self, alive: List[Individual]) -> Dict:
        """Calculate HIV prevalence by 5-year age bands and sex (15-64)."""
        
        # Define 5-year age bands for adults (15-64)
        age_bands = [
            (15, 19), (20, 24), (25, 29), (30, 34), (35, 39),
            (40, 44), (45, 49), (50, 54), (55, 59), (60, 64)
        ]
        
        prevalence_data = {}
        
        for sex in ['M', 'F']:
            prevalence_data[sex] = {}
            
            for min_age, max_age in age_bands:
                # Get population in this age-sex group
                group_pop = [
                    p for p in alive
                    if p.gender == sex and min_age <= p.age <= max_age
                ]

                # Count HIV-positive individuals
                hiv_positive = [
                    p for p in group_pop
                    if p.hiv_status in ["acute", "chronic", "aids"]
                ]
                
                # Calculate prevalence percentage
                total = len(group_pop)
                positive = len(hiv_positive)
                prevalence_pct = (positive / total * 100) if total > 0 else 0
                
                band_name = f"{min_age}-{max_age}"
                prevalence_data[sex][band_name] = {
                    'prevalence_pct': prevalence_pct,
                    'hiv_positive': positive,
                    'total_population': total
                }
        
        return prevalence_data
    
    def _calculate_age_sex_incidence(self, alive: List[Individual]) -> Dict:
        """Calculate HIV incidence rates by age groups and sex."""
        
        # Get individuals infected in the last year
        recently_infected = [
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"]
            and p.infection_time <= 1.0
        ]
        
        age_groups = ['15-24', '25-34', '35-49', '15-49', '15-64']
        incidence_data = {}
        
        for age_group in age_groups:
            min_age, max_age = map(int, age_group.split('-'))
            incidence_data[age_group] = {}
            
            for sex in ['M', 'F', 'Total']:
                if sex == 'Total':
                    # All individuals in age group
                    group_pop = [
                        p for p in alive
                        if min_age <= p.age <= max_age
                    ]
                    new_infections = [
                        p for p in recently_infected
                        if min_age <= p.age <= max_age
                    ]
                else:
                    # Sex-specific groups
                    group_pop = [
                        p for p in alive
                        if p.gender == sex and min_age <= p.age <= max_age
                    ]
                    new_infections = [
                        p for p in recently_infected
                        if p.gender == sex and min_age <= p.age <= max_age
                    ]
                
                # Calculate annual incidence rate per 1000
                total_pop = len(group_pop)
                new_inf = len(new_infections)
                incidence_rate = (new_inf / total_pop * 1000) if total_pop > 0 else 0
                
                incidence_data[age_group][sex] = {
                    'incidence_per_1000': incidence_rate,
                    'new_infections': new_inf,
                    'total_population': total_pop
                }
        
        return incidence_data
    
    def _calculate_adult_prevalence_aggregates(self, alive: List[Individual]) -> Dict:
        """Calculate total adult prevalence aggregates."""
        
        age_groups = {
            '15-64': (15, 64),
            '15-49': (15, 49),
            '15-24': (15, 24)
        }
        
        aggregates = {}
        
        for group_name, (min_age, max_age) in age_groups.items():
            adults = [p for p in alive if min_age <= p.age <= max_age]
            hiv_positive = [p for p in adults if p.hiv_status in ["acute", "chronic", "aids"]]
            
            total = len(adults)
            positive = len(hiv_positive)
            prevalence_pct = (positive / total * 100) if total > 0 else 0
            
            aggregates[group_name] = {
                'prevalence_pct': prevalence_pct,
                'hiv_positive': positive,
                'total_population': total
            }
        
        return aggregates
    
    def _calculate_treatment_cascade_95_95_95(self, alive: List[Individual]) -> Dict:
        """Calculate 95-95-95 treatment cascade by age and sex."""
        
        age_groups = ['15-24', '25-34', '35-49', '15-49', '15-64']
        cascade_data = {}
        
        for age_group in age_groups:
            min_age, max_age = map(int, age_group.split('-'))
            cascade_data[age_group] = {}
            
            for sex in ['M', 'F', 'Total']:
                # Get PLHIV in this age-sex group
                if sex == 'Total':
                    plhiv = [
                        p for p in alive
                        if min_age <= p.age <= max_age
                        and p.hiv_status in ["acute", "chronic", "aids"]
                    ]
                else:
                    plhiv = [
                        p for p in alive
                        if p.gender == sex
                        and min_age <= p.age <= max_age
                        and p.hiv_status in ["acute", "chronic", "aids"]
                    ]
                
                total_plhiv = len(plhiv)
                diagnosed = len([p for p in plhiv if hasattr(p, 'diagnosed') and p.diagnosed])
                on_art = len([p for p in plhiv if p.on_art])
                
                # Viral suppression - use viral load < 1000 copies/mL
                virally_suppressed = len([
                    p for p in plhiv
                    if p.on_art and hasattr(p, 'viral_load') and p.viral_load < 1000
                ])
                
                cascade_data[age_group][sex] = {
                    'total_plhiv': total_plhiv,
                    'first_95_pct': (diagnosed / total_plhiv * 100) if total_plhiv > 0 else 0,
                    'second_95_pct': (on_art / diagnosed * 100) if diagnosed > 0 else 0,
                    'third_95_pct': (virally_suppressed / on_art * 100) if on_art > 0 else 0,
                    'diagnosed_count': diagnosed,
                    'on_art_count': on_art,
                    'suppressed_count': virally_suppressed
                }
        
        return cascade_data
    
    def _calculate_testing_coverage(self, alive: List[Individual]) -> Dict:
        """Calculate testing coverage indicators."""
        
        # Adults 15-64
        adults = [p for p in alive if 15 <= p.age <= 64]
        
        # Ever tested
        ever_tested = len([p for p in adults if hasattr(p, 'tested') and p.tested])
        
        # Tested in last 12 months
        tested_last_12m = len([
            p for p in adults
            if hasattr(p, 'last_test_year') and p.last_test_year
            and (self.current_year - p.last_test_year) <= 1.0
        ])
        
        total_adults = len(adults)
        
        testing_data = {
            'ever_tested_pct': (ever_tested / total_adults * 100) if total_adults > 0 else 0,
            'tested_last_12m_pct': (tested_last_12m / total_adults * 100) if total_adults > 0 else 0,
            'ever_tested_count': ever_tested,
            'tested_last_12m_count': tested_last_12m,
            'total_adults': total_adults
        }
        
        # By residence type if available
        if hasattr(adults[0], 'residence') if adults else False:
            testing_data['by_residence'] = {}
            for residence in ['urban', 'rural']:
                residence_adults = [p for p in adults if hasattr(p, 'residence') and p.residence == residence]
                residence_tested = len([p for p in residence_adults if hasattr(p, 'tested') and p.tested])
                
                testing_data['by_residence'][residence] = {
                    'ever_tested_pct': (residence_tested / len(residence_adults) * 100) if residence_adults else 0,
                    'total_population': len(residence_adults)
                }
        
        return testing_data
    
    def _calculate_pmtct_indicators(self, alive: List[Individual]) -> Dict:
        """Calculate PMTCT indicators."""
        
        # Women of reproductive age (15-49)
        women_repro = [p for p in alive if p.gender == 'F' and 15 <= p.age <= 49]
        
        # HIV-positive women of reproductive age
        hiv_pos_women = [p for p in women_repro if p.hiv_status in ["acute", "chronic", "aids"]]
        
        # Simplified PMTCT calculation based on current year and ART status
        pmtct_coverage = 0
        if hiv_pos_women:
            women_on_art = len([p for p in hiv_pos_women if p.on_art])
            pmtct_coverage = (women_on_art / len(hiv_pos_women) * 100)
        
        # Estimate transmission rates based on current year and treatment
        if self.current_year < 2004:
            baseline_mtct_rate = 25.0  # 25% without intervention
        elif self.current_year < 2010:
            baseline_mtct_rate = 15.0  # Improved with basic PMTCT
        elif self.current_year < 2016:
            baseline_mtct_rate = 8.0   # Option B+ era
        else:
            baseline_mtct_rate = 3.0   # "Treat All" era
        
        return {
            'women_repro_age': len(women_repro),
            'hiv_pos_women_repro': len(hiv_pos_women),
            'pmtct_coverage_pct': pmtct_coverage,
            'estimated_mtct_rate_pct': baseline_mtct_rate,
            'women_on_art': len([p for p in hiv_pos_women if p.on_art]) if hiv_pos_women else 0
        }
    
    def _calculate_population_structure(self, alive: List[Individual]) -> Dict:
        """Calculate population structure for normalization."""
        
        # Age-sex composition
        age_sex_structure = {}
        total_pop = len(alive)
        
        # 5-year age bands
        age_bands = [(i, i+4) for i in range(0, 85, 5)]
        
        for sex in ['M', 'F']:
            age_sex_structure[sex] = {}
            for min_age, max_age in age_bands:
                count = len([
                    p for p in alive 
                    if p.gender == sex and min_age <= p.age <= max_age
                ])
                age_sex_structure[sex][f"{min_age}-{max_age}"] = {
                    'count': count,
                    'percentage': (count / total_pop * 100) if total_pop > 0 else 0
                }
        
        # Urban-rural composition if available
        residence_structure = {}
        if hasattr(alive[0], 'residence') if alive else False:
            for residence in ['urban', 'rural']:
                count = len([p for p in alive if hasattr(p, 'residence') and p.residence == residence])
                residence_structure[residence] = {
                    'count': count,
                    'percentage': (count / total_pop * 100) if total_pop > 0 else 0
                }
        
        return {
            'total_population': total_pop,
            'age_sex_structure': age_sex_structure,
            'residence_structure': residence_structure
        }
    
    def _calculate_regional_prevalence(self, alive: List[Individual]) -> Dict:
        """Calculate HIV prevalence by region."""
        from hivec_cm.core.demographic_parameters import REGIONAL_DISTRIBUTION
        
        regional_data = {}
        
        for region in REGIONAL_DISTRIBUTION.keys():
            # Get population in this region
            region_pop = [p for p in alive if hasattr(p, 'region') and p.region == region]
            
            if not region_pop:
                continue
            
            # Count HIV+ individuals
            hiv_positive = [p for p in region_pop if p.hiv_status in ["acute", "chronic", "aids"]]
            
            # Age-specific prevalence (15-49)
            adults_15_49 = [p for p in region_pop if 15 <= p.age <= 49]
            hiv_pos_15_49 = [p for p in adults_15_49 if p.hiv_status in ["acute", "chronic", "aids"]]
            
            # Gender-specific
            males = [p for p in region_pop if p.gender == 'M']
            females = [p for p in region_pop if p.gender == 'F']
            hiv_pos_males = [p for p in males if p.hiv_status in ["acute", "chronic", "aids"]]
            hiv_pos_females = [p for p in females if p.hiv_status in ["acute", "chronic", "aids"]]
            
            regional_data[region] = {
                'total_population': len(region_pop),
                'hiv_positive': len(hiv_positive),
                'prevalence_all_ages_pct': (len(hiv_positive) / len(region_pop) * 100) if region_pop else 0,
                'prevalence_15_49_pct': (len(hiv_pos_15_49) / len(adults_15_49) * 100) if adults_15_49 else 0,
                'prevalence_male_pct': (len(hiv_pos_males) / len(males) * 100) if males else 0,
                'prevalence_female_pct': (len(hiv_pos_females) / len(females) * 100) if females else 0,
                'male_count': len(males),
                'female_count': len(females)
            }
        
        return regional_data
    
    def _calculate_regional_cascade(self, alive: List[Individual]) -> Dict:
        """Calculate 95-95-95 cascade by region."""
        from hivec_cm.core.demographic_parameters import REGIONAL_DISTRIBUTION
        
        regional_cascade = {}
        
        for region in REGIONAL_DISTRIBUTION.keys():
            # Get PLHIV in this region
            plhiv = [
                p for p in alive
                if hasattr(p, 'region') and p.region == region
                and p.hiv_status in ["acute", "chronic", "aids"]
            ]
            
            if not plhiv:
                continue
            
            total_plhiv = len(plhiv)
            diagnosed = len([p for p in plhiv if hasattr(p, 'diagnosed') and p.diagnosed])
            on_art = len([p for p in plhiv if p.on_art])
            suppressed = len([
                p for p in plhiv
                if p.on_art and hasattr(p, 'viral_load') and p.viral_load < 1000
            ])
            
            regional_cascade[region] = {
                'total_plhiv': total_plhiv,
                'diagnosed': diagnosed,
                'on_art': on_art,
                'suppressed': suppressed,
                'first_95_pct': (diagnosed / total_plhiv * 100) if total_plhiv > 0 else 0,
                'second_95_pct': (on_art / diagnosed * 100) if diagnosed > 0 else 0,
                'third_95_pct': (suppressed / on_art * 100) if on_art > 0 else 0
            }
        
        return regional_cascade
    
    def _calculate_regional_demographics(self, alive: List[Individual]) -> Dict:
        """Calculate demographic indicators by region."""
        from hivec_cm.core.demographic_parameters import REGIONAL_DISTRIBUTION
        
        regional_demog = {}
        
        for region in REGIONAL_DISTRIBUTION.keys():
            region_pop = [p for p in alive if hasattr(p, 'region') and p.region == region]
            
            if not region_pop:
                continue
            
            # Age structure
            children = len([p for p in region_pop if p.age < 15])
            youth = len([p for p in region_pop if 15 <= p.age < 25])
            adults = len([p for p in region_pop if 25 <= p.age < 65])
            elderly = len([p for p in region_pop if p.age >= 65])
            
            # Gender ratio
            males = len([p for p in region_pop if p.gender == 'M'])
            females = len([p for p in region_pop if p.gender == 'F'])
            
            total = len(region_pop)
            
            regional_demog[region] = {
                'total_population': total,
                'children_0_14': children,
                'youth_15_24': youth,
                'adults_25_64': adults,
                'elderly_65plus': elderly,
                'males': males,
                'females': females,
                'children_pct': (children / total * 100) if total > 0 else 0,
                'youth_pct': (youth / total * 100) if total > 0 else 0,
                'adults_pct': (adults / total * 100) if total > 0 else 0,
                'elderly_pct': (elderly / total * 100) if total > 0 else 0,
                'sex_ratio': (males / females * 100) if females > 0 else 0
            }
        
        return regional_demog
    
    def _calculate_regional_age_sex_prevalence(self, alive: List[Individual]) -> Dict:
        """Calculate HIV prevalence by region, age, and sex."""
        from hivec_cm.core.demographic_parameters import REGIONAL_DISTRIBUTION
        
        regional_age_sex = {}
        
        # Key age groups for analysis
        age_groups = ['15-24', '25-34', '35-49', '15-49']
        
        for region in REGIONAL_DISTRIBUTION.keys():
            regional_age_sex[region] = {}
            
            for age_group in age_groups:
                min_age, max_age = map(int, age_group.split('-'))
                regional_age_sex[region][age_group] = {}
                
                for sex in ['M', 'F', 'Total']:
                    if sex == 'Total':
                        group_pop = [
                            p for p in alive
                            if hasattr(p, 'region') and p.region == region
                            and min_age <= p.age <= max_age
                        ]
                    else:
                        group_pop = [
                            p for p in alive
                            if hasattr(p, 'region') and p.region == region
                            and p.gender == sex
                            and min_age <= p.age <= max_age
                        ]
                    
                    hiv_pos = [p for p in group_pop if p.hiv_status in ["acute", "chronic", "aids"]]
                    
                    total = len(group_pop)
                    positive = len(hiv_pos)
                    
                    regional_age_sex[region][age_group][sex] = {
                        'total_population': total,
                        'hiv_positive': positive,
                        'prevalence_pct': (positive / total * 100) if total > 0 else 0
                    }
        
        return regional_age_sex

    # ===== PHASE 1 ENHANCED DATA COLLECTION METHODS =====
    
    def _calculate_transmission_by_stage(self, alive: List[Individual]) -> Dict:
        """Track transmissions by donor's HIV stage (PHASE 1 ENHANCEMENT)."""
        # Count recent infections (this year) by donor stage
        recent_infections = [
            p for p in alive
            if (hasattr(p, 'transmission_year') and
                p.transmission_year is not None and
                abs(p.transmission_year - self.current_year) < 1.0)
        ]
        
        by_stage = {
            'acute': 0,
            'chronic': 0,
            'aids': 0,
            'undiagnosed': 0,
            'diagnosed_not_on_art': 0,
            'on_art_non_suppressed': 0,
            'unknown': 0
        }
        
        for person in recent_infections:
            if hasattr(person, 'transmission_donor_stage') and person.transmission_donor_stage:
                stage = person.transmission_donor_stage
                by_stage[stage] = by_stage.get(stage, 0) + 1
            else:
                by_stage['unknown'] += 1
        
        by_stage['total_new_infections'] = len(recent_infections)
        
        return by_stage
    
    def _calculate_transmission_by_viral_load(self, alive: List[Individual]) -> Dict:
        """Track transmissions by donor's viral load (PHASE 1 ENHANCEMENT)."""
        recent_infections = [
            p for p in alive
            if (hasattr(p, 'transmission_year') and
                p.transmission_year is not None and
                abs(p.transmission_year - self.current_year) < 1.0)
        ]
        
        vl_categories = {
            'vl_under_1000': 0,  # Suppressed (shouldn't transmit)
            'vl_1000_10000': 0,  # Low VL
            'vl_10000_100000': 0,  # Moderate VL
            'vl_over_100000': 0,  # High VL
            'vl_unknown': 0
        }
        
        for person in recent_infections:
            if hasattr(person, 'transmission_donor_viral_load') and person.transmission_donor_viral_load:
                vl = person.transmission_donor_viral_load
                if vl < 1000:
                    vl_categories['vl_under_1000'] += 1
                elif vl < 10000:
                    vl_categories['vl_1000_10000'] += 1
                elif vl < 100000:
                    vl_categories['vl_10000_100000'] += 1
                else:
                    vl_categories['vl_over_100000'] += 1
            else:
                vl_categories['vl_unknown'] += 1
        
        vl_categories['total_transmissions'] = len(recent_infections)
        
        return vl_categories
    
    def _calculate_cascade_transitions(self, alive: List[Individual]) -> Dict:
        """Track movement through HIV care cascade (PHASE 1 ENHANCEMENT)."""
        hiv_positive = [
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"]
        ]
        
        # Newly diagnosed this year
        newly_diagnosed = len([
            p for p in hiv_positive
            if (hasattr(p, 'diagnosis_year') and
                p.diagnosis_year is not None and
                abs(p.diagnosis_year - self.current_year) < 1.0)
        ])
        
        # Diagnosed and linked to care
        diagnosed_linked = len([
            p for p in hiv_positive
            if p.diagnosed and hasattr(p, 'cascade_linkage_year') and
            p.cascade_linkage_year is not None
        ])
        
        # Initiated ART this year
        art_initiations = len([
            p for p in hiv_positive
            if p.on_art and hasattr(p, 'art_start_time') and
            abs(self.current_year - (p.infection_time + p.art_start_time)) < 1.0
        ])
        
        # Achieved viral suppression
        achieved_suppression = len([
            p for p in hiv_positive
            if p.on_art and hasattr(p, 'viral_load_suppressed') and
            p.viral_load_suppressed
        ])
        
        # Lost to follow-up (LTFU) - simplified: on ART but poor adherence
        ltfu_count = len([
            p for p in hiv_positive
            if hasattr(p, 'ltfu_date') and p.ltfu_date is not None
        ])
        
        # Returned to care after LTFU
        returned_to_care = len([
            p for p in hiv_positive
            if hasattr(p, 'return_to_care_date') and p.return_to_care_date is not None
        ])
        
        return {
            'total_hiv_positive': len(hiv_positive),
            'newly_diagnosed': newly_diagnosed,
            'diagnosed_linked_to_care': diagnosed_linked,
            'art_initiations_this_year': art_initiations,
            'achieved_suppression': achieved_suppression,
            'ltfu_count': ltfu_count,
            'returned_to_care': returned_to_care,
            # Cascade percentages
            'pct_diagnosed': (len([p for p in hiv_positive if p.diagnosed]) / len(hiv_positive) * 100)
                if hiv_positive else 0,
            'pct_on_art': (len([p for p in hiv_positive if p.on_art]) / len(hiv_positive) * 100)
                if hiv_positive else 0
        }
    
    def _calculate_late_diagnosis(self, alive: List[Individual]) -> Dict:
        """Track CD4 count at diagnosis (late diagnosis) (PHASE 1 ENHANCEMENT)."""
        # Get all diagnosed individuals
        diagnosed = [
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"] and p.diagnosed
        ]
        
        cd4_categories = {
            'diagnosed_cd4_under_200': 0,  # Late presenters
            'diagnosed_cd4_200_350': 0,
            'diagnosed_cd4_350_500': 0,
            'diagnosed_cd4_over_500': 0,
            'cd4_unknown': 0
        }
        
        cd4_values = []
        
        for person in diagnosed:
            if hasattr(person, 'cd4_at_diagnosis') and person.cd4_at_diagnosis is not None:
                cd4 = person.cd4_at_diagnosis
                cd4_values.append(cd4)
                
                if cd4 < 200:
                    cd4_categories['diagnosed_cd4_under_200'] += 1
                elif cd4 < 350:
                    cd4_categories['diagnosed_cd4_200_350'] += 1
                elif cd4 < 500:
                    cd4_categories['diagnosed_cd4_350_500'] += 1
                else:
                    cd4_categories['diagnosed_cd4_over_500'] += 1
            else:
                cd4_categories['cd4_unknown'] += 1
        
        cd4_categories['total_diagnosed'] = len(diagnosed)
        cd4_categories['median_cd4_at_diagnosis'] = float(np.median(cd4_values)) if cd4_values else 0
        cd4_categories['proportion_late_diagnosis'] = (
            (cd4_categories['diagnosed_cd4_under_200'] + cd4_categories['diagnosed_cd4_200_350']) /
            len(diagnosed) if diagnosed else 0
        )
        
        return cd4_categories
    
    def _calculate_testing_modalities(self, alive: List[Individual]) -> Dict:
        """Track testing modality distribution (PHASE 1 ENHANCEMENT)."""
        # Get all who have been tested
        tested = [
            p for p in alive
            if hasattr(p, 'ever_tested') and p.ever_tested
        ]
        
        modality_counts = {
            'facility_based': 0,
            'community_based': 0,
            'antenatal': 0,
            'self_test': 0,
            'index_testing': 0,
            'unknown': 0
        }
        
        # Count by most recent testing modality
        for person in tested:
            if hasattr(person, 'testing_modality_last') and person.testing_modality_last:
                modality = person.testing_modality_last
                if modality in modality_counts:
                    modality_counts[modality] += 1
                else:
                    modality_counts['unknown'] += 1
            else:
                modality_counts['unknown'] += 1
        
        modality_counts['total_tested'] = len(tested)
        
        # Calculate positivity by modality (if tested this year)
        recent_tests = [
            p for p in tested
            if hasattr(p, 'last_test_year') and p.last_test_year is not None and
            abs(p.last_test_year - self.current_year) < 1.0
        ]
        
        modality_counts['tests_this_year'] = len(recent_tests)
        
        return modality_counts
    
    def _calculate_time_to_milestones(self, alive: List[Individual]) -> Dict:
        """Calculate time intervals between cascade stages (PHASE 1 ENHANCEMENT)."""
        hiv_positive = [
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"]
        ]
        
        # Infection to diagnosis time
        infection_to_diagnosis = []
        for person in hiv_positive:
            if (person.diagnosed and
                    hasattr(person, 'diagnosis_year') and
                    hasattr(person, 'transmission_year') and
                    person.diagnosis_year and person.transmission_year):
                time_diff = (person.diagnosis_year - person.transmission_year) * 365  # Convert to days
                if time_diff >= 0:  # Sanity check
                    infection_to_diagnosis.append(time_diff)
        
        # Diagnosis to ART time
        diagnosis_to_art = []
        for person in hiv_positive:
            if (person.on_art and
                    hasattr(person, 'diagnosis_year') and
                    person.diagnosis_year and
                    hasattr(person, 'art_start_time')):
                if (hasattr(person, 'transmission_year') and
                        person.transmission_year is not None):
                    art_year = person.transmission_year + person.art_start_time
                else:
                    art_year = None
                if art_year and person.diagnosis_year:
                    time_diff = (art_year - person.diagnosis_year) * 365
                    if time_diff >= 0:
                        diagnosis_to_art.append(time_diff)
        
        return {
            'median_infection_to_diagnosis_days': float(np.median(infection_to_diagnosis))
                if infection_to_diagnosis else 0,
            'p25_infection_to_diagnosis': float(np.percentile(infection_to_diagnosis, 25))
                if infection_to_diagnosis else 0,
            'p75_infection_to_diagnosis': float(np.percentile(infection_to_diagnosis, 75))
                if infection_to_diagnosis else 0,
            'n_infection_to_diagnosis': len(infection_to_diagnosis),
            
            'median_diagnosis_to_art_days': float(np.median(diagnosis_to_art))
                if diagnosis_to_art else 0,
            'p25_diagnosis_to_art': float(np.percentile(diagnosis_to_art, 25))
                if diagnosis_to_art else 0,
            'p75_diagnosis_to_art': float(np.percentile(diagnosis_to_art, 75))
                if diagnosis_to_art else 0,
            'n_diagnosis_to_art': len(diagnosis_to_art)
        }

    # ===== PHASE 2: TESTING & CO-INFECTIONS DATA COLLECTION METHODS =====
    
    def _calculate_testing_frequency(self, alive: List[Individual]) -> Dict:
        """Track testing frequency and repeat testing (PHASE 2)."""
        adults = [p for p in alive if p.age >= 15]
        
        # First-time vs repeat testers
        first_time_testers = len([
            p for p in adults
            if hasattr(p, 'total_tests_lifetime') and p.total_tests_lifetime == 1
        ])
        
        repeat_testers = len([
            p for p in adults
            if hasattr(p, 'total_tests_lifetime') and p.total_tests_lifetime > 1
        ])
        
        # Tested once lifetime
        tested_once = len([
            p for p in adults
            if hasattr(p, 'total_tests_lifetime') and p.total_tests_lifetime == 1
        ])
        
        # Tested annually (more than once and recent test)
        tested_annually = len([
            p for p in adults
            if hasattr(p, 'tests_last_12_months') and p.tests_last_12_months >= 1
        ])
        
        # Tested multiple times per year
        tested_multiple_year = len([
            p for p in adults
            if hasattr(p, 'tests_last_12_months') and p.tests_last_12_months > 1
        ])
        
        # Calculate median time between tests (simplified)
        tests_per_person = []
        for person in adults:
            if hasattr(person, 'total_tests_lifetime') and person.total_tests_lifetime > 0:
                tests_per_person.append(person.total_tests_lifetime)
        
        return {
            'total_adults': len(adults),
            'first_time_testers': first_time_testers,
            'repeat_testers': repeat_testers,
            'tested_once_lifetime': tested_once,
            'tested_annually': tested_annually,
            'tested_multiple_per_year': tested_multiple_year,
            'median_tests_per_person': float(np.median(tests_per_person))
                if tests_per_person else 0,
            'mean_tests_per_person': float(np.mean(tests_per_person))
                if tests_per_person else 0
        }
    
    def _calculate_testing_yield(self, alive: List[Individual]) -> Dict:
        """Calculate positivity rate by testing strategy (PHASE 2)."""
        # Get people tested recently (this year)
        recent_tests = [
            p for p in alive
            if hasattr(p, 'last_test_year') and p.last_test_year is not None and
            abs(p.last_test_year - self.current_year) < 1.0
        ]
        
        # Count positives among recent tests
        positives = len([
            p for p in recent_tests
            if p.hiv_status in ['acute', 'chronic', 'aids']
        ])
        
        # By risk group
        yield_by_risk = {}
        for risk_group in ['low', 'medium', 'high']:
            risk_tests = [p for p in recent_tests if p.risk_group == risk_group]
            risk_positives = [p for p in risk_tests
                            if p.hiv_status in ['acute', 'chronic', 'aids']]
            
            yield_by_risk[risk_group] = {
                'tests': len(risk_tests),
                'positives': len(risk_positives),
                'yield_pct': (len(risk_positives) / len(risk_tests) * 100)
                    if risk_tests else 0
            }
        
        # By age-sex
        yield_by_age_sex = {}
        age_groups = [(15, 24), (25, 34), (35, 49)]
        
        for min_age, max_age in age_groups:
            age_label = f"{min_age}-{max_age}"
            for sex in ['M', 'F']:
                group_tests = [
                    p for p in recent_tests
                    if p.gender == sex and min_age <= p.age <= max_age
                ]
                group_positives = [
                    p for p in group_tests
                    if p.hiv_status in ['acute', 'chronic', 'aids']
                ]
                
                yield_by_age_sex[f"{age_label}_{sex}"] = {
                    'tests': len(group_tests),
                    'positives': len(group_positives),
                    'yield_pct': (len(group_positives) / len(group_tests) * 100)
                        if group_tests else 0
                }
        
        return {
            'tests_performed_this_year': len(recent_tests),
            'positive_results': positives,
            'overall_yield_pct': (positives / len(recent_tests) * 100)
                if recent_tests else 0,
            'by_risk_group': yield_by_risk,
            'by_age_sex': yield_by_age_sex
        }
    
    def _calculate_knowledge_of_status(self, alive: List[Individual]) -> Dict:
        """Track awareness of HIV status (PHASE 2)."""
        hiv_positive = [
            p for p in alive
            if p.hiv_status in ['acute', 'chronic', 'aids']
        ]
        
        # Aware of status (diagnosed)
        aware = [p for p in hiv_positive if p.diagnosed]
        
        # Unaware of status
        unaware = [p for p in hiv_positive if not p.diagnosed]
        
        # By age group
        age_groups = [(15, 24), (25, 49)]
        awareness_by_age = {}
        
        for min_age, max_age in age_groups:
            age_label = f"{min_age}-{max_age}"
            age_plhiv = [p for p in hiv_positive
                        if min_age <= p.age <= max_age]
            age_aware = [p for p in age_plhiv if p.diagnosed]
            
            awareness_by_age[age_label] = {
                'total_plhiv': len(age_plhiv),
                'aware': len(age_aware),
                'unaware': len(age_plhiv) - len(age_aware),
                'proportion_aware': (len(age_aware) / len(age_plhiv))
                    if age_plhiv else 0
            }
        
        # Undiagnosed with high VL (high transmission risk)
        undiagnosed_high_vl = len([
            p for p in unaware
            if hasattr(p, 'viral_load') and p.viral_load > 10000
        ])
        
        # Time from infection to diagnosis
        time_to_diagnosis = []
        for person in aware:
            if (hasattr(person, 'diagnosis_year') and
                    hasattr(person, 'transmission_year') and
                    person.diagnosis_year and person.transmission_year):
                time_diff = person.diagnosis_year - person.transmission_year
                if time_diff >= 0:
                    time_to_diagnosis.append(time_diff)
        
        return {
            'total_plhiv': len(hiv_positive),
            'aware_of_status': len(aware),
            'unaware_of_status': len(unaware),
            'proportion_aware': (len(aware) / len(hiv_positive))
                if hiv_positive else 0,
            'undiagnosed_high_vl': undiagnosed_high_vl,
            'median_years_to_diagnosis': float(np.median(time_to_diagnosis))
                if time_to_diagnosis else 0,
            'by_age_group': awareness_by_age
        }
    
    def _calculate_tb_hiv_coinfection(self, alive: List[Individual]) -> Dict:
        """Track TB-HIV co-infection indicators (PHASE 2)."""
        hiv_positive = [
            p for p in alive
            if p.hiv_status in ['acute', 'chronic', 'aids']
        ]
        
        # PLHIV with active TB
        plhiv_with_tb = len([
            p for p in hiv_positive
            if hasattr(p, 'tb_status') and p.tb_status == 'active_tb'
        ])
        
        # PLHIV on IPT (Isoniazid Preventive Therapy)
        plhiv_on_ipt = len([
            p for p in hiv_positive
            if hasattr(p, 'on_ipt') and p.on_ipt
        ])
        
        # TB-HIV deaths (simplified - would need cause tracking)
        # For now, estimate based on TB status at death
        
        # PLHIV screened for TB this year
        plhiv_screened_tb = len([
            p for p in hiv_positive
            if hasattr(p, 'tb_screened_this_year') and p.tb_screened_this_year
        ])
        
        # PLHIV on ART with TB
        plhiv_on_art_with_tb = len([
            p for p in hiv_positive
            if p.on_art and hasattr(p, 'tb_status') and p.tb_status == 'active_tb'
        ])
        
        # IPT coverage among eligible PLHIV
        eligible_for_ipt = len([
            p for p in hiv_positive
            if hasattr(p, 'tb_status') and p.tb_status != 'active_tb'
        ])
        
        ipt_coverage = (plhiv_on_ipt / eligible_for_ipt) if eligible_for_ipt > 0 else 0
        
        return {
            'total_plhiv': len(hiv_positive),
            'plhiv_with_tb': plhiv_with_tb,
            'plhiv_on_ipt': plhiv_on_ipt,
            'plhiv_screened_tb_this_year': plhiv_screened_tb,
            'plhiv_on_art_with_tb': plhiv_on_art_with_tb,
            'tb_hiv_coinfection_rate': (plhiv_with_tb / len(hiv_positive))
                if hiv_positive else 0,
            'ipt_coverage_pct': ipt_coverage * 100,
            'screening_coverage_pct': (plhiv_screened_tb / len(hiv_positive) * 100)
                if hiv_positive else 0
        }
    
    def _calculate_hepatitis_coinfection(self, alive: List[Individual]) -> Dict:
        """Track HBV/HCV co-infection with HIV (PHASE 2)."""
        hiv_positive = [
            p for p in alive
            if p.hiv_status in ['acute', 'chronic', 'aids']
        ]
        
        # HBV-HIV co-infection
        hbv_hiv = len([
            p for p in hiv_positive
            if hasattr(p, 'hbv_status') and p.hbv_status == 'positive'
        ])
        
        # HCV-HIV co-infection (rare in Cameroon)
        hcv_hiv = len([
            p for p in hiv_positive
            if hasattr(p, 'hcv_status') and p.hcv_status == 'positive'
        ])
        
        # Triple infection
        triple_infection = len([
            p for p in hiv_positive
            if (hasattr(p, 'hbv_status') and p.hbv_status == 'positive' and
                hasattr(p, 'hcv_status') and p.hcv_status == 'positive')
        ])
        
        # Co-infected on appropriate ART (TDF-based regimen)
        coinfected_on_art = len([
            p for p in hiv_positive
            if (p.on_art and
                hasattr(p, 'hbv_status') and p.hbv_status == 'positive')
        ])
        
        # Regional breakdown of HBV-HIV
        regional_coinfection = {}
        from hivec_cm.core.demographic_parameters import REGIONAL_DISTRIBUTION
        
        for region in REGIONAL_DISTRIBUTION.keys():
            region_hiv_pos = [p for p in hiv_positive
                            if hasattr(p, 'region') and p.region == region]
            region_hbv_hiv = [p for p in region_hiv_pos
                            if hasattr(p, 'hbv_status') and p.hbv_status == 'positive']
            
            regional_coinfection[region] = {
                'hiv_positive': len(region_hiv_pos),
                'hbv_hiv_coinfection': len(region_hbv_hiv),
                'coinfection_rate': (len(region_hbv_hiv) / len(region_hiv_pos))
                    if region_hiv_pos else 0
            }
        
        return {
            'total_plhiv': len(hiv_positive),
            'hbv_hiv_coinfection': hbv_hiv,
            'hcv_hiv_coinfection': hcv_hiv,
            'triple_infection': triple_infection,
            'hbv_hiv_coinfection_rate': (hbv_hiv / len(hiv_positive))
                if hiv_positive else 0,
            'coinfected_on_appropriate_art': coinfected_on_art,
            'art_coverage_among_coinfected': (coinfected_on_art / hbv_hiv)
                if hbv_hiv > 0 else 0,
            'by_region': regional_coinfection
        }
    
    # ========== PHASE 3: DEMOGRAPHICS & PREVENTION DATA COLLECTION ==========
    
    def _calculate_life_years_dalys(self, alive: List[Individual]) -> Dict[str, Any]:
        """Calculate life years lost and DALYs (Disability-Adjusted Life Years).
        
        Returns metrics for:
        - Life years lived with HIV
        - QALYs (Quality-Adjusted Life Years)
        - Life years lost to HIV
        - DALYs by age group
        - YLD (Years Lived with Disability) and YLL (Years of Life Lost)
        """
        hiv_positive = [p for p in alive if p.hiv_status != "susceptible"]
        
        total_life_years_with_hiv = sum(
            getattr(p, 'life_years_lived_with_hiv', 0) for p in hiv_positive
        )
        
        total_qalys = sum(
            getattr(p, 'quality_adjusted_life_years', 0) for p in hiv_positive
        )
        
        # Calculate DALYs by age group
        age_groups = {
            '0_14': (0, 14),
            '15_24': (15, 24),
            '25_49': (25, 49),
            '50_plus': (50, 999)
        }
        
        dalys_by_age = {}
        for age_label, (min_age, max_age) in age_groups.items():
            age_group_hiv = [p for p in hiv_positive
                           if min_age <= p.age <= max_age]
            
            # YLD = Years Lived with Disability
            yld = sum(getattr(p, 'disability_weight', 0) for p in age_group_hiv)
            
            # YLL = Years of Life Lost (estimated from premature deaths)
            # This would be calculated separately based on life expectancy
            
            dalys_by_age[age_label] = {
                'plhiv': len(age_group_hiv),
                'total_life_years': sum(getattr(p, 'life_years_lived_with_hiv', 0)
                                      for p in age_group_hiv),
                'total_qalys': sum(getattr(p, 'quality_adjusted_life_years', 0)
                                  for p in age_group_hiv),
                'yld': yld
            }
        
        return {
            'total_plhiv': len(hiv_positive),
            'life_years_lived_with_hiv': total_life_years_with_hiv,
            'total_qalys': total_qalys,
            'mean_disability_weight': (sum(getattr(p, 'disability_weight', 0)
                                          for p in hiv_positive) / len(hiv_positive))
                if hiv_positive else 0,
            'by_age_group': dalys_by_age
        }
    
    def _calculate_orphanhood(self, alive: List[Individual]) -> Dict[str, Any]:
        """Track orphanhood burden due to HIV.
        
        Returns metrics for:
        - Total orphans due to HIV
        - Maternal/paternal/double orphans
        - Orphans by age group
        - Children with HIV+ parents
        """
        all_children = [p for p in alive if p.age < 18]
        
        orphans = [c for c in all_children
                  if getattr(c, 'is_orphan', False)]
        
        maternal_orphans = [o for o in orphans
                           if getattr(o, 'orphan_type', None) == 'maternal']
        paternal_orphans = [o for o in orphans
                           if getattr(o, 'orphan_type', None) == 'paternal']
        double_orphans = [o for o in orphans
                         if getattr(o, 'orphan_type', None) == 'double']
        
        # Orphans by age group
        orphans_0_4 = [o for o in orphans if o.age < 5]
        orphans_5_14 = [o for o in orphans if 5 <= o.age < 15]
        orphans_15_17 = [o for o in orphans if 15 <= o.age < 18]
        
        # Children with HIV+ parents (not orphans yet)
        hiv_positive_adults = [p for p in alive
                              if p.hiv_status != "susceptible" and p.age >= 15]
        children_of_plhiv = 0
        for adult in hiv_positive_adults:
            children_of_plhiv += len(getattr(adult, 'children_ids', []))
        
        return {
            'total_children_under_18': len(all_children),
            'total_orphans': len(orphans),
            'maternal_orphans': len(maternal_orphans),
            'paternal_orphans': len(paternal_orphans),
            'double_orphans': len(double_orphans),
            'orphans_0_4': len(orphans_0_4),
            'orphans_5_14': len(orphans_5_14),
            'orphans_15_17': len(orphans_15_17),
            'orphan_rate': (len(orphans) / len(all_children))
                if all_children else 0,
            'children_with_hiv_positive_parents': children_of_plhiv
        }
    
    def _calculate_aids_defining_illnesses(self, alive: List[Individual]) -> Dict[str, Any]:
        """Track burden of AIDS-defining opportunistic infections.
        
        Returns metrics for:
        - Total OIs this year
        - Specific OI types (TB, PCP, toxoplasmosis, etc.)
        - OI burden by CD4 count
        - OI prophylaxis coverage
        """
        hiv_positive = [p for p in alive if p.hiv_status != "susceptible"]
        
        # Count individuals who ever had specific OIs
        ever_tb = sum(1 for p in hiv_positive
                     if getattr(p, 'ever_had_tb', False))
        ever_pcp = sum(1 for p in hiv_positive
                      if getattr(p, 'ever_had_pcp', False))
        ever_toxo = sum(1 for p in hiv_positive
                       if getattr(p, 'ever_had_toxo', False))
        
        # Count current active OIs
        active_oi = [p for p in hiv_positive
                    if getattr(p, 'current_oi', None) is not None]
        
        # OI burden by CD4 count
        low_cd4 = [p for p in hiv_positive
                  if getattr(p, 'cd4_count', 500) < 200]
        low_cd4_with_oi = [p for p in low_cd4
                          if getattr(p, 'current_oi', None) is not None]
        
        # Total lifetime OI count
        total_oi_lifetime = sum(getattr(p, 'oi_count_lifetime', 0)
                               for p in hiv_positive)
        
        return {
            'total_plhiv': len(hiv_positive),
            'active_oi_count': len(active_oi),
            'ever_had_tb': ever_tb,
            'ever_had_pcp': ever_pcp,
            'ever_had_toxoplasmosis': ever_toxo,
            'total_oi_lifetime': total_oi_lifetime,
            'plhiv_cd4_under_200': len(low_cd4),
            'plhiv_cd4_under_200_with_oi': len(low_cd4_with_oi),
            'oi_rate_low_cd4': (len(low_cd4_with_oi) / len(low_cd4))
                if low_cd4 else 0,
            'mean_oi_per_person': (total_oi_lifetime / len(hiv_positive))
                if hiv_positive else 0
        }
    
    def _calculate_vmmc_coverage(self, alive: List[Individual]) -> Dict[str, Any]:
        """Track Voluntary Medical Male Circumcision coverage and impact.
        
        Returns metrics for:
        - VMMC coverage by age group
        - VMMC by region
        - Medical vs traditional circumcision
        - Infections potentially averted
        """
        males = [p for p in alive if p.gender == 'male']
        males_15_49 = [p for p in males if 15 <= p.age <= 49]
        
        circumcised = [p for p in males
                      if getattr(p, 'circumcised', False)]
        medically_circumcised = [p for p in circumcised
                                if getattr(p, 'circumcision_type', None) == 'medical']
        
        # VMMC coverage in key age group (15-49)
        circumcised_15_49 = [p for p in males_15_49
                            if getattr(p, 'circumcised', False)]
        vmmc_15_49 = [p for p in circumcised_15_49
                     if getattr(p, 'circumcision_type', None) == 'medical']
        
        # By age group
        age_groups = {
            '10_14': (10, 14),
            '15_19': (15, 19),
            '20_24': (20, 24),
            '25_29': (25, 29),
            '30_49': (30, 49)
        }
        
        vmmc_by_age = {}
        for age_label, (min_age, max_age) in age_groups.items():
            age_males = [p for p in males if min_age <= p.age <= max_age]
            age_vmmc = [p for p in age_males
                       if getattr(p, 'circumcised', False) and
                          getattr(p, 'circumcision_type', None) == 'medical']
            
            vmmc_by_age[age_label] = {
                'total_males': len(age_males),
                'circumcised': len(age_vmmc),
                'coverage_pct': (len(age_vmmc) / len(age_males) * 100)
                    if age_males else 0
            }
        
        return {
            'total_males': len(males),
            'males_15_49': len(males_15_49),
            'total_circumcised': len(circumcised),
            'medically_circumcised': len(medically_circumcised),
            'traditionally_circumcised': len(circumcised) - len(medically_circumcised),
            'vmmc_coverage_15_49_pct': (len(vmmc_15_49) / len(males_15_49) * 100)
                if males_15_49 else 0,
            'by_age_group': vmmc_by_age
        }
    
    def _calculate_prep_coverage(self, alive: List[Individual]) -> Dict[str, Any]:
        """Track PrEP (Pre-Exposure Prophylaxis) coverage and outcomes.
        
        Returns metrics for:
        - PrEP users by risk group
        - PrEP initiations/discontinuations
        - PrEP adherence
        - Breakthrough infections
        """
        hiv_negative = [p for p in alive if p.hiv_status == "susceptible"]
        
        on_prep = [p for p in hiv_negative
                  if getattr(p, 'on_prep', False)]
        
        # PrEP by risk group
        prep_by_risk = {}
        for risk_group in ['low', 'medium', 'high']:
            risk_negative = [p for p in hiv_negative
                           if hasattr(p, 'risk_group') and p.risk_group == risk_group]
            risk_on_prep = [p for p in risk_negative
                          if getattr(p, 'on_prep', False)]
            
            prep_by_risk[risk_group] = {
                'eligible': len(risk_negative),
                'on_prep': len(risk_on_prep),
                'coverage_pct': (len(risk_on_prep) / len(risk_negative) * 100)
                    if risk_negative else 0
            }
        
        # Mean adherence among PrEP users
        mean_prep_adherence = (sum(getattr(p, 'prep_adherence', 0) for p in on_prep) /
                              len(on_prep)) if on_prep else 0
        
        return {
            'total_hiv_negative': len(hiv_negative),
            'on_prep': len(on_prep),
            'prep_coverage_pct': (len(on_prep) / len(hiv_negative) * 100)
                if hiv_negative else 0,
            'mean_prep_adherence': mean_prep_adherence,
            'by_risk_group': prep_by_risk
        }
    
    def _calculate_fertility_patterns(self, alive: List[Individual]) -> Dict[str, Any]:
        """Track fertility patterns in HIV+ vs HIV- women.
        
        Returns metrics for:
        - Births to HIV+ mothers
        - Fertility rate HIV+ vs HIV-
        - Pregnancies on ART
        - Fertility desires met
        """
        women_15_49 = [p for p in alive
                      if p.gender == 'female' and 15 <= p.age <= 49]
        
        hiv_positive_women = [p for p in women_15_49 if p.hiv_status != "susceptible"]
        hiv_negative_women = [p for p in women_15_49 if p.hiv_status == "susceptible"]
        
        # Pregnancies and births
        births_to_positive = sum(getattr(p, 'children_born_while_positive', 0)
                                for p in hiv_positive_women)
        pregnancies_on_art = sum(getattr(p, 'pregnancies_on_art', 0)
                                for p in hiv_positive_women)
        
        # Fertility desire
        positive_want_children = [p for p in hiv_positive_women
                                 if getattr(p, 'fertility_desire', False)]
        
        # Calculate fertility rates (simplified - births per woman)
        fertility_rate_positive = (births_to_positive / len(hiv_positive_women)
                                  if hiv_positive_women else 0)
        fertility_rate_negative = 0  # Would need birth tracking for HIV- women
        
        return {
            'women_15_49': len(women_15_49),
            'hiv_positive_women_15_49': len(hiv_positive_women),
            'hiv_negative_women_15_49': len(hiv_negative_women),
            'births_to_hiv_positive_mothers': births_to_positive,
            'pregnancies_on_art': pregnancies_on_art,
            'fertility_rate_hiv_positive': fertility_rate_positive,
            'proportion_positive_want_children': (len(positive_want_children) /
                len(hiv_positive_women)) if hiv_positive_women else 0
        }



