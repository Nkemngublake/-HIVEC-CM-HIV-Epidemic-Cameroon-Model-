#!/usr/bin/env python3
"""
Quick Statistical Analysis for Monte Carlo HIV Study Results
Generates key statistics and visualizations for policy analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from datetime import datetime


def load_and_analyze_results(results_file):
    """Load Monte Carlo results and perform key analyses."""
    
    print("🎯 LOADING MONTE CARLO RESULTS")
    print("=" * 50)
    
    # Load data
    df = pd.read_csv(results_file)
    
    print(f"✅ Loaded {len(df):,} observations")
    print(f"🎲 Scenarios: {list(df['scenario'].unique())}")
    print(f"📊 Replications per scenario: {df.groupby('scenario')['replication'].nunique().to_dict()}")
    print(f"📅 Time period: {df['year'].min()}-{df['year'].max()}")
    
    return df


def calculate_key_statistics(df):
    """Calculate key statistics for policy analysis."""
    
    print("\n📈 KEY FINDINGS ANALYSIS")
    print("=" * 50)
    
    # Key years for analysis
    key_years = [2025, 2030, 2040, 2050]
    results = {}
    
    for year in key_years:
        if year in df['year'].values:
            year_data = df[df['year'] == year]
            year_results = {}
            
            print(f"\n📅 YEAR {year}")
            print("-" * 15)
            
            for scenario in ['baseline', 'funding_cut']:
                scenario_data = year_data[year_data['scenario'] == scenario]
                
                if not scenario_data.empty:
                    # Key metrics
                    prevalence_mean = scenario_data['prevalence_pct'].mean()
                    prevalence_std = scenario_data['prevalence_pct'].std()
                    prevalence_ci = 1.96 * prevalence_std / np.sqrt(len(scenario_data))
                    
                    incidence_mean = scenario_data['incidence_per_1000'].mean()
                    mortality_mean = scenario_data['hiv_mortality_per_1000'].mean()
                    
                    year_results[scenario] = {
                        'prevalence_mean': prevalence_mean,
                        'prevalence_std': prevalence_std,
                        'prevalence_ci': prevalence_ci,
                        'incidence_mean': incidence_mean,
                        'mortality_mean': mortality_mean
                    }
                    
                    print(f"{scenario.upper():>12}: {prevalence_mean:.2f}% (±{prevalence_ci:.2f}%) prevalence")
                    print(f"{'':>12}  {incidence_mean:.2f} incidence per 1000")
            
            # Calculate impact if both scenarios exist
            if 'baseline' in year_results and 'funding_cut' in year_results:
                baseline_prev = year_results['baseline']['prevalence_mean']
                funding_cut_prev = year_results['funding_cut']['prevalence_mean']
                
                absolute_diff = funding_cut_prev - baseline_prev
                relative_diff = (absolute_diff / baseline_prev) * 100 if baseline_prev > 0 else 0
                
                year_results['impact'] = {
                    'absolute_difference': absolute_diff,
                    'relative_difference': relative_diff
                }
                
                print(f"{'IMPACT':>12}: {absolute_diff:+.2f} pp ({relative_diff:+.1f}%)")
            
            results[year] = year_results
    
    return results


def create_trajectory_plot(df, output_dir):
    """Create trajectory comparison plot."""
    
    print("\n📊 GENERATING TRAJECTORY PLOTS")
    print("=" * 35)
    
    # Setup plot style
    plt.style.use('default')
    sns.set_palette("husl")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    metrics = [
        ('prevalence_pct', 'HIV Prevalence (%)'),
        ('incidence_per_1000', 'HIV Incidence (per 1000)'),
        ('hiv_mortality_per_1000', 'HIV Mortality (per 1000)'),
        ('art_coverage_pct', 'ART Coverage (%)')
    ]
    
    colors = {'baseline': '#2E86AB', 'funding_cut': '#A23B72'}
    
    for i, (metric, title) in enumerate(metrics):
        ax = axes[i//2, i%2]
        
        for scenario in ['baseline', 'funding_cut']:
            scenario_data = df[df['scenario'] == scenario]
            
            # Calculate yearly means and confidence intervals
            yearly_stats = scenario_data.groupby('year')[metric].agg(['mean', 'std', 'count'])
            yearly_stats['ci'] = 1.96 * yearly_stats['std'] / np.sqrt(yearly_stats['count'])
            
            # Plot mean trajectory
            years = yearly_stats.index
            means = yearly_stats['mean']
            cis = yearly_stats['ci']
            
            label = scenario.replace('_', ' ').title()
            ax.plot(years, means, color=colors[scenario], linewidth=2.5, 
                   label=label, marker='o', markersize=3)
            
            # Add confidence interval
            ax.fill_between(years, means - cis, means + cis, 
                          color=colors[scenario], alpha=0.2)
        
        # Add funding cut indicator
        ax.axvline(x=2025, color='red', linestyle='--', alpha=0.7, linewidth=1)
        ax.text(2025, ax.get_ylim()[1]*0.9, 'Funding\nCut', ha='center', 
               fontsize=9, color='red')
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Year')
        ax.set_ylabel(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('HIV Epidemic Trajectories: Baseline vs Funding Cut Scenarios', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, 'trajectory_comparison.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved trajectory plot: {plot_path}")
    return plot_path


def create_impact_summary(df, statistics, output_dir):
    """Create executive summary of impacts."""
    
    print("\n📋 GENERATING IMPACT SUMMARY")
    print("=" * 35)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Final year comparison (top left)
    ax1 = axes[0, 0]
    final_year = df['year'].max()
    final_data = df[df['year'] == final_year]
    
    sns.boxplot(data=final_data, x='scenario', y='prevalence_pct', ax=ax1)
    ax1.set_title(f'HIV Prevalence in {final_year}', fontweight='bold')
    ax1.set_xlabel('Scenario')
    ax1.set_ylabel('Prevalence (%)')
    
    # Add mean markers
    for i, scenario in enumerate(['baseline', 'funding_cut']):
        scenario_data = final_data[final_data['scenario'] == scenario]
        mean_val = scenario_data['prevalence_pct'].mean()
        ax1.scatter(i, mean_val, color='red', s=100, marker='D', zorder=10)
    
    # 2. Timeline of impacts (top right)
    ax2 = axes[0, 1]
    
    impact_years = []
    impact_values = []
    
    for year in [2025, 2030, 2040, 2050]:
        if year in statistics and 'impact' in statistics[year]:
            impact_years.append(year)
            impact_values.append(statistics[year]['impact']['relative_difference'])
    
    if impact_values:
        ax2.bar(impact_years, impact_values, color=['orange' if x < 0 else 'red' for x in impact_values])
        ax2.set_title('Relative Impact Over Time', fontweight='bold')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Relative Change in Prevalence (%)')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax2.grid(True, alpha=0.3)
    
    # 3. Cumulative infections (bottom left)
    ax3 = axes[1, 0]
    
    cumulative_infections = df.groupby(['scenario', 'replication'])['new_infections'].sum().reset_index()
    sns.violinplot(data=cumulative_infections, x='scenario', y='new_infections', ax=ax3)
    ax3.set_title('Cumulative New Infections (1990-2050)', fontweight='bold')
    ax3.set_xlabel('Scenario')
    ax3.set_ylabel('Total New Infections')
    
    # 4. Key statistics table (bottom right)
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Create summary text
    if 2050 in statistics and 'impact' in statistics[2050]:
        final_impact = statistics[2050]['impact']
        baseline_prev = statistics[2050]['baseline']['prevalence_mean']
        funding_cut_prev = statistics[2050]['funding_cut']['prevalence_mean']
        
        summary_text = f"""
        🎯 EXECUTIVE SUMMARY
        
        By 2050, HIV funding cuts would result in:
        
        • Baseline scenario: {baseline_prev:.2f}% prevalence
        • Funding cut scenario: {funding_cut_prev:.2f}% prevalence
        
        • Absolute difference: {final_impact['absolute_difference']:+.2f} percentage points
        • Relative increase: {final_impact['relative_difference']:+.1f}%
        
        💡 POLICY IMPLICATIONS:
        
        • Funding cuts prevent epidemic control
        • {abs(final_impact['relative_difference']):.0f}% higher burden in 2050
        • Sustained transmission vs. elimination
        
        📊 STUDY PARAMETERS:
        
        • {len(df['replication'].unique())} replications per scenario
        • {df['total_population'].iloc[0]:,} agents per simulation
        • 60-year projection (1990-2050)
        • 30% ART funding cut from 2025
        • 40% prevention cut for key populations
        """
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    
    # Save plot
    summary_path = os.path.join(output_dir, 'executive_summary.png')
    plt.savefig(summary_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved executive summary: {summary_path}")
    return summary_path


def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python quick_analysis.py <results_csv> <output_dir>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Load and analyze
    df = load_and_analyze_results(results_file)
    statistics = calculate_key_statistics(df)
    
    # Generate visualizations
    trajectory_plot = create_trajectory_plot(df, output_dir)
    summary_plot = create_impact_summary(df, statistics, output_dir)
    
    # Save statistics
    stats_file = os.path.join(output_dir, 'key_statistics.json')
    with open(stats_file, 'w') as f:
        json.dump(statistics, f, indent=2, default=str)
    
    print(f"\n🎉 ANALYSIS COMPLETE!")
    print("=" * 25)
    print(f"📁 Results saved to: {output_dir}")
    print(f"📊 Trajectory plot: trajectory_comparison.png")
    print(f"📋 Executive summary: executive_summary.png") 
    print(f"📈 Statistics: key_statistics.json")


if __name__ == "__main__":
    main()
