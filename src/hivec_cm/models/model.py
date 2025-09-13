import numpy as np
import pandas as pd
import logging
from typing import List, Optional, Callable, Dict, Any
from numpy.random import default_rng, Generator
from hivec_cm.utils.accel import NUMBA_AVAILABLE, poisson_counts_numba
import time

from .parameters import ModelParameters
from .individual import Individual

logger = logging.getLogger(__name__)


class EnhancedHIVModel:
    """Enhanced HIV epidemic model with improved calibration."""

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

        # Annual counters
        self.deaths_hiv_this_year = 0
        self.deaths_natural_this_year = 0
        self.births_this_year = 0

        # Results storage
        self.results = {
            'year': [], 'total_population': [], 'susceptible': [],
            'hiv_infections': [], 'acute': [], 'chronic': [], 'aids': [],
            'new_infections': [],
            'deaths_hiv': [],
            'deaths_natural': [],
            'births': [],
            'on_art': [], 'tested': [], 'diagnosed': [],
            'hiv_prevalence': [], 'art_coverage': []
        }

        self._initialize_population()
        logger.info(
            "Initialized model with %d individuals",
            len(self.population),
        )
    
    def _initialize_population(self):
        """Initialize population with demographic structure."""
        for _ in range(self.params.initial_population):
            # Age structure based on Cameroon demographics
            age = self._sample_age_structure()
            gender = self.rng.choice(['M', 'F'])
            
            individual = Individual(
                self.agent_id_counter, age, gender, self.params, rng=self.rng
            )
            self.agent_id_counter += 1
            
            # Seed initial HIV infections - Enhanced for realistic 1990
            # prevalence
            if (
                age >= 15
                and self.rng.random() < self.params.initial_hiv_prevalence
            ):
                individual.hiv_status = "chronic"
                individual.infection_time = float(self.rng.uniform(0, 3))
                individual.cd4_count = self.rng.normal(450, 120)
                
                # Some individuals already in acute or AIDS stage
                stage_prob = self.rng.random()
                if stage_prob < 0.05:  # 5% in acute stage
                    individual.hiv_status = "acute"
                    individual.infection_time = float(self.rng.uniform(0, 0.25))
                elif stage_prob > 0.85:  # 15% in AIDS stage
                    individual.hiv_status = "aids"
                    individual.infection_time = float(self.rng.uniform(5, 10))
                    individual.cd4_count = self.rng.normal(150, 50)
            
            self.population.append(individual)
    
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

                transmission_prob = partner.get_infectivity(self.current_year)

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
                    person.hiv_status = "acute"
                    person.infection_time = 0.0
                    person.cd4_count = self.rng.normal(600, 100)
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
                transmission_prob = partner.get_infectivity(self.current_year)

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
                    person.hiv_status = "acute"
                    person.infection_time = 0.0
                    person.cd4_count = self.rng.normal(600, 100)
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
        """Enhanced condom use rate based on Cameroon prevention campaigns."""
        if year < 2000:
            rate = 0.12  # Enhanced: Higher baseline in 1990s
        elif year < 2010:
            # Enhanced linear increase - better early campaigns
            rate = np.interp(year, [2000, 2010], [0.12, 0.35])
        elif year < 2018:
            # Continued acceleration to higher levels
            rate = np.interp(year, [2010, 2018], [0.35, 0.65])
        else:
            rate = 0.65  # Enhanced: Higher sustained level
        
        # Funding cut scenario - more severe reversal (40% reduction)
        if (
            self.params.funding_cut_scenario
            and year >= self.params.funding_cut_year
        ):
            rate *= (1.0 - self.params.funding_cut_magnitude)
        
        return rate
    
    def _mortality_events(self, dt: float):
        """Handle mortality with HIV-specific rates."""
        # Data-driven natural death rate from parameters (series) with fallback
        current_natural_death_rate = self._get_natural_death_rate(
            self.current_year
        )
        
        for individual in self.population[:]:
            if not individual.alive:
                continue
            
            # Base mortality rate
            death_rate = current_natural_death_rate
            
            # Age-specific mortality
            if individual.age > 50:
                death_rate += (individual.age - 50) * 0.003
            elif individual.age < 5:
                death_rate += 0.02  # Child mortality
            
            # HIV-specific mortality
            if individual.hiv_status != "susceptible":
                hiv_multiplier = self.params.hiv_mortality_multiplier.get(
                    individual.hiv_status, 1.0)
                
                if individual.on_art:
                    hiv_multiplier *= (1 - self.params.art_mortality_reduction)
                
                death_rate += (death_rate * hiv_multiplier)
            
            if self.rng.random() < death_rate * dt:
                individual.alive = False
                cause = (
                    "HIV" if individual.hiv_status != "susceptible" else "Natural"
                )
                if cause == "HIV":
                    self.deaths_hiv_this_year += 1
                else:
                    self.deaths_natural_this_year += 1
                individual.death_cause = cause
                self.population.remove(individual)
    
    def _birth_events(self, dt: float):
        """Handle births with mother-to-child transmission."""
        women = [
            p for p in self.population
            if p.alive and p.gender == 'F' and 15 <= p.age <= 45
        ]

        if not women:
            return

        # Time-varying birth rate, from series if provided, else fallback curve
        current_birth_rate = self._get_birth_rate(self.current_year)
        births = int(self.rng.poisson(len(women) * current_birth_rate * dt))
        self.births_this_year += int(births)

        for _ in range(births):
            mother = women[int(self.rng.integers(len(women)))]
            gender = self.rng.choice(['M', 'F'])

            baby = Individual(self.agent_id_counter, 0, gender, self.params, rng=self.rng)
            self.agent_id_counter += 1

            # Mother-to-child transmission with evolving PMTCT guidelines
            if mother.hiv_status in ["acute", "chronic", "aids"]:
                if self.current_year < 2004:
                    mtct_rate = 0.18
                elif self.current_year < 2014:
                    mtct_rate = 0.07 if mother.on_art else 0.13
                else:
                    mtct_rate = 0.02 if mother.on_art else 0.10

                if self.rng.random() < mtct_rate:
                    baby.hiv_status = "chronic"
                    baby.infection_time = 0.0
                    baby.cd4_count = self.rng.normal(300, 50)

            self.population.append(baby)

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
        """Get natural death rate for a year, using series if present."""
        ndr = self.params.natural_death_rate
        # Handle dict forms
        if isinstance(ndr, dict):
            series = ndr.get('series')
            if isinstance(series, dict) and series:
                le_series = None
                le_param = getattr(self.params, 'life_expectancy', None)
                if isinstance(le_param, dict):
                    le_series = le_param.get('series')
                proj_cfg = ndr.get('projection', {}) if isinstance(ndr, dict) else {}
                method = None
                horizon = None
                if isinstance(proj_cfg, dict):
                    method = proj_cfg.get('method')
                    horizon = (
                        proj_cfg.get('taper_horizon_years')
                        or proj_cfg.get('horizon_years')
                    )
                return self._get_series_value_with_projection(
                    series,
                    year,
                    bound_min=None,
                    bound_max=None,
                    le_series=le_series,
                    taper_horizon_years=float(horizon) if horizon else 30.0,
                    projection_method=method or "auto",
                )
            # If min/max provided, use midpoint
            minv = ndr.get('min')
            maxv = ndr.get('max')
            if minv is not None and maxv is not None:
                return (float(minv) + float(maxv)) / 2.0
            # If a single numeric value provided under 'value'
            val = ndr.get('value')
            if val is not None:
                return float(val)
        # If scalar
        try:
            return float(ndr)  # type: ignore[arg-type]
        except Exception:
            # Conservative fallback replicating prior hardcoded curve
            if year < 2000:
                return 0.017
            if year < 2011:
                return float(np.interp(year, [2000, 2010], [0.015, 0.012]))
            if year <= 2022:
                return float(np.interp(year, [2011, 2022], [0.011, 0.008]))
            return float(np.interp(year, [2022, 2100], [0.008, 0.0089]))

    def _get_birth_rate(self, year: float) -> float:
        """Get birth rate for a year, using series if present; fallback to curve."""
        br = self.params.birth_rate
        # Handle dict forms
        if isinstance(br, dict):
            series = br.get('series')
            if isinstance(series, dict) and series:
                bmin = br.get('min')
                bmax = br.get('max')
                proj_cfg = br.get('projection', {}) if isinstance(br, dict) else {}
                method = None
                horizon = None
                if isinstance(proj_cfg, dict):
                    method = proj_cfg.get('method')
                    horizon = (
                        proj_cfg.get('taper_horizon_years')
                        or proj_cfg.get('horizon_years')
                    )
                return self._get_series_value_with_projection(
                    series,
                    year,
                    bound_min=float(bmin) if bmin is not None else None,
                    bound_max=float(bmax) if bmax is not None else None,
                    le_series=None,
                    taper_horizon_years=float(horizon) if horizon else 30.0,
                    projection_method=method or "trend",
                )
            minv = br.get('min')
            maxv = br.get('max')
            if minv is not None and maxv is not None:
                return (float(minv) + float(maxv)) / 2.0
            val = br.get('value')
            if val is not None:
                return float(val)
        # If scalar provided
        try:
            return float(br)  # type: ignore[arg-type]
        except Exception:
            pass
        # Fallback historical curve
        if year < 2000:
            return 0.046
        if year < 2011:
            return float(np.interp(year, [2000, 2010], [0.044, 0.038]))
        if year <= 2022:
            return float(np.interp(year, [2011, 2022], [0.037, 0.034]))
        return float(np.interp(year, [2022, 2100], [0.034, 0.0137]))
    
    def _record_results(self, year: int):
        """Record comprehensive simulation results."""
        alive = [p for p in self.population if p.alive]

        # Count by HIV status
        susceptible = len([p for p in alive if p.hiv_status == "susceptible"])
        acute = len([p for p in alive if p.hiv_status == "acute"])
        chronic = len([p for p in alive if p.hiv_status == "chronic"])
        aids = len([p for p in alive if p.hiv_status == "aids"])

        hiv_positive = acute + chronic + aids

        # Treatment and testing counts
        on_art = len([p for p in alive if p.on_art])
        tested = len([p for p in alive if p.tested])
        diagnosed = len([p for p in alive if p.diagnosed])

        # New infections (infected within last year)
        new_infections = len([
            p for p in alive
            if p.hiv_status in ["acute", "chronic", "aids"]
            and p.infection_time < 1.0
        ])

        # Calculate rates (as proportions, not percentages)
        total_pop = len(alive)
        hiv_prevalence = (hiv_positive / total_pop) if total_pop > 0 else 0
        art_coverage = (on_art / hiv_positive) if hiv_positive > 0 else 0

        # Store results
        self.results['year'].append(year)
        self.results['total_population'].append(total_pop)
        self.results['susceptible'].append(susceptible)
        self.results['hiv_infections'].append(hiv_positive)
        self.results['acute'].append(acute)
        self.results['chronic'].append(chronic)
        self.results['aids'].append(aids)
        self.results['new_infections'].append(new_infections)
        self.results['on_art'].append(on_art)
        self.results['tested'].append(tested)
        self.results['diagnosed'].append(diagnosed)
        self.results['hiv_prevalence'].append(hiv_prevalence)
        self.results['art_coverage'].append(art_coverage)

        self.results['deaths_hiv'].append(self.deaths_hiv_this_year)
        self.results['deaths_natural'].append(self.deaths_natural_this_year)
        self.results['births'].append(self.births_this_year)

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
                    progress = (row['year'] - self.start_year) / self._run_total_years if self._run_total_years > 0 else None
                except Exception:
                    progress = None
                if progress is not None:
                    row['progress'] = max(0.0, min(1.0, float(progress)))
                self._on_year_result(row)
            except Exception as _e:
                # Swallow callback errors to avoid impacting the core model
                pass

        # Reset annual counters
        self.deaths_hiv_this_year = 0
        self.deaths_natural_this_year = 0
        self.births_this_year = 0
