"""
Model Calibration and Parameter Estimation
==========================================

Advanced calibration methods for the HIV/AIDS epidemiological model
using optimization algorithms and validation techniques.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize, differential_evolution
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ModelCalibrator:
    """
    Advanced calibration system for HIV epidemic model parameters.
    """
    
    def __init__(self, target_data: pd.DataFrame, model_class):
        """
        Initialize calibrator with target data and model class.
        
        Args:
            target_data: DataFrame with Year and HIV Prevalence columns
            model_class: The model class to calibrate
        """
        self.target_data = target_data
        self.model_class = model_class
        self.calibration_years = None
        self.target_prevalences = None
        self._prepare_calibration_data()
        
    def _prepare_calibration_data(self):
        """Prepare target data for calibration."""
        # Use data points every 2-3 years to avoid overfitting
        target_years = [1995, 1998, 2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022]
        
        self.calibration_years = []
        self.target_prevalences = []
        
        for year in target_years:
            if year in self.target_data['Year'].values:
                prevalence = self.target_data[
                    self.target_data['Year'] == year]['HIV Prevalence'].iloc[0]
                if not pd.isna(prevalence):
                    self.calibration_years.append(year)
                    self.target_prevalences.append(prevalence)
        
        logger.info(f"Prepared {len(self.calibration_years)} calibration points")
    
    def objective_function(self, params_array: np.ndarray) -> float:
        """
        Objective function for optimization.
        
        Args:
            params_array: Array of parameter values to test
            
        Returns:
            Objective value (lower is better)
        """
        try:
            # Convert parameter array to ModelParameters object
            params = self._array_to_params(params_array)
            
            # Run model with these parameters
            model = self.model_class(params)
            results = model.run_simulation(years=35, dt=0.5)  # Faster run
            
            # Calculate fit to target data
            model_prevalences = []
            for year in self.calibration_years:
                if year in results['year'].values:
                    model_prev = results[results['year'] == year]['hiv_prevalence'].iloc[0]
                    model_prevalences.append(model_prev)
                else:
                    # Interpolate if exact year not available
                    model_prev = np.interp(year, results['year'], results['hiv_prevalence'])
                    model_prevalences.append(model_prev)
            
            # Calculate weighted mean squared error
            weights = self._get_calibration_weights()
            mse = np.average(
                [(target - model)**2 for target, model in 
                 zip(self.target_prevalences, model_prevalences)],
                weights=weights
            )
            
            # Add penalty for unrealistic epidemic curves
            penalty = self._calculate_penalties(results)
            
            return mse + penalty
            
        except Exception as e:
            logger.warning(f"Model run failed during calibration: {e}")
            return 1e6  # Large penalty for failed runs
    
    def _get_calibration_weights(self) -> List[float]:
        """Get weights for different calibration time points."""
        weights = []
        for year in self.calibration_years:
            if year <= 2000:
                weight = 1.0  # Early epidemic
            elif year <= 2010:
                weight = 2.0  # Peak period (most important)
            else:
                weight = 1.5  # Recent period
            weights.append(weight)
        return weights
    
    def _calculate_penalties(self, results: pd.DataFrame) -> float:
        """Calculate penalties for unrealistic model behavior."""
        penalty = 0.0
        
        # Penalty for extremely high prevalence
        max_prevalence = results['hiv_prevalence'].max()
        if max_prevalence > 15:  # More than 15% seems too high for Cameroon
            penalty += (max_prevalence - 15) * 10
        
        # Penalty for prevalence increasing after 2010
        recent_trend = results[results['year'] >= 2010]['hiv_prevalence']
        if len(recent_trend) > 5:
            trend_slope = np.polyfit(range(len(recent_trend)), recent_trend, 1)[0]
            if trend_slope > 0.1:  # Should be declining
                penalty += trend_slope * 50
        
        # Penalty for unrealistic ART coverage
        final_art_coverage = results['art_coverage'].iloc[-1]
        if final_art_coverage > 90:  # Unrealistically high
            penalty += (final_art_coverage - 90) * 2
        
        return penalty
    
    def _array_to_params(self, params_array: np.ndarray):
        """Convert parameter array to ModelParameters object."""
        from .hiv_model import ModelParameters
        
        params = ModelParameters()
        
        # Map array elements to parameters (order matters!)
        params.base_transmission_rate = params_array[0]
        params.acute_multiplier = params_array[1]
        params.aids_multiplier = params_array[2]
        params.mean_contacts_per_year = params_array[3]
        params.testing_rate_late = params_array[4]
        params.treatment_initiation_prob = params_array[5]
        
        return params
    
    def _params_to_array(self, params) -> np.ndarray:
        """Convert ModelParameters object to array."""
        return np.array([
            params.base_transmission_rate,
            params.acute_multiplier,
            params.aids_multiplier,
            params.mean_contacts_per_year,
            params.testing_rate_late,
            params.treatment_initiation_prob
        ])
    
    def calibrate_differential_evolution(self, 
                                       max_iterations: int = 100) -> Tuple[Dict, float]:
        """
        Calibrate using differential evolution algorithm.
        
        Args:
            max_iterations: Maximum number of iterations
            
        Returns:
            Best parameters and objective value
        """
        logger.info("Starting differential evolution calibration")
        
        # Parameter bounds (min, max)
        bounds = [
            (0.0005, 0.005),    # base_transmission_rate
            (3.0, 15.0),        # acute_multiplier
            (1.5, 8.0),         # aids_multiplier
            (1.5, 5.0),         # mean_contacts_per_year
            (0.1, 0.4),         # testing_rate_late
            (0.5, 0.9)          # treatment_initiation_prob
        ]
        
        result = differential_evolution(
            self.objective_function,
            bounds,
            maxiter=max_iterations,
            popsize=15,
            seed=42,
            updating='deferred',
            workers=1
        )
        
        best_params = self._array_to_params(result.x)
        best_objective = result.fun
        
        logger.info(f"Calibration completed. Best objective: {best_objective:.4f}")
        
        return best_params, best_objective
    
    def calibrate_nelder_mead(self, 
                             initial_params, 
                             max_iterations: int = 200) -> Tuple[Dict, float]:
        """
        Calibrate using Nelder-Mead simplex algorithm.
        
        Args:
            initial_params: Starting parameter values
            max_iterations: Maximum number of iterations
            
        Returns:
            Best parameters and objective value
        """
        logger.info("Starting Nelder-Mead calibration")
        
        initial_array = self._params_to_array(initial_params)
        
        result = minimize(
            self.objective_function,
            initial_array,
            method='Nelder-Mead',
            options={'maxiter': max_iterations, 'disp': True}
        )
        
        best_params = self._array_to_params(result.x)
        best_objective = result.fun
        
        logger.info(f"Calibration completed. Best objective: {best_objective:.4f}")
        
        return best_params, best_objective
    
    def validate_calibration(self, calibrated_params) -> Dict[str, float]:
        """
        Validate calibrated parameters against target data.
        
        Args:
            calibrated_params: Calibrated model parameters
            
        Returns:
            Validation metrics
        """
        logger.info("Validating calibrated parameters")
        
        # Run full model with calibrated parameters
        model = self.model_class(calibrated_params)
        results = model.run_simulation(years=35)
        
        # Calculate validation metrics
        model_prevalences = []
        for year in self.calibration_years:
            model_prev = np.interp(year, results['year'], results['hiv_prevalence'])
            model_prevalences.append(model_prev)
        
        # Calculate metrics
        mae = np.mean([abs(target - model) for target, model in 
                      zip(self.target_prevalences, model_prevalences)])
        
        rmse = np.sqrt(np.mean([(target - model)**2 for target, model in 
                               zip(self.target_prevalences, model_prevalences)]))
        
        mape = np.mean([abs((target - model) / target) * 100 
                       for target, model in zip(self.target_prevalences, model_prevalences)
                       if target > 0])
        
        r_squared = self._calculate_r_squared(self.target_prevalences, model_prevalences)
        
        correlation = np.corrcoef(self.target_prevalences, model_prevalences)[0, 1]
        
        validation_metrics = {
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape,
            'R_squared': r_squared,
            'correlation': correlation,
            'final_prevalence_target': self.target_prevalences[-1],
            'final_prevalence_model': model_prevalences[-1],
            'peak_prevalence_model': max(model_prevalences)
        }
        
        logger.info(f"Validation metrics: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r_squared:.3f}")
        
        return validation_metrics
    
    def _calculate_r_squared(self, actual: List[float], predicted: List[float]) -> float:
        """Calculate R-squared coefficient."""
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        
        if ss_tot == 0:
            return 0.0
        
        return 1 - (ss_res / ss_tot)


class MultiObjectiveCalibrator(ModelCalibrator):
    """
    Multi-objective calibration considering multiple epidemiological indicators.
    """
    
    def __init__(self, target_data: pd.DataFrame, model_class):
        super().__init__(target_data, model_class)
        self.objectives = ['prevalence', 'incidence_trend', 'mortality_trend']
    
    def multi_objective_function(self, params_array: np.ndarray) -> List[float]:
        """
        Multi-objective function returning multiple objectives.
        
        Args:
            params_array: Parameter values to test
            
        Returns:
            List of objective values
        """
        try:
            params = self._array_to_params(params_array)
            model = self.model_class(params)
            results = model.run_simulation(years=35, dt=0.5)
            
            objectives = []
            
            # Objective 1: HIV prevalence fit
            prevalence_mse = self._calculate_prevalence_objective(results)
            objectives.append(prevalence_mse)
            
            # Objective 2: Incidence trend
            incidence_penalty = self._calculate_incidence_objective(results)
            objectives.append(incidence_penalty)
            
            # Objective 3: Epidemic curve realism
            curve_penalty = self._calculate_curve_objective(results)
            objectives.append(curve_penalty)
            
            return objectives
            
        except Exception as e:
            logger.warning(f"Multi-objective evaluation failed: {e}")
            return [1e6, 1e6, 1e6]
    
    def _calculate_prevalence_objective(self, results: pd.DataFrame) -> float:
        """Calculate prevalence fitting objective."""
        model_prevalences = []
        for year in self.calibration_years:
            model_prev = np.interp(year, results['year'], results['hiv_prevalence'])
            model_prevalences.append(model_prev)
        
        weights = self._get_calibration_weights()
        mse = np.average(
            [(target - model)**2 for target, model in 
             zip(self.target_prevalences, model_prevalences)],
            weights=weights
        )
        return mse
    
    def _calculate_incidence_objective(self, results: pd.DataFrame) -> float:
        """Calculate incidence trend objective."""
        # Incidence should peak early and then decline
        incidence_rates = np.array(results['new_infections']) / np.array(results['total_population']) * 100
        
        # Find peak year
        peak_idx = np.argmax(incidence_rates)
        peak_year = results['year'].iloc[peak_idx]
        
        penalty = 0.0
        
        # Peak should be before 2005
        if peak_year > 2005:
            penalty += (peak_year - 2005) * 0.5
        
        # Decline after peak should be consistent
        if peak_idx < len(incidence_rates) - 5:
            post_peak = incidence_rates[peak_idx:]
            if len(post_peak) > 3:
                trend = np.polyfit(range(len(post_peak)), post_peak, 1)[0]
                if trend > 0:  # Should be declining
                    penalty += abs(trend) * 10
        
        return penalty
    
    def _calculate_curve_objective(self, results: pd.DataFrame) -> float:
        """Calculate epidemic curve realism objective."""
        prevalences = np.array(results['hiv_prevalence'])
        
        penalty = 0.0
        
        # Smooth epidemic curve (penalize too much volatility)
        if len(prevalences) > 10:
            differences = np.diff(prevalences)
            volatility = np.std(differences)
            if volatility > 2.0:  # Too volatile
                penalty += (volatility - 2.0) * 5
        
        # Realistic peak timing and magnitude
        peak_prevalence = np.max(prevalences)
        if peak_prevalence > 12:  # Too high for Cameroon
            penalty += (peak_prevalence - 12) * 2
        
        return penalty


def run_comprehensive_calibration(target_data: pd.DataFrame, 
                                 model_class,
                                 calibration_method: str = 'differential_evolution') -> Dict:
    """
    Run comprehensive calibration with multiple methods.
    
    Args:
        target_data: Target HIV prevalence data
        model_class: Model class to calibrate
        calibration_method: 'differential_evolution' or 'nelder_mead'
        
    Returns:
        Calibration results dictionary
    """
    logger.info(f"Starting comprehensive calibration using {calibration_method}")
    
    calibrator = ModelCalibrator(target_data, model_class)
    
    if calibration_method == 'differential_evolution':
        best_params, best_objective = calibrator.calibrate_differential_evolution()
    else:
        # Use default parameters as starting point
        from .hiv_model import ModelParameters
        initial_params = ModelParameters()
        best_params, best_objective = calibrator.calibrate_nelder_mead(initial_params)
    
    # Validate calibrated parameters
    validation_metrics = calibrator.validate_calibration(best_params)
    
    # Prepare results
    calibration_results = {
        'best_parameters': best_params,
        'objective_value': best_objective,
        'validation_metrics': validation_metrics,
        'calibration_method': calibration_method,
        'calibration_points': len(calibrator.calibration_years),
        'target_years': calibrator.calibration_years,
        'target_prevalences': calibrator.target_prevalences
    }
    
    logger.info("Comprehensive calibration completed")
    
    return calibration_results
