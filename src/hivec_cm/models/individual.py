import numpy as np
from typing import Optional
from numpy.random import Generator, default_rng
from .parameters import ModelParameters
from hivec_cm.core.demographic_parameters import (
    get_regional_assignment_probabilities,
    get_regional_hiv_risk_multiplier
)

class Individual:
    """Enhanced individual agent with detailed characteristics."""

    def __init__(
        self,
        agent_id: int,
        age: float,
        gender: str,
        params: ModelParameters,
        rng: Optional[Generator] = None,
        region: Optional[str] = None,
    ):
        self.id = agent_id
        self.age = age
        self.gender = gender
        self.params = params
        self.rng: Generator = rng or default_rng()
        
        # Geographic location
        self.region = region if region else self._assign_region()
        self.regional_hiv_risk_multiplier = get_regional_hiv_risk_multiplier(self.region)
        
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
        self.ever_tested = False
        self.last_test_year = None
        self.viral_load_suppressed = False
        
        # Social and behavioral characteristics
        self.risk_group = self._assign_risk_group()
        self.contacts_per_year = self._assign_contact_rate()
        self.partnership_duration = self.rng.exponential(2.0)
        
        # Vital events
        self.alive = True
        self.death_cause = None
        
        # ===== PHASE 1: ENHANCED DATA COLLECTION ATTRIBUTES =====
        # Transmission tracking
        self.transmission_donor_id = None  # ID of person who infected this individual
        self.transmission_donor_stage = None  # Stage of donor at transmission (acute/chronic/aids)
        self.transmission_donor_viral_load = None  # VL of donor at transmission
        self.transmission_year = None  # Year when infection occurred
        
        # Testing tracking
        self.test_history = []  # List of (year, modality) tuples
        self.testing_modality_last = None  # facility_based, community_based, antenatal, self_test
        self.cd4_at_diagnosis = None  # CD4 count when first diagnosed
        self.diagnosis_year = None  # Year when diagnosed
        
        # Cascade tracking
        self.cascade_linkage_year = None  # Year linked to care after diagnosis
        self.art_regimen = "first_line"  # first_line, second_line, third_line
        self.ltfu_date = None  # Lost to follow-up date
        self.return_to_care_date = None  # Date returned after LTFU
        self.viral_load_rebound_count = 0  # Number of times VL rebounded on ART
        self.regimen_switches = []  # List of (year, old_regimen, new_regimen) tuples
        
        # Partnership tracking (for discordant couple analysis)
        self.current_partner_id = None  # ID of current partner (if in stable partnership)
        self.partner_hiv_status = None  # HIV status of partner (for discordant tracking)
        
        # ===== PHASE 2: TESTING & CO-INFECTIONS ATTRIBUTES =====
        # Testing frequency tracking
        self.total_tests_lifetime = 0  # Total number of HIV tests ever taken
        self.tests_last_12_months = 0  # Tests in past year
        self.last_negative_test_year = None  # Most recent negative test
        self.aware_of_status = False  # Knows they are HIV+
        
        # Co-infection tracking
        self.tb_status = "negative"  # negative, active_tb, latent_tb, on_ipt
        self.tb_diagnosis_year = None  # Year TB was diagnosed
        self.on_ipt = False  # Isoniazid preventive therapy
        self.tb_screened_this_year = False  # Screened for TB this year
        
        # Hepatitis co-infection (from CAMPHIA data)
        self.hbv_status = self._assign_hbv_status()  # HBV co-infection
        self.hcv_status = "negative"  # HCV status (simplified - rare in Cameroon)
        
        # ART adherence & resistance tracking
        self.adherence_level = 0.95  # Proportion of doses taken (0-1)
        self.missed_doses_this_month = 0
        self.drug_resistance = False  # Has developed resistance
        self.resistance_testing_done = False
        
        # ===== PHASE 3: DEMOGRAPHICS & PREVENTION ATTRIBUTES =====
        # Life years & health tracking
        self.life_years_lived_with_hiv = 0  # Years lived since infection
        self.quality_adjusted_life_years = 0  # QALYs (accounting for health state)
        self.disability_weight = 0.0  # Current health state weight (0=perfect, 1=death)
        
        # Orphanhood tracking
        self.children_ids = []  # List of child Individual IDs
        self.is_orphan = False  # Lost one or both parents to HIV
        self.orphan_type = None  # "maternal", "paternal", "double"
        self.orphan_age_at_loss = None  # Age when became orphan
        
        # AIDS-defining illness tracking
        self.oi_history = []  # List of opportunistic infections
        self.current_oi = None  # Active OI
        self.oi_count_lifetime = 0  # Total OIs experienced
        self.ever_had_tb = False
        self.ever_had_pcp = False  # Pneumocystis pneumonia
        self.ever_had_toxo = False  # Toxoplasmosis
        
        # VMMC (Voluntary Medical Male Circumcision)
        self.circumcised = False
        self.circumcision_type = None  # "medical", "traditional", None
        self.vmmc_year = None  # Year of medical circumcision
        
        # PrEP (Pre-Exposure Prophylaxis)
        self.on_prep = False
        self.prep_start_date = None
        self.prep_stop_date = None
        self.prep_adherence = 0.0  # Proportion of doses taken
        self.prep_discontinuation_reason = None  # "side_effects", "seroconverted", "choice"
        
        # Fertility tracking
        self.ever_pregnant_while_hiv_positive = False
        self.pregnancies_on_art = 0  # Number of pregnancies while on ART
        self.children_born_while_positive = 0
        self.fertility_desire = True  # Wants children
    
    def _assign_region(self) -> str:
        """Assign region based on Cameroon population distribution."""
        regional_probs = get_regional_assignment_probabilities()
        regions = list(regional_probs.keys())
        probabilities = list(regional_probs.values())
        return str(self.rng.choice(regions, p=probabilities))
        
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
    
    def _assign_hbv_status(self) -> str:
        """Assign HBV status based on CAMPHIA regional data (PHASE 2)."""
        from hivec_cm.core.demographic_parameters import get_regional_hepatitis_b_prevalence
        
        # Get regional HBV prevalence for this individual's region
        hbv_prev = get_regional_hepatitis_b_prevalence(self.region)
        
        # Check if person has HBV
        if self.rng.random() < hbv_prev:
            return "positive"
        else:
            return "negative"
    
    def get_infectivity(self, current_year: float, time_varying_rate: Optional[float] = None) -> float:
        """
        Calculate current infectivity based on HIV status and treatment.
        
        Args:
            current_year: Current simulation year
            time_varying_rate: Optional time-varying base transmission rate.
                             If provided, overrides params.base_transmission_rate
        """
        if self.hiv_status == "susceptible":
            return 0.0
        
        # Use time-varying rate if provided, otherwise use static rate
        base_rate = time_varying_rate if time_varying_rate is not None else self.params.base_transmission_rate
        
        # Base infectivity by stage
        stage_multipliers = {
            'acute': self.params.acute_multiplier,
            'chronic': self.params.chronic_multiplier,
            'aids': self.params.aids_multiplier
        }
        
        base_infectivity = base_rate * stage_multipliers.get(self.hiv_status, 1.0)
        
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
            # PHASE 1 ENHANCEMENT: Track testing modality
            self.testing_modality_last = self._determine_testing_modality(current_year)
            self.test_history.append((current_year, self.testing_modality_last))
            self.ever_tested = True
            self.last_test_year = current_year
            
            self.tested = True
            # Test accuracy
            if self.rng.random() < 0.98:  # 98% accuracy
                self.diagnosed = True
                # PHASE 1 ENHANCEMENT: Record CD4 at diagnosis (late diagnosis tracking)
                self.cd4_at_diagnosis = self.cd4_count
                self.diagnosis_year = current_year
    
    def _determine_testing_modality(self, current_year: float) -> str:
        """Determine how the person got tested (PHASE 1 ENHANCEMENT)."""
        # Probability distribution for testing modalities changes over time
        
        # Pregnant women
        if self.gender == 'F' and 20 <= self.age <= 45:
            if self.rng.random() < 0.4:  # 40% chance of antenatal testing
                return 'antenatal'
        
        # Before 2010: mostly facility-based
        if current_year < 2010:
            modality_probs = {'facility_based': 0.85, 'community_based': 0.15}
        # 2010-2017: expansion of community testing
        elif current_year < 2018:
            modality_probs = {'facility_based': 0.60, 'community_based': 0.35, 'self_test': 0.05}
        # 2018+: self-testing introduced, index testing
        else:
            modality_probs = {
                'facility_based': 0.45,
                'community_based': 0.30,
                'self_test': 0.15,
                'index_testing': 0.10
            }
        
        modalities = list(modality_probs.keys())
        probs = list(modality_probs.values())
        return str(self.rng.choice(modalities, p=probs))

    
    def _consider_treatment_initiation(self, dt: float, current_year: float):
        """Consider starting antiretroviral treatment."""
        # PHASE 1 ENHANCEMENT: Track linkage to care
        if self.diagnosed and not self.cascade_linkage_year:
            # Assume linkage happens relatively quickly after diagnosis
            if self.rng.random() < 0.8 * dt:  # 80% linkage probability
                self.cascade_linkage_year = current_year
        
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
        
        if (eligible and self.rng.random() < 
                self.params.treatment_initiation_prob * initiation_factor * dt):
            self.on_art = True
            self.art_start_time = self.infection_time
            self.treatment_experienced = True

