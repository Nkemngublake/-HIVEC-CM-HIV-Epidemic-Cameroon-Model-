"""
HIVEC-CM Parameter Mapper
Bridges scenario parameters to model behavior with smooth transitions from historical calibration.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union


class ParameterMapper:
    """
    Maps scenario parameters to model behavior curves.
    
    Key responsibilities:
    1. Load calibrated historical parameters
    2. Apply scenario modifications for future years
    3. Provide smooth transitions at transition year (default 2024)
    4. Apply funding multipliers appropriately
    
    Usage:
        mapper = ParameterMapper(
            calibration_file="config/parameters_v4_calibrated.json",
            scenario_params=scenario_object,
            transition_year=2024
        )
        
        # Get policy parameters
        condom_rate = mapper.get_condom_coverage(year)
        testing_rate = mapper.get_testing_rate(year)
    """
    
    def __init__(
        self,
        calibration_file: Union[str, Path],
        scenario_params: Optional[Any] = None,
        transition_year: int = 2024,
        transition_duration: int = 2
    ):
        """
        Initialize parameter mapper.
        
        Args:
            calibration_file: Path to parameters_v4_calibrated.json
            scenario_params: Scenario object with policy parameters
            transition_year: Year to start transitioning to scenario values
            transition_duration: Years over which to smooth the transition
        """
        self.transition_year = transition_year
        self.transition_duration = transition_duration
        self.scenario_params = scenario_params
        
        # Load calibrated parameters
        with open(calibration_file, 'r') as f:
            self.calibrated_params = json.load(f)
        
        # Determine scenario type from scenario_params
        self.scenario_type = self._determine_scenario_type()
    
    def _determine_scenario_type(self) -> str:
        """Determine scenario type from scenario_params attributes."""
        if self.scenario_params is None:
            return 'baseline'
        
        scenario_id = getattr(self.scenario_params, 'scenario_id', '').lower()
        
        if 'optimistic' in scenario_id or 's1a' in scenario_id:
            return 'optimistic'
        elif 'pessimistic' in scenario_id or 's1b' in scenario_id:
            return 'pessimistic'
        else:
            return 'baseline'
    
    def _get_historical_value(self, param_path: str, year: float) -> float:
        """
        Get historical calibrated value for a parameter.
        
        Args:
            param_path: Path to parameter in calibrated_params (e.g., 'prevention.condom_distribution')
            year: Year to get value for
        
        Returns:
            Interpolated historical value
        """
        # Navigate to parameter
        parts = param_path.split('.')
        param = self.calibrated_params
        for part in parts:
            param = param[part]
        
        # Handle different historical coverage formats
        if 'historical_coverage' in param:
            coverage_dict = param['historical_coverage']
        elif 'historical_rates' in param:
            coverage_dict = param['historical_rates']
        elif 'historical_series' in param:
            return self._interpolate_series(param['historical_series'], year)
        else:
            # Direct value
            return param
        
        # Find appropriate time period
        for period_key, period_value in coverage_dict.items():
            if isinstance(period_value, dict):
                # Check if this is a range or interpolation period
                if 'start' in period_value and 'end' in period_value:
                    # Parse period (e.g., "2000_2009")
                    if '_' in period_key:
                        start_year, end_year = map(int, period_key.split('_'))
                        if start_year <= year <= end_year:
                            return np.interp(
                                year,
                                [start_year, end_year],
                                [period_value['start'], period_value['end']]
                            )
                elif 'value' in period_value:
                    # Single value for period
                    if '_' in period_key:
                        start_year, end_year = map(int, period_key.split('_'))
                        if start_year <= year <= end_year:
                            return period_value['value']
            else:
                # Direct value (e.g., for single year periods)
                if '_' in period_key:
                    start_year, end_year = map(int, period_key.split('_'))
                    if start_year <= year <= end_year:
                        return period_value
        
        # Default fallback
        return 0.0
    
    def _interpolate_series(self, series: Dict[str, float], year: float) -> float:
        """Interpolate value from time series."""
        years = sorted([int(y) for y in series.keys()])
        values = [series[str(y)] for y in years]
        return float(np.interp(year, years, values))
    
    def _get_scenario_target(self, param_path: str) -> Optional[float]:
        """Get scenario-specific target value."""
        parts = param_path.split('.')
        param = self.calibrated_params
        for part in parts:
            if part not in param:
                return None
            param = param[part]
        
        if 'scenario_targets' in param:
            return param['scenario_targets'].get(self.scenario_type)
        
        return None
    
    def _smooth_transition(self, year: float, historical_value: float, scenario_target: float) -> float:
        """
        Smooth transition from historical to scenario value using sigmoid function.
        
        Args:
            year: Current year
            historical_value: Value from historical calibration
            scenario_target: Target value from scenario
        
        Returns:
            Smoothly transitioned value
        """
        if year < self.transition_year:
            return historical_value
        
        if year >= self.transition_year + self.transition_duration:
            return scenario_target
        
        # Sigmoid transition
        progress = (year - self.transition_year) / self.transition_duration
        # Use smooth sigmoid: 0.5 + 0.5 * tanh(4*(progress-0.5))
        smooth_progress = 0.5 + 0.5 * np.tanh(4 * (progress - 0.5))
        
        return historical_value + (scenario_target - historical_value) * smooth_progress
    
    def get_condom_coverage(self, year: float) -> float:
        """
        Get condom distribution coverage rate.
        
        Args:
            year: Simulation year
        
        Returns:
            Condom coverage rate (0-1)
        """
        historical = self._get_historical_value('prevention.condom_distribution', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('prevention.condom_distribution')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_testing_rate(self, year: float, population_type: str = 'general') -> float:
        """
        Get HIV testing rate.
        
        Args:
            year: Simulation year
            population_type: 'general' or 'key_populations'
        
        Returns:
            Testing rate (0-1)
        """
        if population_type == 'key_populations':
            param_path = 'testing.key_populations'
        else:
            param_path = 'testing.general_population'
        
        historical = self._get_historical_value(param_path, year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target(param_path)
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_art_initiation_rate(self, year: float) -> float:
        """
        Get ART initiation rate.
        
        Args:
            year: Simulation year
        
        Returns:
            ART initiation rate (0-1)
        """
        # ART not available before 2004
        if year < 2004:
            return 0.0
        
        historical = self._get_historical_value('art_program.initiation', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('art_program.initiation')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_art_retention_rate(self, year: float, months: int = 12) -> float:
        """
        Get ART retention rate.
        
        Args:
            year: Simulation year
            months: 12 or 24 month retention
        
        Returns:
            Retention rate (0-1)
        """
        if year < 2004:
            return 0.0
        
        if months == 12:
            param_path = 'art_program.retention_12_months'
        else:
            param_path = 'art_program.retention_24_months'
        
        historical = self._get_historical_value(param_path, year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target(param_path)
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_viral_suppression_rate(self, year: float) -> float:
        """
        Get viral suppression rate among those on ART.
        
        Args:
            year: Simulation year
        
        Returns:
            Viral suppression rate (0-1)
        """
        if year < 2004:
            return 0.0
        
        historical = self._get_historical_value('art_program.viral_suppression', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('art_program.viral_suppression')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_treatment_interruption_rate(self, year: float) -> float:
        """
        Get treatment interruption rate (stockouts).
        
        Args:
            year: Simulation year
        
        Returns:
            Interruption rate (0-1)
        """
        if year < 2004:
            return 0.0
        
        historical = self._get_historical_value('art_program.treatment_interruption', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('art_program.treatment_interruption')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_pmtct_anc_coverage(self, year: float) -> float:
        """Get ANC coverage rate."""
        historical = self._get_historical_value('pmtct.anc_coverage', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('pmtct.anc_coverage')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_pmtct_testing_rate(self, year: float) -> float:
        """Get PMTCT testing rate at ANC."""
        historical = self._get_historical_value('pmtct.testing_at_anc', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('pmtct.testing_at_anc')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_pmtct_art_coverage(self, year: float) -> float:
        """Get PMTCT ART coverage for pregnant women."""
        historical = self._get_historical_value('pmtct.art_coverage_pregnant', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('pmtct.art_coverage_pregnant')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_prep_coverage(self, year: float) -> float:
        """Get PrEP coverage for key populations."""
        historical = self._get_historical_value('prevention.prep_coverage', year)
        
        if year < self.transition_year:
            return historical
        
        scenario_target = self._get_scenario_target('prevention.prep_coverage')
        
        if scenario_target is None:
            return historical
        
        return self._smooth_transition(year, historical, scenario_target)
    
    def get_birth_rate(self, year: float) -> float:
        """Get birth rate from demographics."""
        return self._get_historical_value('demographics.birth_rate', year)
    
    def get_death_rate(self, year: float) -> float:
        """Get natural death rate from demographics."""
        return self._get_historical_value('demographics.death_rate', year)
    
    def apply_funding_multiplier(self, base_value: float, category: str) -> float:
        """
        Apply funding multiplier to a coverage parameter.
        
        Args:
            base_value: Base parameter value
            category: Parameter category ('testing', 'art', 'prevention', 'pmtct')
        
        Returns:
            Adjusted value with funding multiplier applied
        """
        if self.scenario_type == 'baseline':
            return base_value
        
        funding_config = self.calibrated_params['funding_scenarios'].get(self.scenario_type)
        
        if not funding_config:
            return base_value
        
        multiplier = funding_config['multiplier']
        sensitivity = funding_config['sensitivity_by_category'].get(category, 0.5)
        
        # Calculate adjustment
        adjustment = (multiplier - 1.0) * sensitivity
        adjusted = base_value * (1.0 + adjustment)
        
        # Ensure value stays in valid range [0, 1]
        return max(0.0, min(1.0, adjusted))
    
    def get_scenario_info(self) -> Dict[str, Any]:
        """Get information about current scenario."""
        return {
            'scenario_type': self.scenario_type,
            'transition_year': self.transition_year,
            'transition_duration': self.transition_duration,
            'has_scenario_params': self.scenario_params is not None
        }
