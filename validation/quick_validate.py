#!/usr/bin/env python3
"""
Quick Validation Against UNAIDS Data
=====================================
Validates HIVEC-CM model outputs against UNAIDS validation targets.

Usage:
    python quick_validate.py
    python quick_validate.py --scenario S0_baseline --period calibration
    python quick_validate.py --scenario S0_baseline --period validation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import argparse

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 300

class QuickValidator:
    """Quick validation against UNAIDS targets."""
    
    def __init__(self, targets_path='../data/validation_targets/unaids_cameroon_data.json'):
        with open(targets_path, 'r') as f:
            self.targets_data = json.load(f)
        
        self.calibration = self.targets_data['calibration_targets']
        self.validation = self.targets_data['validation_targets']
        self.criteria = self.targets_data['acceptance_criteria']
    
    def load_model_results(self, scenario='S0_baseline'):
        """Load most recent model results for scenario."""
        results_dir = Path(f'../results/montecarlo_scenarios/{scenario}')
        
        # Find most recent run
        run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], reverse=True)
        if not run_dirs:
            raise FileNotFoundError(f"No results found for {scenario}")
        
        latest_run = run_dirs[0]
        print(f"Loading results from: {latest_run}")
        
        # Load summary statistics
        summary_path = latest_run / 'summary_statistics.csv'
        df = pd.read_csv(summary_path)
        
        # ===== APPLY SCALING FACTORS =====
        # Model uses 10,000 agents representing 11.9M people (1990)
        # Scale factor: 11,900,000 / 10,000 = 1,190 people per agent
        
        POPULATION_SCALE = 1190.0  # Each agent represents ~1,190 real people
        
        print(f"\n🔧 Applying scaling factors:")
        print(f"   Population scale: 1 agent = {POPULATION_SCALE:.0f} people")
        
        # Convert prevalence from proportion (0-1) to percentage (0-100)
        # (No population scaling needed - prevalence is already correct proportion)
        df['prevalence_pct'] = df['hiv_prevalence_mean'] * 100
        
        # Convert population from agent count to thousands
        df['population_thousands'] = (df['total_population_mean'] * POPULATION_SCALE) / 1000
        
        # Convert infections from agent count to thousands
        df['infections_thousands'] = (df['new_infections_mean'] * POPULATION_SCALE) / 1000
        
        # Convert deaths from agent count to thousands
        df['deaths_thousands'] = (df['deaths_hiv_mean'] * POPULATION_SCALE) / 1000
        
        # Calculate PLHIV in thousands
        # PLHIV = prevalence × population (both already in correct proportions)
        df['plhiv'] = df['hiv_prevalence_mean'] * df['total_population_mean']
        df['plhiv_thousands'] = (df['plhiv'] * POPULATION_SCALE) / 1000
        
        # Calculate ART coverage as percentage
        df['art_coverage_pct'] = (df['on_art_mean'] / df['plhiv']) * 100
        df['art_coverage_pct'] = df['art_coverage_pct'].fillna(0)
        
        print(f"   ✅ Prevalence: {df['hiv_prevalence_mean'].iloc[0]:.6f} → {df['prevalence_pct'].iloc[0]:.2f}%")
        print(f"   ✅ Population: {df['total_population_mean'].iloc[0]:.0f} agents → {df['population_thousands'].iloc[0]:.1f}k")
        print(f"   ✅ Infections: {df['new_infections_mean'].iloc[0]:.1f} agents → {df['infections_thousands'].iloc[0]:.2f}k")
        
        return df
    
    def calculate_metrics(self, observed, predicted):
        """Calculate all validation metrics."""
        mae = mean_absolute_error(observed, predicted)
        rmse = np.sqrt(mean_squared_error(observed, predicted))
        r2 = r2_score(observed, predicted)
        
        # Nash-Sutcliffe Efficiency
        nse = 1 - np.sum((observed - predicted)**2) / np.sum((observed - np.mean(observed))**2)
        
        # MAPE
        mape = np.mean(np.abs((observed - predicted) / observed)) * 100
        
        # Bias
        bias = np.mean(predicted - observed)
        rel_bias = (bias / np.mean(observed)) * 100
        
        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': r2,
            'nse': nse,
            'bias': bias,
            'rel_bias': rel_bias,
            'n': len(observed)
        }
    
    def validate_indicator(self, df, indicator_name, target_dict, model_col):
        """Validate single indicator."""
        print(f"\nValidating {indicator_name}...")
        
        # Extract target years and values
        years = sorted(target_dict.keys())
        observed = np.array([target_dict[y] for y in years])
        
        # Get model predictions for matching years
        df_filtered = df[df['year'].isin([int(y) for y in years])].copy()
        df_filtered = df_filtered.sort_values('year')
        
        if model_col not in df_filtered.columns:
            print(f"  ⚠️  Column '{model_col}' not found in model outputs")
            return None
        
        predicted = df_filtered[model_col].values
        
        if len(predicted) != len(observed):
            print(f"  ⚠️  Length mismatch: {len(predicted)} vs {len(observed)}")
            return None
        
        # Calculate metrics
        metrics = self.calculate_metrics(observed, predicted)
        metrics['indicator'] = indicator_name
        metrics['years'] = years
        metrics['observed'] = observed.tolist()
        metrics['predicted'] = predicted.tolist()
        
        # Check acceptance criteria
        metrics['pass_r2'] = metrics['r2'] >= self.criteria['r_squared']['threshold']
        metrics['pass_nse'] = metrics['nse'] >= self.criteria['nash_sutcliffe']['threshold']
        metrics['pass_bias'] = abs(metrics['rel_bias']) <= self.criteria['relative_error']['threshold'] * 100
        metrics['overall_pass'] = metrics['pass_r2'] and metrics['pass_nse'] and metrics['pass_bias']
        
        # Print summary
        status = "✅ PASS" if metrics['overall_pass'] else "❌ FAIL"
        print(f"  {status}")
        print(f"  R² = {metrics['r2']:.4f} (threshold: {self.criteria['r_squared']['threshold']})")
        print(f"  NSE = {metrics['nse']:.4f} (threshold: {self.criteria['nash_sutcliffe']['threshold']})")
        print(f"  Rel Bias = {metrics['rel_bias']:.2f}% (threshold: ±{self.criteria['relative_error']['threshold']*100}%)")
        print(f"  MAPE = {metrics['mape']:.2f}%")
        
        return metrics
    
    def plot_comparison(self, metrics, save_path):
        """Create comparison plot."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        years = metrics['years']
        observed = metrics['observed']
        predicted = metrics['predicted']
        
        # Time series
        ax1.plot(years, observed, 'o-', label='UNAIDS Data', linewidth=2, markersize=8)
        ax1.plot(years, predicted, 's--', label='Model', linewidth=2, markersize=6, alpha=0.7)
        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('Value', fontsize=12)
        ax1.set_title(f"{metrics['indicator']}\nTime Series Comparison", fontsize=13)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Scatter plot
        ax2.scatter(observed, predicted, s=100, alpha=0.6)
        
        # 1:1 line
        min_val = min(min(observed), min(predicted))
        max_val = max(max(observed), max(predicted))
        ax2.plot([min_val, max_val], [min_val, max_val], 'k--', label='1:1 Line', linewidth=2)
        
        ax2.set_xlabel('UNAIDS Data', fontsize=12)
        ax2.set_ylabel('Model Prediction', fontsize=12)
        ax2.set_title(
            f"R² = {metrics['r2']:.3f}, NSE = {metrics['nse']:.3f}\n"
            f"Bias = {metrics['rel_bias']:.1f}%",
            fontsize=13
        )
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved plot: {save_path}")
    
    def validate_scenario(self, scenario='S0_baseline', period='calibration'):
        """Validate all indicators for scenario and period."""
        print(f"\n{'='*60}")
        print(f"Validating {scenario} - {period.upper()} period")
        print(f"{'='*60}")
        
        # Load model results
        df = self.load_model_results(scenario)
        
        # Get targets for period
        targets = self.calibration if period == 'calibration' else self.validation
        
        # Map indicator names to SCALED model columns
        indicator_map = {
            'hiv_prevalence_15_49': 'prevalence_pct',  # Now in percentage
            'new_hiv_infections': 'infections_thousands',  # Now in thousands
            'hiv_deaths': 'deaths_thousands',  # Now in thousands
            'people_living_with_hiv': 'plhiv_thousands',  # Now in thousands
            'art_coverage': 'art_coverage_pct',  # Already calculated as percentage
            'population_total': 'population_thousands'  # Now in thousands
        }
        
        # Validate each indicator
        all_metrics = {}
        output_dir = Path('validation_outputs')
        output_dir.mkdir(exist_ok=True)
        
        for indicator_name, target_dict in targets.items():
            if not target_dict:
                continue
            
            model_col = indicator_map.get(indicator_name)
            if model_col is None:
                continue
            
            metrics = self.validate_indicator(df, indicator_name, target_dict, model_col)
            
            if metrics:
                all_metrics[indicator_name] = metrics
                
                # Create plot
                plot_path = output_dir / f"{indicator_name}_{scenario}_{period}.png"
                self.plot_comparison(metrics, plot_path)
        
        # Generate summary report
        self.generate_report(scenario, period, all_metrics, output_dir)
        
        return all_metrics
    
    def generate_report(self, scenario, period, all_metrics, output_dir):
        """Generate markdown validation report."""
        report_path = output_dir / f"validation_report_{scenario}_{period}.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Validation Report: {scenario} - {period.upper()}\n\n")
            f.write(f"**Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            # Summary
            n_total = len(all_metrics)
            n_passed = sum(1 for m in all_metrics.values() if m['overall_pass'])
            
            f.write("## Summary\n\n")
            f.write(f"- **Indicators Validated**: {n_total}\n")
            f.write(f"- **Passed**: {n_passed} ({n_passed/n_total*100:.1f}%)\n")
            f.write(f"- **Failed**: {n_total - n_passed}\n\n")
            
            # Acceptance criteria
            f.write("## Acceptance Criteria\n\n")
            f.write("| Metric | Threshold |\n")
            f.write("|--------|----------|\n")
            f.write(f"| R² | ≥ {self.criteria['r_squared']['threshold']} |\n")
            f.write(f"| NSE | ≥ {self.criteria['nash_sutcliffe']['threshold']} |\n")
            f.write(f"| Relative Bias | ≤ ±{self.criteria['relative_error']['threshold']*100}% |\n\n")
            
            # Individual results
            f.write("## Detailed Results\n\n")
            
            for indicator_name, m in all_metrics.items():
                status = "✅ PASS" if m['overall_pass'] else "❌ FAIL"
                f.write(f"### {indicator_name} {status}\n\n")
                
                f.write("| Metric | Value | Status |\n")
                f.write("|--------|-------|--------|\n")
                f.write(f"| Data Points | {m['n']} | - |\n")
                f.write(f"| MAE | {m['mae']:.4f} | - |\n")
                f.write(f"| RMSE | {m['rmse']:.4f} | - |\n")
                f.write(f"| MAPE | {m['mape']:.2f}% | - |\n")
                f.write(f"| R² | {m['r2']:.4f} | {'✅' if m['pass_r2'] else '❌'} |\n")
                f.write(f"| NSE | {m['nse']:.4f} | {'✅' if m['pass_nse'] else '❌'} |\n")
                f.write(f"| Bias | {m['bias']:.4f} | - |\n")
                f.write(f"| Relative Bias | {m['rel_bias']:.2f}% | {'✅' if m['pass_bias'] else '❌'} |\n\n")
                
                plot_name = f"{indicator_name}_{scenario}_{period}.png"
                f.write(f"![{indicator_name}]({plot_name})\n\n")
        
        print(f"\n✅ Report saved: {report_path}")


def main():
    parser = argparse.ArgumentParser(description='Quick validation against UNAIDS data')
    parser.add_argument('--scenario', default='S0_baseline', help='Scenario name')
    parser.add_argument('--period', default='calibration', choices=['calibration', 'validation', 'both'])
    
    args = parser.parse_args()
    
    validator = QuickValidator()
    
    if args.period == 'both':
        validator.validate_scenario(args.scenario, 'calibration')
        validator.validate_scenario(args.scenario, 'validation')
    else:
        validator.validate_scenario(args.scenario, args.period)


if __name__ == '__main__':
    main()
