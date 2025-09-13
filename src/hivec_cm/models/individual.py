import numpy as np
from typing import Optional
from numpy.random import Generator, default_rng
from .parameters import ModelParameters

class Individual:
    """Enhanced individual agent with detailed characteristics."""

    def __init__(
        self,
        agent_id: int,
        age: float,
        gender: str,
        params: ModelParameters,
        rng: Optional[Generator] = None,
    ):
        self.id = agent_id
        self.age = age
        self.gender = gender
        self.params = params
        self.rng: Generator = rng or default_rng()
        
        # Health status
        self.hiv_status = "susceptible"
        self.infection_time = 0.0
        self.cd4_count = self.rng.normal(750, 150)  # Initial CD4
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
        self.partnership_duration = self.rng.exponential(2.0)
        
        # Vital events
        self.alive = True
        self.death_cause = None
        
    def _assign_risk_group(self) -> str:
        """Assign risk group based on age and demographics."""
        if self.age < 15:
            return 'low'
        
        probabilities = list(self.params.risk_group_proportions.values())
        groups = list(self.params.risk_group_proportions.keys())
        return self.rng.choice(groups, p=probabilities)
    
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
        return max(
            0.1,
            self.rng.gamma(rate / self.params.contact_variance, self.params.contact_variance),
        )
    
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
            
            if self.rng.random() < adherence_prob:
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
                self.cd4_count = max(200, self.cd4_count - self.rng.normal(200, 50))
                
        elif self.hiv_status == "chronic":
            # Gradual CD4 decline
            if not self.on_art:
                decline = self.rng.normal(50, 20) * dt
                self.cd4_count = max(0, self.cd4_count - decline)
            
            # Progression to AIDS
            progression_rate = 1.0 / self.params.chronic_duration_years
            if not self.on_art:
                if self.rng.random() < progression_rate * dt:
                    self.hiv_status = "aids"
                    self.cd4_count = min(self.cd4_count, 200)
    
    def _update_viral_load(self):
        """Update viral load based on disease stage and treatment."""
        if self.hiv_status == "acute":
            self.viral_load = self.rng.lognormal(11, 1)  # High viral load
        elif self.hiv_status == "chronic":
            if self.on_art:
                suppression_prob = self.params.treatment_adherence
                if self.rng.random() < suppression_prob:
                    self.viral_load = self.rng.lognormal(1.5, 0.5)  # Suppressed
                else:
                    self.viral_load = self.rng.lognormal(8, 1)  # Unsuppressed
            else:
                self.viral_load = self.rng.lognormal(9, 1)  # Untreated
        elif self.hiv_status == "aids":
            self.viral_load = self.rng.lognormal(10, 1)  # Very high
    
    def _update_treatment_effects(self, dt: float):
        """Update effects of antiretroviral treatment."""
        if self.infection_time - self.art_start_time > 0.5:  # 6 months on ART
            # CD4 recovery
            if self.cd4_count < 500:
                recovery = self.rng.normal(30, 10) * dt
                self.cd4_count = min(800, self.cd4_count + recovery)
            
            # Potential status improvement
            if (self.hiv_status == "aids" and 
                self.cd4_count > 350 and 
                self.rng.random() < 0.1 * dt):
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
            testing_rate *= (1.0 - self.params.funding_cut_magnitude)
        
        # Risk group multiplier for testing
        if self.risk_group == 'high':
            testing_rate *= 2.0
        elif self.risk_group == 'low':
            testing_rate *= 0.5
        
        if self.rng.random() < testing_rate * dt:
            self.tested = True
            # Test accuracy
            if self.rng.random() < 0.98:  # 98% accuracy
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
            initiation_factor *= (1.0 - self.params.funding_cut_magnitude)
        
        if (
            eligible
            and self.rng.random()
            < self.params.treatment_initiation_prob * initiation_factor * dt
        ):
            self.on_art = True
            self.art_start_time = self.infection_time
            self.treatment_experienced = True
