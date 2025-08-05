"""
Enhanced HIV/AIDS Epidemiological Model for Cameroon
====================================================

A sophisticated agent-based model with improved calibration and realistic
transmission dynamics for HIV epidemic simulation.

Author: Epidemiological Modeling Team
Version: 3.0
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import json
import os
from datetime import datetime
import logging


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ModelParameters:
    """
    Comprehensive parameters for the HIV/AIDS epidemic model.
    All rates are annual unless specified otherwise.
    """
    # Population parameters
    initial_population: int = 200000  # Enhanced: Larger population for stability
    birth_rate: float = 0.035
    natural_death_rate: float = 0.015
    
    # HIV transmission parameters - Calibrated for Cameroon epidemic 
    base_transmission_rate: float = 0.0035  # Increased for better calibration
    initial_hiv_prevalence: float = 0.008   # 0.8% starting prevalence
    acute_multiplier: float = 8.0
    chronic_multiplier: float = 1.0
    aids_multiplier: float = 3.0
    
    # Disease progression parameters
    acute_duration_months: float = 3.0
    chronic_duration_years: float = 9.0
    aids_duration_years: float = 2.0
    
    # Behavioral and social parameters - Enhanced for better calibration
    mean_contacts_per_year: float = 2.5  # Increased contact rate
    contact_variance: float = 1.4
    risk_group_proportions: Dict[str, float] = field(default_factory=lambda: {
        'low': 0.85, 'medium': 0.14, 'high': 0.01  # Standard proportions
    })
    risk_group_multipliers: Dict[str, float] = field(default_factory=lambda: {
        'low': 0.7, 'medium': 1.6, 'high': 15.0  # Enhanced multipliers
    })
    
    # Intervention parameters - Updated based on Cameroon timeline
    art_start_year: int = 2002  # Updated: ART officially started in 2002
    art_efficacy_transmission: float = 0.92
    art_efficacy_progression: float = 0.85
    art_mortality_reduction: float = 0.80
    
    # Testing and treatment parameters - Moderately enhanced
    testing_rate_early: float = 0.06   # Moderate early testing
    testing_rate_late: float = 0.28    # Moderate late testing
    treatment_initiation_prob: float = 0.78  # Moderate initiation
    treatment_adherence: float = 0.86   # Moderate adherence
    
    # Mortality parameters
    hiv_mortality_multiplier: Dict[str, float] = field(default_factory=lambda: {
        'acute': 1.2, 'chronic': 1.5, 'aids': 8.0
    })
    
    # Scenario parameters
    funding_cut_scenario: bool = False
    funding_cut_year: int = 2025


class Individual:
    """Enhanced individual agent with detailed characteristics."""
    
    def __init__(self, agent_id: int, age: float, gender: str, params: ModelParameters):
        self.id = agent_id
        self.age = age
        self.gender = gender
        self.params = params
        
        # Health status
        self.hiv_status = "susceptible"
        self.infection_time = 0.0
        self.cd4_count = np.random.normal(750, 150)  # Initial CD4
        self.viral_load = 0.0
        
        # Treatment status
        self.on_art = False
        self.art_start_time = 0.0
        self.tested = False
        self.diagnosed = False
        self.treatment_experienced = False
        
        # Social and behavioral characteristics
        self.risk_group = self._assign_risk_group()
        self.contacts_per_year = self._assign_contact_rate()
        self.partnership_duration = np.random.exponential(2.0)
        
        # Vital events
        self.alive = True
        self.death_cause = None
        
    def _assign_risk_group(self) -> str:
        """Assign risk group based on age and demographics."""
        if self.age < 15:
            return 'low'
        
        probabilities = list(self.params.risk_group_proportions.values())
        groups = list(self.params.risk_group_proportions.keys())
        return np.random.choice(groups, p=probabilities)
    
    def _assign_contact_rate(self) -> float:
        """Assign annual contact rate based on risk group and demographics."""
        base_rate = self.params.mean_contacts_per_year
        risk_multiplier = self.params.risk_group_multipliers[self.risk_group]
        
        # Age-dependent adjustment
        if self.age < 20:
            age_multiplier = 0.6
        elif 20 <= self.age < 30:
            age_multiplier = 1.3
        elif 30 <= self.age < 50:
            age_multiplier = 1.0
        else:
            age_multiplier = 0.4
        
        rate = base_rate * risk_multiplier * age_multiplier
        return max(0.1, np.random.gamma(rate/self.params.contact_variance, 
                                      self.params.contact_variance))
    
    def get_infectivity(self, current_year: float) -> float:
        """Calculate current infectivity based on HIV status and treatment."""
        if self.hiv_status == "susceptible":
            return 0.0
        
        # Base infectivity by stage
        stage_multipliers = {
            'acute': self.params.acute_multiplier,
            'chronic': self.params.chronic_multiplier,
            'aids': self.params.aids_multiplier
        }
        
        base_infectivity = (self.params.base_transmission_rate * 
                           stage_multipliers.get(self.hiv_status, 1.0))
        
        # Viral load effect (simplified)
        if hasattr(self, 'viral_load'):
            viral_load_effect = min(2.0, self.viral_load / 50000)
            base_infectivity *= viral_load_effect
        
        # ART effect with funding cut scenario
        if self.on_art and current_year >= self.params.art_start_year:
            adherence_prob = self.params.treatment_adherence
            if (self.params.funding_cut_scenario and 
                current_year >= self.params.funding_cut_year):
                adherence_prob *= 0.75  # 25% reduction in effective adherence
            
            if random.random() < adherence_prob:
                base_infectivity *= (1 - self.params.art_efficacy_transmission)
        
        return base_infectivity
    
    def update(self, dt: float, current_year: float):
        """Update individual state for one time step."""
        if not self.alive:
            return
            
        self.age += dt
        
        # HIV-related updates
        if self.hiv_status != "susceptible":
            self.infection_time += dt
            self._update_disease_progression(dt)
            self._update_viral_load()
        
        # Treatment updates
        if self.on_art:
            self._update_treatment_effects(dt)
        
        # Testing and care cascade
        if current_year >= 2000:  # Testing became available
            self._consider_testing(dt, current_year)
        
        if (self.diagnosed and not self.on_art and 
            current_year >= self.params.art_start_year):
            self._consider_treatment_initiation(dt, current_year)
    
    def _update_disease_progression(self, dt: float):
        """Update HIV disease stage progression."""
        if self.hiv_status == "acute":
            if self.infection_time > (self.params.acute_duration_months / 12.0):
                self.hiv_status = "chronic"
                self.cd4_count = max(200, self.cd4_count - np.random.normal(200, 50))
                
        elif self.hiv_status == "chronic":
            # Gradual CD4 decline
            if not self.on_art:
                decline = np.random.normal(50, 20) * dt
                self.cd4_count = max(0, self.cd4_count - decline)
            
            # Progression to AIDS
            progression_rate = 1.0 / self.params.chronic_duration_years
            if not self.on_art:
                if random.random() < progression_rate * dt:
                    self.hiv_status = "aids"
                    self.cd4_count = min(self.cd4_count, 200)
    
    def _update_viral_load(self):
        """Update viral load based on disease stage and treatment."""
        if self.hiv_status == "acute":
            self.viral_load = np.random.lognormal(11, 1)  # High viral load
        elif self.hiv_status == "chronic":
            if self.on_art:
                suppression_prob = self.params.treatment_adherence
                if random.random() < suppression_prob:
                    self.viral_load = np.random.lognormal(1.5, 0.5)  # Suppressed
                else:
                    self.viral_load = np.random.lognormal(8, 1)  # Unsuppressed
            else:
                self.viral_load = np.random.lognormal(9, 1)  # Untreated
        elif self.hiv_status == "aids":
            self.viral_load = np.random.lognormal(10, 1)  # Very high
    
    def _update_treatment_effects(self, dt: float):
        """Update effects of antiretroviral treatment."""
        if self.infection_time - self.art_start_time > 0.5:  # 6 months on ART
            # CD4 recovery
            if self.cd4_count < 500:
                recovery = np.random.normal(30, 10) * dt
                self.cd4_count = min(800, self.cd4_count + recovery)
            
            # Potential status improvement
            if (self.hiv_status == "aids" and 
                self.cd4_count > 350 and 
                random.random() < 0.1 * dt):
                self.hiv_status = "chronic"
    
    def _consider_testing(self, dt: float, current_year: float):
        """Consider HIV testing based on year and individual characteristics."""
        if self.tested or self.hiv_status == "susceptible":
            return
        
        # Enhanced time-varying testing rates reflecting Cameroon's actual scale-up
        if current_year < 2004:
            testing_rate = 0.05  # Enhanced: Slightly higher early testing
        elif current_year < 2010:
            testing_rate = 0.18  # Enhanced: Better VCT scale-up
        elif current_year < 2018:
            testing_rate = 0.32  # Enhanced: Accelerated testing expansion  
        else:
            testing_rate = 0.55  # Enhanced: Aggressive "Test and Treat"
        
        # Funding cut scenario
        if (self.params.funding_cut_scenario and 
            current_year >= self.params.funding_cut_year):
            testing_rate *= 0.5  # 50% reduction in testing outreach
        
        # Risk group multiplier for testing
        if self.risk_group == 'high':
            testing_rate *= 2.0
        elif self.risk_group == 'low':
            testing_rate *= 0.5
        
        if random.random() < testing_rate * dt:
            self.tested = True
            # Test accuracy
            if random.random() < 0.98:  # 98% accuracy
                self.diagnosed = True
    
    def _consider_treatment_initiation(self, dt: float, current_year: float):
        """Consider starting antiretroviral treatment."""
        # Treatment eligibility based on CD4 count and year
        if current_year >= 2016:
            eligible = True  # "Treat All" policy
        else:
            # Keep the original CD4 threshold logic
            if current_year < 2010:
                cd4_threshold = 200  # WHO guidelines 2002-2009
            elif current_year < 2013:
                cd4_threshold = 350  # WHO guidelines 2010-2012
            else:
                cd4_threshold = 500  # WHO guidelines 2013+
            eligible = (self.hiv_status == "aids" or 
                       self.cd4_count <= cd4_threshold)

        # Time-varying initiation probability
        if current_year < 2004.75:  # October 2004
            initiation_factor = 0.1  # High cost, very low initiation
        elif current_year < 2010:
            initiation_factor = 0.5  # Post-price drop
        else:
            initiation_factor = 1.0  # PEPFAR/Global Fund scale-up

        # Funding cut scenario
        if (self.params.funding_cut_scenario and 
            current_year >= self.params.funding_cut_year):
            initiation_factor *= 0.6  # 40% reduction in new ART initiations
        
        if (eligible and 
            random.random() < self.params.treatment_initiation_prob * 
            initiation_factor * dt):
            self.on_art = True
            self.art_start_time = self.infection_time
            self.treatment_experienced = True


class EnhancedHIVModel:
    """Enhanced HIV epidemic model with improved calibration."""
    
    def __init__(self, params: ModelParameters, calibration_data: Optional[pd.DataFrame] = None):
        self.params = params
        self.calibration_data = calibration_data
        self.population = []
        self.agent_id_counter = 0
        self.current_year = 1990
        
        # Results storage
        self.results = {
            'year': [], 'total_population': [], 'susceptible': [],
            'hiv_infections': [], 'acute': [], 'chronic': [], 'aids': [],
            'new_infections': [], 'deaths_hiv': [], 'deaths_natural': [],
            'on_art': [], 'tested': [], 'diagnosed': [],
            'hiv_prevalence': [], 'art_coverage': []
        }
        
        self._initialize_population()
        logger.info(f"Initialized model with {len(self.population)} individuals")
    
    def _initialize_population(self):
        """Initialize population with demographic structure."""
        for _ in range(self.params.initial_population):
            # Age structure based on Cameroon demographics
            age = self._sample_age_structure()
            gender = random.choice(['M', 'F'])
            
            individual = Individual(self.agent_id_counter, age, gender, self.params)
            self.agent_id_counter += 1
            
            # Seed initial HIV infections - Enhanced for realistic 1990 prevalence  
            if age >= 15 and random.random() < self.params.initial_hiv_prevalence:
                individual.hiv_status = "chronic"
                individual.infection_time = random.uniform(0, 3)
                individual.cd4_count = np.random.normal(450, 120)
                
                # Some individuals already in acute or AIDS stage
                stage_prob = random.random()
                if stage_prob < 0.05:  # 5% in acute stage
                    individual.hiv_status = "acute"
                    individual.infection_time = random.uniform(0, 0.25)
                elif stage_prob > 0.85:  # 15% in AIDS stage
                    individual.hiv_status = "aids"
                    individual.infection_time = random.uniform(5, 10)
                    individual.cd4_count = np.random.normal(150, 50)
            
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
        selected_group = np.random.choice(len(age_groups), p=probs)
        min_age, max_age, _ = age_groups[selected_group]
        
        return random.uniform(min_age, max_age)
    
    def run_simulation(self, years: int = 35, dt: float = 0.1) -> pd.DataFrame:
        """Run the complete HIV epidemic simulation."""
        logger.info(f"Starting simulation for {years} years")
        
        steps = int(years / dt)
        
        for step in range(steps):
            self.current_year = 1990 + (step * dt)
            
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
    
    def _transmission_events(self, dt: float):
        """Handle HIV transmission with improved mixing patterns."""
        susceptible = [p for p in self.population 
                      if p.alive and p.hiv_status == "susceptible" and p.age >= 15]
        infected = [p for p in self.population 
                   if p.alive and p.hiv_status in ["acute", "chronic", "aids"]]
        
        if not infected or not susceptible:
            return
        
        for person in susceptible:
            # Number of contacts this time step
            contacts = np.random.poisson(person.contacts_per_year * dt)
            
            for _ in range(contacts):
                # Assortative mixing by age and risk group
                partner = self._select_partner(person, infected)
                if partner:
                    transmission_prob = partner.get_infectivity(self.current_year)
                    
                    # Transmission probability modifiers
                    transmission_prob *= person.params.risk_group_multipliers[person.risk_group]
                    
                    # Circumcision effect (males)
                    if person.gender == 'M' and random.random() < 0.3:  # 30% circumcised
                        transmission_prob *= 0.4
                    
                    # Condom use effect
                    if random.random() < self._get_condom_use_rate(self.current_year):
                        transmission_prob *= 0.15  # 85% efficacy
                    
                    if random.random() < transmission_prob:
                        person.hiv_status = "acute"
                        person.infection_time = 0.0
                        person.cd4_count = np.random.normal(600, 100)
                        break
    
    def _select_partner(self, person: Individual, 
                       infected: List[Individual]) -> Optional[Individual]:
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
            return random.choice(infected)
        
        # Use numpy choice with indices
        probs = [w / total_weight for w in age_preferences]
        chosen_index = np.random.choice(len(infected), p=probs)
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
        if (self.params.funding_cut_scenario and 
            year >= self.params.funding_cut_year):
            rate *= 0.6
        
        return rate
    
    def _mortality_events(self, dt: float):
        """Handle mortality with HIV-specific rates."""
        # Time-varying natural death rate
        if self.current_year < 2000:
            current_natural_death_rate = 0.017  # Higher mortality in the 90s
        elif self.current_year < 2011:
            # Linear interpolation from 0.015 down to 0.012
            current_natural_death_rate = np.interp(
                self.current_year, [2000, 2010], [0.015, 0.012])
        else:
            # Linear interpolation from 0.011 down to 0.008
            current_natural_death_rate = np.interp(
                self.current_year, [2011, 2022], [0.011, 0.008])
        
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
            
            if random.random() < death_rate * dt:
                individual.alive = False
                cause = ("HIV" if individual.hiv_status != "susceptible" 
                        else "Natural")
                individual.death_cause = cause
                self.population.remove(individual)
    
    def _birth_events(self, dt: float):
        """Handle births with mother-to-child transmission."""
        women = [p for p in self.population 
                if p.alive and p.gender == 'F' and 15 <= p.age <= 45]
        
        if not women:
            return
        
        # Time-varying birth rate
        if self.current_year < 2000:
            current_birth_rate = 0.046
        elif self.current_year < 2011:
            # Linear interpolation from 0.044 (in 2000) down to 0.038 (in 2010)
            current_birth_rate = np.interp(
                self.current_year, [2000, 2010], [0.044, 0.038])
        else:
            # Linear interpolation from 0.037 (in 2011) down to 0.034 (in 2022)
            current_birth_rate = np.interp(
                self.current_year, [2011, 2022], [0.037, 0.034])
        
        births = np.random.poisson(len(women) * current_birth_rate * dt)
        
        for _ in range(births):
            mother = random.choice(women)
            gender = random.choice(['M', 'F'])
            
            baby = Individual(self.agent_id_counter, 0, gender, self.params)
            self.agent_id_counter += 1
            
            # Mother-to-child transmission with evolving PMTCT guidelines
            if mother.hiv_status in ["acute", "chronic", "aids"]:
                if self.current_year < 2004:
                    # Pre-intervention / single-dose Nevirapine era
                    mtct_rate = 0.18
                elif self.current_year < 2014:
                    # More effective multidrug regimens
                    mtct_rate = 0.07 if mother.on_art else 0.13
                else:
                    # Option B+ era
                    mtct_rate = 0.02 if mother.on_art else 0.10
                
                if random.random() < mtct_rate:
                    baby.hiv_status = "chronic"
                    baby.infection_time = 0.0
                    baby.cd4_count = np.random.normal(300, 50)
            
            self.population.append(baby)
    
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
        new_infections = len([p for p in alive 
                             if p.hiv_status in ["acute", "chronic", "aids"] 
                             and p.infection_time < 1.0])
        
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
        
        # Mortality (estimated)
        self.results['deaths_hiv'].append(int(hiv_positive * 0.1))
        self.results['deaths_natural'].append(int(total_pop * 0.015))


def save_model_configuration(params: ModelParameters, output_path: str):
    """Save model parameters to JSON file."""
    config = {
        'model_info': {
            'version': '3.0',
            'description': 'Enhanced HIV/AIDS Epidemiological Model for Cameroon',
            'created': datetime.now().isoformat()
        },
        'parameters': {
            'population': {
                'initial_population': params.initial_population,
                'birth_rate': params.birth_rate,
                'natural_death_rate': params.natural_death_rate
            },
            'transmission': {
                'base_transmission_rate': params.base_transmission_rate,
                'acute_multiplier': params.acute_multiplier,
                'chronic_multiplier': params.chronic_multiplier,
                'aids_multiplier': params.aids_multiplier
            },
            'disease_progression': {
                'acute_duration_months': params.acute_duration_months,
                'chronic_duration_years': params.chronic_duration_years,
                'aids_duration_years': params.aids_duration_years
            },
            'social_behavioral': {
                'mean_contacts_per_year': params.mean_contacts_per_year,
                'contact_variance': params.contact_variance,
                'risk_group_proportions': params.risk_group_proportions,
                'risk_group_multipliers': params.risk_group_multipliers
            },
            'interventions': {
                'art_start_year': params.art_start_year,
                'art_efficacy_transmission': params.art_efficacy_transmission,
                'art_efficacy_progression': params.art_efficacy_progression,
                'art_mortality_reduction': params.art_mortality_reduction,
                'testing_rate_early': params.testing_rate_early,
                'testing_rate_late': params.testing_rate_late,
                'treatment_initiation_prob': params.treatment_initiation_prob,
                'treatment_adherence': params.treatment_adherence
            }
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)


def main():
    """Main execution function."""
    logger.info("Starting Enhanced HIV/AIDS Model for Cameroon")
    
    # Load calibration data
    try:
        calibration_data = pd.read_csv('data/processed/integrated_hiv_cameroon_data.csv')
        logger.info("Loaded calibration data successfully")
    except FileNotFoundError:
        logger.warning("No calibration data found, using default parameters")
        calibration_data = None
    
    # Initialize model
    params = ModelParameters()
    model = EnhancedHIVModel(params, calibration_data)
    
    # Run simulation
    results = model.run_simulation(years=35)
    
    # Save results
    os.makedirs('results', exist_ok=True)
    results.to_csv('results/enhanced_hiv_model_results.csv', index=False)
    save_model_configuration(params, 'results/model_configuration.json')
    
    logger.info("Enhanced model execution completed")
    
    # Print summary
    final_prevalence = results['hiv_prevalence'].iloc[-1]
    peak_prevalence = results['hiv_prevalence'].max()
    final_art_coverage = results['art_coverage'].iloc[-1]
    
    print(f"\nModel Results Summary:")
    print(f"Final HIV prevalence: {final_prevalence:.2f}%")
    print(f"Peak HIV prevalence: {peak_prevalence:.2f}%")
    print(f"Final ART coverage: {final_art_coverage:.2f}%")
    print(f"Final population: {results['total_population'].iloc[-1]:,}")


if __name__ == "__main__":
    main()
