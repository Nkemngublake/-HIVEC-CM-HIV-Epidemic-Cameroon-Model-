#!/usr/bin/env python3
"""
Automated Model Calibration Tool
=================================
Calibrates HIVEC-CM model parameters to match UNAIDS validation targets.

This script uses Bayesian optimization to find optimal parameter values that
minimize the discrepancy between model outputs and empirical data.

Usage:
    python calibrate_model.py
    python calibrate_model.py --max-iterations 50 --targets unaids_cameroon_data.json
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import minimize, differential_evolution
from sklearn.metrics import mean_squared_error, r2_score
import argparse
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')


class ModelCalibrator:
    """Calibrates model parameters to match empirical targets."""
    
    def __init__(self, targets_path=None):
        if targets_path is None:
            # Use absolute path relative to this script
            script_dir = Path(__file__).parent
            targets_path = script_dir.parent / 'data' / 'validation_targets' / 'unaids_cameroon_data.json'
        
        with open(targets_path, 'r') as f:
            self.targets_data = json.load(f)
        
        self.calibration_targets = self.targets_data['calibration_targets']
        self.validation_targets = self.targets_data['validation_targets']
        
        # Parameters to calibrate
        self.param_bounds = {
            'transmission_multiplier': (0.5, 2.0),  # Scales base transmission probability
            'contact_rate_multiplier': (0.5, 2.0),  # Scales contact rates
            'initial_prevalence_1990': (0.001, 0.02),  # Initial HIV prevalence
            'risk_group_multiplier': (1.0, 5.0),  # High-risk group transmission boost
        }
        
        self.calibration_history = []
    
    def objective_function(self, params_array):
        """
        Objective function to minimize: weighted sum of squared errors.
        
        Parameters:
        -----------
        params_array : array
            [transmission_mult, contact_mult, init_prev, risk_mult]
        
        Returns:
        --------
        float
            Weighted sum of squared errors
        """
        param_dict = self._array_to_dict(params_array)
        
        # Load model results (would need to run simulation here in practice)
        # For now, use existing results and apply parameter adjustments
        model_outputs = self._simulate_with_params(param_dict)
        
        # Calculate errors for each indicator
        errors = {}
        weights = {
            'hiv_prevalence_15_49': 10.0,  # High priority
            'new_hiv_infections': 5.0,
            'hiv_deaths': 3.0,
            'people_living_with_hiv': 5.0,
            'art_coverage': 1.0,  # Already well-calibrated
            'population_total': 2.0
        }
        
        total_error = 0.0
        
        for indicator, target_dict in self.calibration_targets.items():
            if indicator not in model_outputs:
                continue
            
            model_vals = model_outputs[indicator]
            target_vals = np.array([target_dict[str(y)] for y in sorted(map(int, target_dict.keys()))])
            
            # Calculate RMSE
            rmse = np.sqrt(mean_squared_error(target_vals, model_vals))
            
            # Normalize by mean target value
            normalized_rmse = rmse / (np.mean(target_vals) + 1e-10)
            
            # Apply weight
            weighted_error = weights.get(indicator, 1.0) * normalized_rmse
            
            errors[indicator] = {
                'rmse': rmse,
                'normalized_rmse': normalized_rmse,
                'weighted_error': weighted_error
            }
            
            total_error += weighted_error
        
        # Store in history
        self.calibration_history.append({
            'params': param_dict.copy(),
            'total_error': total_error,
            'errors': errors
        })
        
        if len(self.calibration_history) % 10 == 0:
            print(f"   Iteration {len(self.calibration_history)}: Error = {total_error:.4f}")
        
        return total_error
    
    def _array_to_dict(self, params_array):
        """Convert parameter array to dictionary."""
        param_names = list(self.param_bounds.keys())
        return {name: params_array[i] for i, name in enumerate(param_names)}
    
    def _dict_to_array(self, param_dict):
        """Convert parameter dictionary to array."""
        param_names = list(self.param_bounds.keys())
        return np.array([param_dict[name] for name in param_names])
    
    def _simulate_with_params(self, param_dict):
        """
        Simulate model with given parameters.
        
        NOTE: This is a simplified version that adjusts existing results.
        In practice, you would run the full model simulation with new parameters.
        """
        # Load existing model results using absolute path
        script_dir = Path(__file__).parent
        results_base = script_dir.parent / 'results' / 'montecarlo_scenarios' / 'S0_baseline'
        
        # Find the most recent results directory
        result_dirs = sorted(results_base.glob('*'))
        if not result_dirs:
            raise FileNotFoundError(f"No results found in {results_base}")
        
        results_path = result_dirs[-1]  # Use most recent
        summary_path = results_path / 'summary_statistics.csv'
        df = pd.read_csv(summary_path)
        
        # Apply scaling (same as in quick_validate.py)
        POPULATION_SCALE = 1190.0
        df['prevalence_pct'] = df['hiv_prevalence_mean'] * 100
        df['population_thousands'] = (df['total_population_mean'] * POPULATION_SCALE) / 1000
        df['infections_thousands'] = (df['new_infections_mean'] * POPULATION_SCALE) / 1000
        df['deaths_thousands'] = (df['deaths_hiv_mean'] * POPULATION_SCALE) / 1000
        df['plhiv'] = df['hiv_prevalence_mean'] * df['total_population_mean']
        df['plhiv_thousands'] = (df['plhiv'] * POPULATION_SCALE) / 1000
        df['art_coverage_pct'] = (df['on_art_mean'] / df['plhiv']) * 100
        df['art_coverage_pct'] = df['art_coverage_pct'].fillna(0)
        
        # Apply parameter adjustments (simplified - scales existing results)
        trans_mult = param_dict['transmission_multiplier']
        init_prev_target = param_dict['initial_prevalence_1990']
        
        # Adjust prevalence trajectory
        # Scale to match initial prevalence target
        df_1990 = df[df['year'] == 1990]
        if not df_1990.empty:
            current_1990_prev = df_1990['prevalence_pct'].values[0] / 100
            scale_factor = init_prev_target / (current_1990_prev + 1e-10)
            
            # Apply scaling with decay (more influence at start, less at end)
            years = df['year'].values
            time_weights = np.exp(-(years - 1990) / 20.0)  # Decay over 20 years
            
            df['prevalence_pct_adjusted'] = df['prevalence_pct'] * (1 + (scale_factor - 1) * time_weights)
            df['prevalence_pct_adjusted'] = df['prevalence_pct_adjusted'].clip(0, 100)
        else:
            df['prevalence_pct_adjusted'] = df['prevalence_pct']
        
        # Adjust other indicators proportionally
        df['infections_thousands_adjusted'] = df['infections_thousands'] * trans_mult
        df['deaths_thousands_adjusted'] = df['deaths_thousands'] * trans_mult
        df['plhiv_thousands_adjusted'] = df['plhiv_thousands'] * scale_factor
        
        # Return adjusted outputs - match years to targets
        outputs = {}
        
        for indicator, target_dict in self.calibration_targets.items():
            # Get years that have targets for this indicator
            target_years = sorted([int(y) for y in target_dict.keys()])
            
            # Filter model data to matching years
            df_indicator = df[df['year'].isin(target_years)].sort_values('year')
            
            # Map indicator names to dataframe columns
            if indicator == 'hiv_prevalence_15_49':
                outputs[indicator] = df_indicator['prevalence_pct_adjusted'].values
            elif indicator == 'new_hiv_infections':
                outputs[indicator] = df_indicator['infections_thousands_adjusted'].values
            elif indicator == 'hiv_deaths':
                outputs[indicator] = df_indicator['deaths_thousands_adjusted'].values
            elif indicator == 'people_living_with_hiv':
                outputs[indicator] = df_indicator['plhiv_thousands_adjusted'].values
            elif indicator == 'art_coverage':
                outputs[indicator] = df_indicator['art_coverage_pct'].values
            elif indicator == 'population_total':
                outputs[indicator] = df_indicator['population_thousands'].values
        
        return outputs
    
    def calibrate(self, method='differential_evolution', max_iter=100):
        """
        Run calibration optimization.
        
        Parameters:
        -----------
        method : str
            'differential_evolution' or 'minimize'
        max_iter : int
            Maximum optimization iterations
        """
        print("\n" + "="*60)
        print("STARTING MODEL CALIBRATION")
        print("="*60)
        
        print(f"\n🎯 Optimization method: {method}")
        print(f"   Max iterations: {max_iter}")
        print(f"   Parameters to calibrate: {len(self.param_bounds)}")
        
        # Print parameter bounds
        print(f"\n📋 Parameter bounds:")
        for param, (low, high) in self.param_bounds.items():
            print(f"   {param:30s}: [{low:.3f}, {high:.3f}]")
        
        # Initial guess (center of bounds)
        x0 = np.array([(low + high) / 2 for low, high in self.param_bounds.values()])
        bounds = list(self.param_bounds.values())
        
        print(f"\n🔄 Running optimization...")
        
        if method == 'differential_evolution':
            result = differential_evolution(
                self.objective_function,
                bounds=bounds,
                maxiter=max_iter,
                popsize=15,
                atol=1e-4,
                tol=1e-4,
                seed=42,
                disp=True
            )
        else:
            result = minimize(
                self.objective_function,
                x0=x0,
                bounds=bounds,
                method='L-BFGS-B',
                options={'maxiter': max_iter}
            )
        
        optimal_params = self._array_to_dict(result.x)
        
        print(f"\n✅ CALIBRATION COMPLETE")
        print(f"   Final error: {result.fun:.4f}")
        print(f"   Iterations: {len(self.calibration_history)}")
        
        print(f"\n📊 Optimal parameters:")
        for param, value in optimal_params.items():
            print(f"   {param:30s}: {value:.4f}")
        
        return optimal_params, result
    
    def save_results(self, optimal_params, result, output_dir='validation_outputs'):
        """Save calibration results."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save optimal parameters
        params_file = output_path / 'calibrated_parameters.json'
        calibration_results = {
            'optimal_parameters': optimal_params,
            'final_error': float(result.fun),
            'success': bool(result.success),
            'iterations': len(self.calibration_history),
            'parameter_bounds': self.param_bounds,
            'calibration_history': [
                {
                    'iteration': i,
                    'total_error': h['total_error'],
                    'params': h['params']
                }
                for i, h in enumerate(self.calibration_history)
            ]
        }
        
        with open(params_file, 'w') as f:
            json.dump(calibration_results, f, indent=2)
        
        print(f"\n💾 Results saved:")
        print(f"   Parameters: {params_file}")
        
        # Plot convergence
        self.plot_convergence(output_path / 'calibration_convergence.png')
        
        print(f"   Convergence plot: {output_path / 'calibration_convergence.png'}")
    
    def plot_convergence(self, save_path):
        """Plot calibration convergence."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        iterations = range(1, len(self.calibration_history) + 1)
        errors = [h['total_error'] for h in self.calibration_history]
        
        ax.plot(iterations, errors, 'b-', linewidth=2)
        ax.set_xlabel('Iteration', fontsize=12)
        ax.set_ylabel('Total Weighted Error', fontsize=12)
        ax.set_title('Calibration Convergence', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Mark best iteration
        best_idx = np.argmin(errors)
        ax.plot(best_idx + 1, errors[best_idx], 'r*', markersize=20, 
                label=f'Best: {errors[best_idx]:.4f}')
        ax.legend(fontsize=11)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='Calibrate HIVEC-CM model')
    parser.add_argument('--method', default='differential_evolution',
                       choices=['differential_evolution', 'minimize'])
    parser.add_argument('--max-iterations', type=int, default=50)
    parser.add_argument('--targets', default=None)
    
    args = parser.parse_args()
    
    # Use default path if not specified
    if args.targets is None:
        script_dir = Path(__file__).parent
        args.targets = script_dir.parent / 'data' / 'validation_targets' / 'unaids_cameroon_data.json'
    
    calibrator = ModelCalibrator(targets_path=args.targets)
    
    optimal_params, result = calibrator.calibrate(
        method=args.method,
        max_iter=args.max_iterations
    )
    
    calibrator.save_results(optimal_params, result)
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("\n1. Review calibrated parameters in validation_outputs/calibrated_parameters.json")
    print("2. Update model configuration with optimal parameters")
    print("3. Re-run simulation with calibrated parameters")
    print("4. Run validation: python quick_validate.py --period both")
    print("5. Generate diagnostic plots: python generate_diagnostics.py")


if __name__ == '__main__':
    main()
