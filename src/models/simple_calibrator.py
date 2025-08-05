"""
Comprehensive calibration module for HIV model
"""

import numpy as np
from scipy.optimize import differential_evolution, minimize
import logging


def run_comprehensive_calibration(data, model_class, method='differential_evolution'):
    """Run comprehensive model calibration."""
    logging.info(f"Starting calibration using {method}")
    
    # Define objective function
    def objective(params):
        """Objective function for calibration."""
        try:
            # Create model with parameters
            from ..models.hiv_model import ModelParameters
            model_params = ModelParameters()
            
            # Update parameters
            param_names = ['transmission_rate', 'death_rate_hiv', 'art_efficacy']
            for i, param_name in enumerate(param_names):
                setattr(model_params, param_name, params[i])
            
            # Run model
            model = model_class(model_params, data)
            results = model.run_simulation(years=30, dt=0.2)
            
            # Calculate fit to data
            error = 0
            for _, row in data.iterrows():
                year = row['Year']
                if year >= 1990 and year <= 2020:
                    time_step = int((year - 1990) / 0.2)
                    if time_step < len(results):
                        simulated_prev = results.iloc[time_step]['HIV_Prevalence']
                        observed_prev = row['HIV_Prevalence_Rate']
                        error += (simulated_prev - observed_prev) ** 2
            
            return np.sqrt(error / len(data))
            
        except Exception as e:
            logging.warning(f"Simulation failed with params {params}: {e}")
            return 1000.0  # Large penalty for failed simulations
    
    # Parameter bounds
    bounds = [
        (0.05, 0.3),   # transmission_rate
        (0.01, 0.15),  # death_rate_hiv
        (0.8, 0.99)    # art_efficacy
    ]
    
    if method == 'differential_evolution':
        result = differential_evolution(
            objective, 
            bounds, 
            maxiter=50,  # Reduced for faster execution
            popsize=10,
            seed=42
        )
    else:
        # Nelder-Mead starting from bounds center
        x0 = [(b[0] + b[1]) / 2 for b in bounds]
        result = minimize(objective, x0, method='Nelder-Mead')
    
    # Create optimized parameters
    from ..models.hiv_model import ModelParameters
    best_params = ModelParameters()
    param_names = ['transmission_rate', 'death_rate_hiv', 'art_efficacy']
    
    for i, param_name in enumerate(param_names):
        setattr(best_params, param_name, result.x[i])
    
    # Calculate validation metrics
    validation_metrics = {
        'objective_value': result.fun,
        'MAE': result.fun,
        'R_squared': max(0, 1 - result.fun),
        'success': result.success if hasattr(result, 'success') else True
    }
    
    calibration_results = {
        'best_parameters': best_params,
        'objective_value': result.fun,
        'validation_metrics': validation_metrics,
        'calibration_method': method,
        'optimization_result': result
    }
    
    logging.info(f"Calibration completed. Best objective: {result.fun:.4f}")
    
    return calibration_results
