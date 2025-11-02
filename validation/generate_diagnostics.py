#!/usr/bin/env python3
"""
Advanced Diagnostic Visualizations
===================================
Creates comprehensive diagnostic plots for model validation.

Generates:
1. Multi-panel trajectory comparison
2. Residual analysis plots  
3. Goodness-of-fit assessment
4. Time-varying error analysis
5. Parameter sensitivity analysis (if calibration results available)

Usage:
    python generate_diagnostics.py
    python generate_diagnostics.py --scenario S0_baseline --output-dir diagnostics
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import argparse
from scipy import stats

sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 300


class DiagnosticPlotter:
    """Creates comprehensive diagnostic visualizations."""
    
    def __init__(self, scenario='S0_baseline', 
                 targets_path='../data/validation_targets/unaids_cameroon_data.json'):
        self.scenario = scenario
        
        # Load targets
        with open(targets_path, 'r') as f:
            self.targets_data = json.load(f)
        
        self.calibration_targets = self.targets_data['calibration_targets']
        self.validation_targets = self.targets_data['validation_targets']
        
        # Load model results
        self.model_data = self._load_model_results()
    
    def _load_model_results(self):
        """Load and scale model results."""
        results_dir = Path(f'../results/montecarlo_scenarios/{self.scenario}')
        run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], reverse=True)
        
        if not run_dirs:
            raise FileNotFoundError(f"No results found for {self.scenario}")
        
        latest_run = run_dirs[0]
        summary_path = latest_run / 'summary_statistics.csv'
        df = pd.read_csv(summary_path)
        
        # Apply scaling
        POPULATION_SCALE = 1190.0
        df['prevalence_pct'] = df['hiv_prevalence_mean'] * 100
        df['population_thousands'] = (df['total_population_mean'] * POPULATION_SCALE) / 1000
        df['infections_thousands'] = (df['new_infections_mean'] * POPULATION_SCALE) / 1000
        df['deaths_thousands'] = (df['deaths_hiv_mean'] * POPULATION_SCALE) / 1000
        df['plhiv'] = df['hiv_prevalence_mean'] * df['total_population_mean']
        df['plhiv_thousands'] = (df['plhiv'] * POPULATION_SCALE) / 1000
        df['art_coverage_pct'] = (df['on_art_mean'] / df['plhiv']) * 100
        df['art_coverage_pct'] = df['art_coverage_pct'].fillna(0)
        
        return df
    
    def plot_comprehensive_comparison(self, save_path, period='calibration'):
        """Create multi-panel comparison of all indicators."""
        targets = self.calibration_targets if period == 'calibration' else self.validation_targets
        
        indicators = [
            ('hiv_prevalence_15_49', 'prevalence_pct', 'HIV Prevalence (%)', 'A'),
            ('new_hiv_infections', 'infections_thousands', 'New Infections (thousands)', 'B'),
            ('hiv_deaths', 'deaths_thousands', 'HIV Deaths (thousands)', 'C'),
            ('people_living_with_hiv', 'plhiv_thousands', 'PLHIV (thousands)', 'D'),
            ('art_coverage', 'art_coverage_pct', 'ART Coverage (%)', 'E'),
            ('population_total', 'population_thousands', 'Population (thousands)', 'F')
        ]
        
        fig, axes = plt.subplots(3, 2, figsize=(16, 14))
        axes = axes.ravel()
        
        for idx, (target_name, model_col, ylabel, panel_letter) in enumerate(indicators):
            ax = axes[idx]
            
            if target_name not in targets or not targets[target_name]:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center')
                ax.set_title(f'{panel_letter}) {ylabel}')
                continue
            
            # Get target data
            target_dict = targets[target_name]
            years = sorted(map(int, target_dict.keys()))
            target_vals = [target_dict[str(y)] for y in years]
            
            # Get model data
            model_df = self.model_data[self.model_data['year'].isin(years)]
            model_vals = [model_df[model_df['year']==y][model_col].values[0] 
                         for y in years if y in model_df['year'].values]
            
            # Plot
            ax.plot(years, target_vals, 'o-', label='UNAIDS Data', 
                   linewidth=2.5, markersize=8, color='#2E86AB')
            ax.plot(years[:len(model_vals)], model_vals, 's--', label='Model', 
                   linewidth=2.5, markersize=6, color='#A23B72', alpha=0.7)
            
            # Calculate and show R²
            if len(model_vals) == len(target_vals):
                r2 = 1 - np.sum((np.array(target_vals) - np.array(model_vals))**2) / \
                         np.sum((np.array(target_vals) - np.mean(target_vals))**2)
                ax.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax.transAxes,
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                       verticalalignment='top', fontsize=10)
            
            ax.set_xlabel('Year', fontsize=11)
            ax.set_ylabel(ylabel, fontsize=11)
            ax.set_title(f'{panel_letter}) {ylabel}', fontsize=12, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
        
        plt.suptitle(f'Model vs. UNAIDS Data Comparison ({period.upper()} Period)',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved comprehensive comparison: {save_path}")
    
    def plot_residual_analysis(self, save_path, period='calibration'):
        """Create residual analysis plots."""
        targets = self.calibration_targets if period == 'calibration' else self.validation_targets
        
        indicators = [
            ('hiv_prevalence_15_49', 'prevalence_pct', 'Prevalence'),
            ('new_hiv_infections', 'infections_thousands', 'Infections'),
            ('hiv_deaths', 'deaths_thousands', 'Deaths'),
            ('people_living_with_hiv', 'plhiv_thousands', 'PLHIV')
        ]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.ravel()
        
        for idx, (target_name, model_col, label) in enumerate(indicators):
            ax = axes[idx]
            
            if target_name not in targets or not targets[target_name]:
                continue
            
            # Get data
            target_dict = targets[target_name]
            years = sorted(map(int, target_dict.keys()))
            target_vals = np.array([target_dict[str(y)] for y in years])
            
            model_df = self.model_data[self.model_data['year'].isin(years)]
            model_vals = np.array([model_df[model_df['year']==y][model_col].values[0] 
                                  for y in years if y in model_df['year'].values])
            
            if len(model_vals) != len(target_vals):
                continue
            
            # Calculate residuals
            residuals = target_vals - model_vals
            rel_residuals = (residuals / target_vals) * 100  # Percentage
            
            # Plot residuals over time
            ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
            ax.plot(years, rel_residuals, 'o-', linewidth=2, markersize=6)
            ax.fill_between(years, -15, 15, alpha=0.2, color='green', 
                           label='±15% (acceptance)')
            
            ax.set_xlabel('Year', fontsize=11)
            ax.set_ylabel('Relative Residual (%)', fontsize=11)
            ax.set_title(f'{label} - Residuals Over Time', fontsize=12, fontweight='bold')
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
            
            # Add mean/std text
            mean_res = np.mean(np.abs(rel_residuals))
            std_res = np.std(rel_residuals)
            ax.text(0.95, 0.95, f'Mean |error|: {mean_res:.1f}%\nStd: {std_res:.1f}%',
                   transform=ax.transAxes, verticalalignment='top', 
                   horizontalalignment='right', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        plt.suptitle(f'Residual Analysis ({period.upper()} Period)',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved residual analysis: {save_path}")
    
    def plot_goodness_of_fit(self, save_path, period='calibration'):
        """Create goodness-of-fit scatter plots."""
        targets = self.calibration_targets if period == 'calibration' else self.validation_targets
        
        indicators = [
            ('hiv_prevalence_15_49', 'prevalence_pct', 'Prevalence (%)'),
            ('new_hiv_infections', 'infections_thousands', 'Infections (thousands)'),
            ('hiv_deaths', 'deaths_thousands', 'Deaths (thousands)'),
            ('people_living_with_hiv', 'plhiv_thousands', 'PLHIV (thousands)')
        ]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        axes = axes.ravel()
        
        for idx, (target_name, model_col, label) in enumerate(indicators):
            ax = axes[idx]
            
            if target_name not in targets or not targets[target_name]:
                continue
            
            # Get data
            target_dict = targets[target_name]
            years = sorted(map(int, target_dict.keys()))
            target_vals = np.array([target_dict[str(y)] for y in years])
            
            model_df = self.model_data[self.model_data['year'].isin(years)]
            model_vals = np.array([model_df[model_df['year']==y][model_col].values[0] 
                                  for y in years if y in model_df['year'].values])
            
            if len(model_vals) != len(target_vals):
                continue
            
            # Scatter plot
            ax.scatter(target_vals, model_vals, s=100, alpha=0.6, c=years, cmap='viridis')
            
            # 1:1 line
            min_val = min(target_vals.min(), model_vals.min())
            max_val = max(target_vals.max(), model_vals.max())
            ax.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=2, 
                   label='1:1 Line', alpha=0.7)
            
            # Fit line
            z = np.polyfit(target_vals, model_vals, 1)
            p = np.poly1d(z)
            ax.plot(target_vals, p(target_vals), 'r-', linewidth=2, alpha=0.7,
                   label=f'Fit: y={z[0]:.2f}x+{z[1]:.2f}')
            
            # Calculate metrics
            r2 = 1 - np.sum((target_vals - model_vals)**2) / \
                     np.sum((target_vals - np.mean(target_vals))**2)
            rmse = np.sqrt(np.mean((target_vals - model_vals)**2))
            
            ax.set_xlabel(f'UNAIDS Data: {label}', fontsize=11)
            ax.set_ylabel(f'Model Output: {label}', fontsize=11)
            ax.set_title(f'{label}\nR² = {r2:.3f}, RMSE = {rmse:.2f}', 
                        fontsize=12, fontweight='bold')
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
        
        plt.suptitle(f'Goodness of Fit Assessment ({period.upper()} Period)',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved goodness-of-fit plots: {save_path}")
    
    def plot_trajectory_uncertainty(self, save_path):
        """Plot model trajectory with uncertainty bounds."""
        # Load raw results for uncertainty quantification
        results_dir = Path(f'../results/montecarlo_scenarios/{self.scenario}')
        run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], reverse=True)
        latest_run = run_dirs[0]
        raw_path = latest_run / 'raw_results.csv'
        
        if not raw_path.exists():
            print("⚠️  Raw results not found - skipping uncertainty plot")
            return
        
        raw_df = pd.read_csv(raw_path)
        
        # Apply scaling
        POPULATION_SCALE = 1190.0
        raw_df['prevalence_pct'] = raw_df['hiv_prevalence'] * 100
        
        # Calculate percentiles
        summary = raw_df.groupby('year')['prevalence_pct'].agg([
            ('mean', 'mean'),
            ('p5', lambda x: np.percentile(x, 5)),
            ('p25', lambda x: np.percentile(x, 25)),
            ('p75', lambda x: np.percentile(x, 75)),
            ('p95', lambda x: np.percentile(x, 95))
        ]).reset_index()
        
        # Get UNAIDS data
        targets = self.calibration_targets['hiv_prevalence_15_49']
        target_years = sorted(map(int, targets.keys()))
        target_vals = [targets[str(y)] for y in target_years]
        
        # Plot
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Model trajectories
        ax.fill_between(summary['year'], summary['p5'], summary['p95'], 
                       alpha=0.2, color='blue', label='90% PI')
        ax.fill_between(summary['year'], summary['p25'], summary['p75'], 
                       alpha=0.3, color='blue', label='50% PI')
        ax.plot(summary['year'], summary['mean'], 'b-', linewidth=2.5, label='Model Mean')
        
        # UNAIDS data
        ax.plot(target_years, target_vals, 'ro-', linewidth=2.5, markersize=10, 
               label='UNAIDS Data', alpha=0.8)
        
        ax.set_xlabel('Year', fontsize=13)
        ax.set_ylabel('HIV Prevalence (%)', fontsize=13)
        ax.set_title('HIV Prevalence Trajectory with Uncertainty', 
                    fontsize=15, fontweight='bold')
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(1990, 2023)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved uncertainty plot: {save_path}")
    
    def generate_all_diagnostics(self, output_dir='validation_outputs/diagnostics'):
        """Generate all diagnostic plots."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*60)
        print("GENERATING DIAGNOSTIC VISUALIZATIONS")
        print("="*60)
        
        # 1. Comprehensive comparison
        print("\n📊 Creating comprehensive comparison plots...")
        self.plot_comprehensive_comparison(
            output_path / 'comprehensive_comparison_calibration.png',
            period='calibration'
        )
        self.plot_comprehensive_comparison(
            output_path / 'comprehensive_comparison_validation.png',
            period='validation'
        )
        
        # 2. Residual analysis
        print("\n📉 Creating residual analysis plots...")
        self.plot_residual_analysis(
            output_path / 'residual_analysis_calibration.png',
            period='calibration'
        )
        self.plot_residual_analysis(
            output_path / 'residual_analysis_validation.png',
            period='validation'
        )
        
        # 3. Goodness of fit
        print("\n🎯 Creating goodness-of-fit plots...")
        self.plot_goodness_of_fit(
            output_path / 'goodness_of_fit_calibration.png',
            period='calibration'
        )
        self.plot_goodness_of_fit(
            output_path / 'goodness_of_fit_validation.png',
            period='validation'
        )
        
        # 4. Trajectory uncertainty
        print("\n📈 Creating uncertainty visualization...")
        self.plot_trajectory_uncertainty(
            output_path / 'trajectory_uncertainty.png'
        )
        
        print("\n" + "="*60)
        print("DIAGNOSTIC GENERATION COMPLETE")
        print("="*60)
        print(f"\n📁 All plots saved to: {output_path}")
        print("\nGenerated files:")
        for f in sorted(output_path.glob('*.png')):
            print(f"   - {f.name}")


def main():
    parser = argparse.ArgumentParser(description='Generate diagnostic visualizations')
    parser.add_argument('--scenario', default='S0_baseline', help='Scenario name')
    parser.add_argument('--output-dir', default='validation_outputs/diagnostics',
                       help='Output directory')
    
    args = parser.parse_args()
    
    plotter = DiagnosticPlotter(scenario=args.scenario)
    plotter.generate_all_diagnostics(output_dir=args.output_dir)
    
    print("\n✅ Diagnostic visualization complete!")
    print("\nReview the plots to:")
    print("   - Assess model fit quality")
    print("   - Identify systematic biases")
    print("   - Understand uncertainty ranges")
    print("   - Guide further calibration")


if __name__ == '__main__':
    main()
