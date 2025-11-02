#!/usr/bin/env python3
"""
HIVEC-CM Model Validation Framework
====================================
Comprehensive validation of model outputs against UN Population Data Portal targets.

This script:
1. Loads model outputs and UN validation targets
2. Calculates validation metrics (MAE, RMSE, R², NSE, bias, coverage)
3. Generates validation figures
4. Produces validation report for publication

Usage:
    python validate_model.py --scenario S0_baseline --targets un_validation_targets.json
    python validate_model.py --all-scenarios --period validation

Author: HIVEC-CM Model Team
Date: 2024
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


class ModelValidator:
    """Validates HIVEC-CM model outputs against empirical data."""
    
    def __init__(
        self, 
        targets_path: str,
        results_dir: str = "../results",
        output_dir: str = "validation_outputs"
    ):
        """
        Initialize validator.
        
        Parameters:
        -----------
        targets_path : str
            Path to validation targets JSON file
        results_dir : str
            Directory containing model results
        output_dir : str
            Directory for validation outputs
        """
        self.targets_path = Path(targets_path)
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load validation targets
        self.targets = self._load_targets()
        self.acceptance_criteria = self.targets.get('acceptance_criteria', {})
        
        # Results storage
        self.metrics = {}
        self.comparisons = {}
        
    def _load_targets(self) -> Dict:
        """Load validation targets from JSON file."""
        if not self.targets_path.exists():
            raise FileNotFoundError(f"Targets file not found: {self.targets_path}")
        
        with open(self.targets_path, 'r') as f:
            return json.load(f)
    
    def load_model_results(
        self, 
        scenario: str,
        metric_file: str = "prevalence_trends.csv"
    ) -> pd.DataFrame:
        """
        Load model results for a specific scenario.
        
        Parameters:
        -----------
        scenario : str
            Scenario name (e.g., 'S0_baseline')
        metric_file : str
            Name of results file to load
            
        Returns:
        --------
        pd.DataFrame
            Model results
        """
        results_path = self.results_dir / scenario / metric_file
        
        if not results_path.exists():
            logger.warning(f"Results file not found: {results_path}")
            return pd.DataFrame()
        
        return pd.read_csv(results_path)
    
    def calculate_mae(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Mean Absolute Error."""
        return mean_absolute_error(observed, predicted)
    
    def calculate_rmse(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Root Mean Squared Error."""
        return np.sqrt(mean_squared_error(observed, predicted))
    
    def calculate_mape(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error."""
        # Avoid division by zero
        mask = observed != 0
        if not mask.any():
            return np.nan
        return np.mean(np.abs((observed[mask] - predicted[mask]) / observed[mask])) * 100
    
    def calculate_r_squared(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate R-squared (coefficient of determination)."""
        return r2_score(observed, predicted)
    
    def calculate_nash_sutcliffe(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """
        Calculate Nash-Sutcliffe Efficiency (NSE).
        
        NSE = 1 - [Σ(O-P)²] / [Σ(O-Ō)²]
        
        NSE ranges from -∞ to 1:
        - NSE = 1: Perfect match
        - NSE = 0: Model predictions = mean of observations
        - NSE < 0: Model worse than using mean
        """
        numerator = np.sum((observed - predicted) ** 2)
        denominator = np.sum((observed - np.mean(observed)) ** 2)
        
        if denominator == 0:
            return np.nan
        
        return 1 - (numerator / denominator)
    
    def calculate_bias(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate bias (mean difference)."""
        return np.mean(predicted - observed)
    
    def calculate_relative_bias(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate relative bias as percentage."""
        mean_observed = np.mean(observed)
        if mean_observed == 0:
            return np.nan
        return (np.mean(predicted - observed) / mean_observed) * 100
    
    def calculate_coverage_probability(
        self, 
        observed: np.ndarray, 
        predicted_lower: np.ndarray,
        predicted_upper: np.ndarray
    ) -> float:
        """
        Calculate 90% prediction interval coverage probability.
        
        Parameters:
        -----------
        observed : np.ndarray
            Observed values
        predicted_lower : np.ndarray
            Lower bound of 90% prediction interval
        predicted_upper : np.ndarray
            Upper bound of 90% prediction interval
            
        Returns:
        --------
        float
            Proportion of observations within prediction intervals
        """
        within_interval = (observed >= predicted_lower) & (observed <= predicted_upper)
        return np.mean(within_interval)
    
    def validate_indicator(
        self,
        indicator_name: str,
        model_data: pd.DataFrame,
        target_data: Dict[int, float],
        model_col: str = 'value',
        year_col: str = 'year'
    ) -> Dict:
        """
        Validate a single indicator.
        
        Parameters:
        -----------
        indicator_name : str
            Name of indicator being validated
        model_data : pd.DataFrame
            Model predictions with year and value columns
        target_data : dict
            Dictionary mapping year -> target value
        model_col : str
            Column name for model predictions
        year_col : str
            Column name for years
            
        Returns:
        --------
        dict
            Validation metrics
        """
        logger.info(f"Validating {indicator_name}...")
        
        # Align data by year
        years = sorted(target_data.keys())
        observed = np.array([target_data[year] for year in years])
        
        # Extract model predictions for matching years
        model_data_filtered = model_data[model_data[year_col].isin(years)]
        
        if len(model_data_filtered) != len(years):
            logger.warning(
                f"Year mismatch for {indicator_name}: "
                f"expected {len(years)}, got {len(model_data_filtered)}"
            )
            # Fill missing years with NaN
            model_dict = dict(zip(model_data_filtered[year_col], model_data_filtered[model_col]))
            predicted = np.array([model_dict.get(year, np.nan) for year in years])
        else:
            predicted = model_data_filtered[model_col].values
        
        # Remove NaN values
        mask = ~(np.isnan(observed) | np.isnan(predicted))
        observed = observed[mask]
        predicted = predicted[mask]
        years = [y for y, m in zip(years, mask) if m]
        
        if len(observed) == 0:
            logger.warning(f"No valid data points for {indicator_name}")
            return {}
        
        # Calculate metrics
        metrics = {
            'indicator': indicator_name,
            'n_points': len(observed),
            'years': years,
            'mae': self.calculate_mae(observed, predicted),
            'rmse': self.calculate_rmse(observed, predicted),
            'mape': self.calculate_mape(observed, predicted),
            'r_squared': self.calculate_r_squared(observed, predicted),
            'nash_sutcliffe': self.calculate_nash_sutcliffe(observed, predicted),
            'bias': self.calculate_bias(observed, predicted),
            'relative_bias': self.calculate_relative_bias(observed, predicted),
            'observed': observed.tolist(),
            'predicted': predicted.tolist()
        }
        
        # Check against acceptance criteria
        metrics['passes_r2'] = metrics['r_squared'] >= self.acceptance_criteria.get('r_squared', {}).get('threshold', 0.85)
        metrics['passes_bias'] = abs(metrics['relative_bias']) <= self.acceptance_criteria.get('relative_error', {}).get('threshold', 15) * 100
        metrics['passes_nse'] = metrics['nash_sutcliffe'] >= self.acceptance_criteria.get('nash_sutcliffe', {}).get('threshold', 0.70)
        
        metrics['overall_pass'] = all([
            metrics['passes_r2'],
            metrics['passes_bias'],
            metrics['passes_nse']
        ])
        
        return metrics
    
    def validate_scenario(
        self,
        scenario: str,
        period: str = 'calibration'
    ) -> Dict[str, Dict]:
        """
        Validate all indicators for a scenario.
        
        Parameters:
        -----------
        scenario : str
            Scenario name
        period : str
            'calibration' or 'validation'
            
        Returns:
        --------
        dict
            Dictionary of indicator -> metrics
        """
        logger.info(f"Validating scenario {scenario} for {period} period...")
        
        target_period = f"{period}_targets"
        if target_period not in self.targets:
            logger.error(f"No {period} targets found")
            return {}
        
        scenario_metrics = {}
        
        # Load model results
        # Note: This is a simplified example - adapt to your actual model output structure
        model_results = self.load_model_results(scenario)
        
        if model_results.empty:
            logger.warning(f"No model results found for {scenario}")
            return {}
        
        # Validate each target indicator
        for indicator_name, target_data in self.targets[target_period].items():
            if not target_data:  # Skip empty targets
                continue
            
            # Map indicator names to model output columns
            # This mapping needs to be customized based on your model outputs
            indicator_map = {
                'hiv_prevalence_15_49': 'prevalence',
                'new_hiv_infections': 'incidence',
                'hiv_deaths': 'deaths',
                'population_total': 'total_population',
                'births': 'births',
                'deaths': 'total_deaths'
            }
            
            model_col = indicator_map.get(indicator_name)
            if model_col and model_col in model_results.columns:
                metrics = self.validate_indicator(
                    indicator_name=indicator_name,
                    model_data=model_results,
                    target_data=target_data,
                    model_col=model_col
                )
                scenario_metrics[indicator_name] = metrics
        
        return scenario_metrics
    
    def plot_validation_comparison(
        self,
        indicator_name: str,
        metrics: Dict,
        save_path: Optional[Path] = None
    ) -> None:
        """
        Create validation comparison plot.
        
        Parameters:
        -----------
        indicator_name : str
            Name of indicator
        metrics : dict
            Validation metrics including observed and predicted values
        save_path : Path, optional
            Path to save figure
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        years = metrics['years']
        observed = metrics['observed']
        predicted = metrics['predicted']
        
        # Time series comparison
        axes[0].plot(years, observed, 'o-', label='UN Data', linewidth=2, markersize=8)
        axes[0].plot(years, predicted, 's--', label='Model', linewidth=2, markersize=8)
        axes[0].set_xlabel('Year', fontsize=12)
        axes[0].set_ylabel('Value', fontsize=12)
        axes[0].set_title(f'{indicator_name}\nTime Series Comparison', fontsize=14)
        axes[0].legend(fontsize=11)
        axes[0].grid(True, alpha=0.3)
        
        # Scatter plot with 1:1 line
        axes[1].scatter(observed, predicted, s=100, alpha=0.6)
        
        # Add 1:1 line
        min_val = min(observed.min(), predicted.min())
        max_val = max(observed.max(), predicted.max())
        axes[1].plot([min_val, max_val], [min_val, max_val], 'k--', label='1:1 Line', linewidth=2)
        
        axes[1].set_xlabel('UN Data', fontsize=12)
        axes[1].set_ylabel('Model Prediction', fontsize=12)
        axes[1].set_title(
            f'{indicator_name}\nModel vs. Data\n'
            f"R² = {metrics['r_squared']:.3f}, "
            f"NSE = {metrics['nash_sutcliffe']:.3f}",
            fontsize=14
        )
        axes[1].legend(fontsize=11)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved figure to {save_path}")
        
        plt.close()
    
    def generate_validation_report(
        self,
        scenario: str,
        period: str,
        metrics: Dict[str, Dict]
    ) -> None:
        """
        Generate comprehensive validation report.
        
        Parameters:
        -----------
        scenario : str
            Scenario name
        period : str
            'calibration' or 'validation'
        metrics : dict
            Dictionary of indicator metrics
        """
        report_path = self.output_dir / f"validation_report_{scenario}_{period}.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Model Validation Report\n\n")
            f.write(f"**Scenario:** {scenario}\n\n")
            f.write(f"**Period:** {period.capitalize()}\n\n")
            f.write(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
            
            f.write("## Summary\n\n")
            
            # Overall statistics
            n_indicators = len(metrics)
            n_passed = sum(1 for m in metrics.values() if m.get('overall_pass', False))
            
            f.write(f"- **Total Indicators:** {n_indicators}\n")
            f.write(f"- **Passed:** {n_passed} ({n_passed/n_indicators*100:.1f}%)\n")
            f.write(f"- **Failed:** {n_indicators - n_passed}\n\n")
            
            f.write("## Acceptance Criteria\n\n")
            f.write("| Metric | Threshold | Description |\n")
            f.write("|--------|-----------|-------------|\n")
            for metric_name, criteria in self.acceptance_criteria.items():
                f.write(f"| {metric_name} | {criteria['threshold']} | {criteria['description']} |\n")
            f.write("\n")
            
            f.write("## Indicator-Level Results\n\n")
            
            for indicator_name, indicator_metrics in metrics.items():
                status = "✅ PASS" if indicator_metrics.get('overall_pass', False) else "❌ FAIL"
                
                f.write(f"### {indicator_name} {status}\n\n")
                f.write(f"**Data Points:** {indicator_metrics['n_points']}\n\n")
                
                f.write("| Metric | Value | Pass? |\n")
                f.write("|--------|-------|-------|\n")
                f.write(f"| MAE | {indicator_metrics['mae']:.4f} | - |\n")
                f.write(f"| RMSE | {indicator_metrics['rmse']:.4f} | - |\n")
                f.write(f"| MAPE | {indicator_metrics['mape']:.2f}% | - |\n")
                f.write(f"| R² | {indicator_metrics['r_squared']:.4f} | {'✅' if indicator_metrics['passes_r2'] else '❌'} |\n")
                f.write(f"| NSE | {indicator_metrics['nash_sutcliffe']:.4f} | {'✅' if indicator_metrics['passes_nse'] else '❌'} |\n")
                f.write(f"| Bias | {indicator_metrics['bias']:.4f} | - |\n")
                f.write(f"| Relative Bias | {indicator_metrics['relative_bias']:.2f}% | {'✅' if indicator_metrics['passes_bias'] else '❌'} |\n")
                f.write("\n")
                
                # Generate comparison plot
                plot_path = self.output_dir / f"{indicator_name}_{scenario}_{period}.png"
                self.plot_validation_comparison(indicator_name, indicator_metrics, plot_path)
                
                f.write(f"![{indicator_name}]({plot_path.name})\n\n")
        
        logger.info(f"Validation report saved to {report_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Validate HIVEC-CM model against UN data'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        default='S0_baseline',
        help='Scenario to validate'
    )
    parser.add_argument(
        '--period',
        type=str,
        default='calibration',
        choices=['calibration', 'validation', 'both'],
        help='Time period for validation'
    )
    parser.add_argument(
        '--targets',
        type=str,
        default='../data/validation_targets/un_validation_targets.json',
        help='Path to validation targets JSON file'
    )
    parser.add_argument(
        '--all-scenarios',
        action='store_true',
        help='Validate all scenarios'
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = ModelValidator(targets_path=args.targets)
    
    # Determine scenarios to validate
    scenarios = []
    if args.all_scenarios:
        # Find all scenario directories
        results_dir = Path("../results")
        if results_dir.exists():
            scenarios = [d.name for d in results_dir.iterdir() if d.is_dir()]
    else:
        scenarios = [args.scenario]
    
    # Validate each scenario
    for scenario in scenarios:
        logger.info(f"\n{'='*60}")
        logger.info(f"Validating scenario: {scenario}")
        logger.info(f"{'='*60}\n")
        
        periods = ['calibration', 'validation'] if args.period == 'both' else [args.period]
        
        for period in periods:
            metrics = validator.validate_scenario(scenario, period)
            
            if metrics:
                validator.generate_validation_report(scenario, period, metrics)
            else:
                logger.warning(f"No validation metrics generated for {scenario} {period}")
    
    logger.info("\nValidation complete!")


if __name__ == '__main__':
    main()
