#!/usr/bin/env python3
"""
Extended Analysis for Long-term HIV Monte Carlo Study (1985-2100)
Generates comprehensive visualizations and policy analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from datetime import datetime


def load_and_prepare_data(results_file):
    """Load and prepare Monte Carlo results for analysis."""
    print("🎯 LOADING COMPREHENSIVE MONTE CARLO RESULTS")
    print("=" * 60)
    
    df = pd.read_csv(results_file)
    print(f"✅ Loaded {len(df):,} observations")
    print(f"🎲 Scenarios: {list(df['scenario'].unique())}")
    print(f"📊 Replications per scenario: {df.groupby('scenario')['replication'].nunique().to_dict()}")
    print(f"📅 Time period: {df['year'].min()}-{df['year'].max()}")
    print(f"👥 Population size: ~{df['total_population'].mean():.0f} agents")
    
    return df


def create_long_term_trajectory_plot(df, output_dir):
    """Create comprehensive long-term trajectory comparison plot."""
    
    print("\n📈 GENERATING LONG-TERM TRAJECTORY ANALYSIS")
    print("=" * 50)
    
    # Calculate statistics by year and scenario
    trajectory_stats = df.groupby(['year', 'scenario']).agg({
        'prevalence_pct': ['mean', 'std', 'quantile'],
        'incidence_per_1000': ['mean', 'std'],
        'hiv_mortality_per_1000': ['mean', 'std'],
        'art_coverage_pct': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names
    trajectory_stats.columns = ['_'.join(col).strip() if col[1] else col[0] 
                               for col in trajectory_stats.columns.values]
    
    # Rename quantile columns
    trajectory_stats = trajectory_stats.rename(columns={
        'prevalence_pct_quantile': 'prevalence_pct_median'
    })
    
    # Calculate confidence intervals (±1.96*std for 95% CI)
    for metric in ['prevalence_pct', 'incidence_per_1000', 'hiv_mortality_per_1000', 'art_coverage_pct']:
        trajectory_stats[f'{metric}_ci_lower'] = (
            trajectory_stats[f'{metric}_mean'] - 1.96 * trajectory_stats[f'{metric}_std']
        )
        trajectory_stats[f'{metric}_ci_upper'] = (
            trajectory_stats[f'{metric}_mean'] + 1.96 * trajectory_stats[f'{metric}_std']
        )
    
    # Create comprehensive plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('HIV Epidemic Trajectories: Cameroon 1985-2100\n'
                'Impact of Funding Cuts from 2025', fontsize=16, fontweight='bold')
    
    # Define colors
    colors = {'baseline': '#2E8B57', 'funding_cut': '#DC143C'}
    
    # Plot 1: HIV Prevalence
    ax1 = axes[0, 0]
    for scenario in ['baseline', 'funding_cut']:
        data = trajectory_stats[trajectory_stats['scenario_'] == scenario]
        ax1.plot(data['year_'], data['prevalence_pct_mean'], 
                color=colors[scenario], linewidth=2.5, label=scenario.replace('_', ' ').title())
        ax1.fill_between(data['year_'], 
                        data['prevalence_pct_ci_lower'], 
                        data['prevalence_pct_ci_upper'], 
                        color=colors[scenario], alpha=0.2)
    
    ax1.axvline(x=2025, color='gray', linestyle='--', alpha=0.7, label='Funding Cut Begins')
    ax1.set_title('HIV Prevalence Over Time', fontweight='bold')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('HIV Prevalence (%)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: HIV Incidence
    ax2 = axes[0, 1]
    for scenario in ['baseline', 'funding_cut']:
        data = trajectory_stats[trajectory_stats['scenario_'] == scenario]
        ax2.plot(data['year_'], data['incidence_per_1000_mean'], 
                color=colors[scenario], linewidth=2.5, label=scenario.replace('_', ' ').title())
        ax2.fill_between(data['year_'], 
                        data['incidence_per_1000_ci_lower'], 
                        data['incidence_per_1000_ci_upper'], 
                        color=colors[scenario], alpha=0.2)
    
    ax2.axvline(x=2025, color='gray', linestyle='--', alpha=0.7, label='Funding Cut Begins')
    ax2.set_title('HIV Incidence Over Time', fontweight='bold')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Incidence (per 1,000)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: HIV Mortality
    ax3 = axes[1, 0]
    for scenario in ['baseline', 'funding_cut']:
        data = trajectory_stats[trajectory_stats['scenario_'] == scenario]
        ax3.plot(data['year_'], data['hiv_mortality_per_1000_mean'], 
                color=colors[scenario], linewidth=2.5, label=scenario.replace('_', ' ').title())
        ax3.fill_between(data['year_'], 
                        data['hiv_mortality_per_1000_ci_lower'], 
                        data['hiv_mortality_per_1000_ci_upper'], 
                        color=colors[scenario], alpha=0.2)
    
    ax3.axvline(x=2025, color='gray', linestyle='--', alpha=0.7, label='Funding Cut Begins')
    ax3.set_title('HIV Mortality Over Time', fontweight='bold')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('HIV Mortality (per 1,000)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: ART Coverage
    ax4 = axes[1, 1]
    for scenario in ['baseline', 'funding_cut']:
        data = trajectory_stats[trajectory_stats['scenario_'] == scenario]
        ax4.plot(data['year_'], data['art_coverage_pct_mean'], 
                color=colors[scenario], linewidth=2.5, label=scenario.replace('_', ' ').title())
        ax4.fill_between(data['year_'], 
                        data['art_coverage_pct_ci_lower'], 
                        data['art_coverage_pct_ci_upper'], 
                        color=colors[scenario], alpha=0.2)
    
    ax4.axvline(x=2025, color='gray', linestyle='--', alpha=0.7, label='Funding Cut Begins')
    ax4.set_title('ART Coverage Over Time', fontweight='bold')
    ax4.set_xlabel('Year')
    ax4.set_ylabel('ART Coverage (%)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = os.path.join(output_dir, 'comprehensive_long_term_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved comprehensive trajectory plot: {plot_path}")
    
    return trajectory_stats


def create_milestone_analysis(df, output_dir):
    """Create analysis of key milestone years."""
    
    print("\n🎯 MILESTONE YEAR ANALYSIS")
    print("=" * 30)
    
    milestone_years = [1990, 2000, 2010, 2025, 2030, 2040, 2050, 2075, 2100]
    milestone_data = []
    
    for year in milestone_years:
        if year in df['year'].values:
            year_data = df[df['year'] == year]
            for scenario in ['baseline', 'funding_cut']:
                scenario_data = year_data[year_data['scenario'] == scenario]
                if not scenario_data.empty:
                    milestone_data.append({
                        'year': year,
                        'scenario': scenario,
                        'prevalence_mean': scenario_data['prevalence_pct'].mean(),
                        'prevalence_std': scenario_data['prevalence_pct'].std(),
                        'incidence_mean': scenario_data['incidence_per_1000'].mean(),
                        'mortality_mean': scenario_data['hiv_mortality_per_1000'].mean(),
                        'art_coverage_mean': scenario_data['art_coverage_pct'].mean()
                    })
    
    milestone_df = pd.DataFrame(milestone_data)
    
    # Create milestone comparison plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Key Milestone Years: HIV Epidemic Impact Analysis', 
                fontsize=16, fontweight='bold')
    
    colors = {'baseline': '#2E8B57', 'funding_cut': '#DC143C'}
    
    # Prevalence milestones
    ax1 = axes[0]
    for scenario in ['baseline', 'funding_cut']:
        data = milestone_df[milestone_df['scenario'] == scenario]
        ax1.plot(data['year'], data['prevalence_mean'], 
                'o-', color=colors[scenario], linewidth=2.5, markersize=8,
                label=scenario.replace('_', ' ').title())
    
    ax1.axvline(x=2025, color='gray', linestyle='--', alpha=0.7, label='Funding Cut')
    ax1.set_title('HIV Prevalence at Key Milestones', fontweight='bold')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('HIV Prevalence (%)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Incidence milestones
    ax2 = axes[1]
    for scenario in ['baseline', 'funding_cut']:
        data = milestone_df[milestone_df['scenario'] == scenario]
        ax2.plot(data['year'], data['incidence_mean'], 
                'o-', color=colors[scenario], linewidth=2.5, markersize=8,
                label=scenario.replace('_', ' ').title())
    
    ax2.axvline(x=2025, color='gray', linestyle='--', alpha=0.7, label='Funding Cut')
    ax2.set_title('HIV Incidence at Key Milestones', fontweight='bold')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Incidence (per 1,000)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # ART Coverage milestones
    ax3 = axes[2]
    for scenario in ['baseline', 'funding_cut']:
        data = milestone_df[milestone_df['scenario'] == scenario]
        ax3.plot(data['year'], data['art_coverage_mean'], 
                'o-', color=colors[scenario], linewidth=2.5, markersize=8,
                label=scenario.replace('_', ' ').title())
    
    ax3.axvline(x=2025, color='gray', linestyle='--', alpha=0.7, label='Funding Cut')
    ax3.set_title('ART Coverage at Key Milestones', fontweight='bold')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('ART Coverage (%)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = os.path.join(output_dir, 'milestone_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved milestone analysis: {plot_path}")
    
    return milestone_df


def create_impact_summary(df, milestone_df, output_dir):
    """Create comprehensive impact summary."""
    
    print("\n📊 IMPACT SUMMARY GENERATION")
    print("=" * 30)
    
    # Calculate key impacts
    key_years = [2030, 2050, 2075, 2100]
    impacts = {}
    
    for year in key_years:
        year_data = df[df['year'] == year]
        if not year_data.empty:
            baseline_prev = year_data[year_data['scenario'] == 'baseline']['prevalence_pct'].mean()
            funding_cut_prev = year_data[year_data['scenario'] == 'funding_cut']['prevalence_pct'].mean()
            
            if not (np.isnan(baseline_prev) or np.isnan(funding_cut_prev)):
                absolute_diff = funding_cut_prev - baseline_prev
                relative_diff = (absolute_diff / baseline_prev) * 100
                
                impacts[year] = {
                    'baseline_prevalence': baseline_prev,
                    'funding_cut_prevalence': funding_cut_prev,
                    'absolute_difference': absolute_diff,
                    'relative_difference': relative_diff
                }
    
    # Create impact visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Long-term Impact of HIV Funding Cuts: 2030-2100', 
                fontsize=16, fontweight='bold')
    
    years = list(impacts.keys())
    absolute_impacts = [impacts[year]['absolute_difference'] for year in years]
    relative_impacts = [impacts[year]['relative_difference'] for year in years]
    
    # Absolute impact
    bars1 = ax1.bar(years, absolute_impacts, color=['#FFA500', '#FF6347', '#DC143C', '#8B0000'])
    ax1.set_title('Absolute Impact on HIV Prevalence', fontweight='bold')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Additional Prevalence (percentage points)')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars1, absolute_impacts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'+{value:.2f}pp', ha='center', va='bottom', fontweight='bold')
    
    # Relative impact
    bars2 = ax2.bar(years, relative_impacts, color=['#FFA500', '#FF6347', '#DC143C', '#8B0000'])
    ax2.set_title('Relative Impact on HIV Prevalence', fontweight='bold')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Relative Increase (%)')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars2, relative_impacts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'+{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot
    plot_path = os.path.join(output_dir, 'long_term_impact_summary.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved impact summary: {plot_path}")
    
    # Print key findings
    print("\n🎯 KEY LONG-TERM FINDINGS")
    print("=" * 30)
    for year, impact in impacts.items():
        print(f"📅 YEAR {year}:")
        print(f"   Baseline: {impact['baseline_prevalence']:.2f}% prevalence")
        print(f"   Funding Cut: {impact['funding_cut_prevalence']:.2f}% prevalence")
        print(f"   Impact: +{impact['absolute_difference']:.2f}pp (+{impact['relative_difference']:.1f}%)")
        print()
    
    return impacts


def generate_policy_brief(df, impacts, output_dir):
    """Generate policy brief with key statistics."""
    
    print("📋 GENERATING POLICY BRIEF")
    print("=" * 25)
    
    # Calculate overall statistics
    final_year = df['year'].max()
    final_data = df[df['year'] == final_year]
    
    baseline_final = final_data[final_data['scenario'] == 'baseline']['prevalence_pct'].mean()
    funding_cut_final = final_data[final_data['scenario'] == 'funding_cut']['prevalence_pct'].mean()
    
    policy_stats = {
        'study_period': f"{df['year'].min()}-{df['year'].max()}",
        'total_simulations': len(df['replication'].unique()) * len(df['scenario'].unique()),
        'population_size': int(df['total_population'].mean()),
        'final_year_baseline_prevalence': baseline_final,
        'final_year_funding_cut_prevalence': funding_cut_final,
        'final_year_impact': funding_cut_final - baseline_final,
        'final_year_relative_impact': ((funding_cut_final - baseline_final) / baseline_final) * 100,
        'long_term_impacts': impacts
    }
    
    # Save to JSON
    brief_path = os.path.join(output_dir, 'policy_brief.json')
    with open(brief_path, 'w') as f:
        json.dump(policy_stats, f, indent=2, default=str)
    
    print(f"✅ Saved policy brief: {brief_path}")
    
    return policy_stats


def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python extended_analysis.py <results_csv> <output_dir>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = load_and_prepare_data(results_file)
    
    # Generate analyses
    trajectory_stats = create_long_term_trajectory_plot(df, output_dir)
    milestone_df = create_milestone_analysis(df, output_dir)
    impacts = create_impact_summary(df, milestone_df, output_dir)
    policy_stats = generate_policy_brief(df, impacts, output_dir)
    
    print("\n🎉 EXTENDED ANALYSIS COMPLETE!")
    print("=" * 35)
    print(f"📁 Results saved to: {output_dir}")
    print("📊 Generated plots:")
    print("   - comprehensive_long_term_analysis.png")
    print("   - milestone_analysis.png") 
    print("   - long_term_impact_summary.png")
    print("📋 Policy brief: policy_brief.json")


if __name__ == "__main__":
    main()
