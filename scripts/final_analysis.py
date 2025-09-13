#!/usr/bin/env python3
"""
Comprehensive Analysis for 1985-2100 HIV Monte Carlo Study
Generates publication-quality visualizations and policy analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os


def load_data(results_file):
    """Load and examine Monte Carlo results."""
    print("🎯 LOADING MONTE CARLO RESULTS (1985-2100)")
    print("=" * 50)
    
    df = pd.read_csv(results_file)
    print(f"✅ Loaded {len(df):,} observations")
    print(f"🎲 Scenarios: {list(df['scenario'].unique())}")
    print(f"📊 Replications per scenario: {df.groupby('scenario')['replication'].nunique().to_dict()}")
    print(f"📅 Time period: {df['year'].min()}-{df['year'].max()}")
    print(f"👥 Average population: {df['total_population'].mean():.0f}")
    
    return df


def create_comprehensive_trajectory_plot(df, output_dir):
    """Create main trajectory analysis plot."""
    
    print("\n📈 GENERATING COMPREHENSIVE TRAJECTORY PLOT")
    print("=" * 45)
    
    # Calculate summary statistics
    summary = df.groupby(['year', 'scenario']).agg({
        'prevalence_pct': ['mean', 'std'],
        'incidence_per_1000': ['mean', 'std'],
        'hiv_mortality_per_1000': ['mean', 'std'],
        'art_coverage_pct': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names
    summary.columns = ['year', 'scenario', 
                      'prev_mean', 'prev_std',
                      'inc_mean', 'inc_std', 
                      'mort_mean', 'mort_std',
                      'art_mean', 'art_std']
    
    # Calculate confidence intervals
    summary['prev_ci_lower'] = summary['prev_mean'] - 1.96 * summary['prev_std']
    summary['prev_ci_upper'] = summary['prev_mean'] + 1.96 * summary['prev_std']
    summary['inc_ci_lower'] = summary['inc_mean'] - 1.96 * summary['inc_std']
    summary['inc_ci_upper'] = summary['inc_mean'] + 1.96 * summary['inc_std']
    
    # Create plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('HIV Epidemic Trajectories: Cameroon 1985-2100\\n'
                'Long-term Impact of HIV Funding Cuts', 
                fontsize=16, fontweight='bold')
    
    colors = {'baseline': '#2E8B57', 'funding_cut': '#DC143C'}
    
    # HIV Prevalence
    ax1 = axes[0, 0]
    for scenario in ['baseline', 'funding_cut']:
        data = summary[summary['scenario'] == scenario]
        ax1.plot(data['year'], data['prev_mean'], 
                color=colors[scenario], linewidth=3, 
                label=scenario.replace('_', ' ').title())
        ax1.fill_between(data['year'], data['prev_ci_lower'], data['prev_ci_upper'], 
                        color=colors[scenario], alpha=0.2)
    
    ax1.axvline(x=2025, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Funding Cut Begins')
    ax1.set_title('HIV Prevalence Over Time', fontweight='bold', fontsize=12)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('HIV Prevalence (%)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(1985, 2100)
    
    # HIV Incidence  
    ax2 = axes[0, 1]
    for scenario in ['baseline', 'funding_cut']:
        data = summary[summary['scenario'] == scenario]
        ax2.plot(data['year'], data['inc_mean'], 
                color=colors[scenario], linewidth=3,
                label=scenario.replace('_', ' ').title())
        ax2.fill_between(data['year'], data['inc_ci_lower'], data['inc_ci_upper'], 
                        color=colors[scenario], alpha=0.2)
    
    ax2.axvline(x=2025, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Funding Cut Begins')
    ax2.set_title('HIV Incidence Over Time', fontweight='bold', fontsize=12)
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Incidence (per 1,000)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(1985, 2100)
    
    # HIV Mortality
    ax3 = axes[1, 0]
    for scenario in ['baseline', 'funding_cut']:
        data = summary[summary['scenario'] == scenario]
        ax3.plot(data['year'], data['mort_mean'], 
                color=colors[scenario], linewidth=3,
                label=scenario.replace('_', ' ').title())
    
    ax3.axvline(x=2025, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Funding Cut Begins')
    ax3.set_title('HIV Mortality Over Time', fontweight='bold', fontsize=12)
    ax3.set_xlabel('Year')
    ax3.set_ylabel('HIV Mortality (per 1,000)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(1985, 2100)
    
    # ART Coverage
    ax4 = axes[1, 1]
    for scenario in ['baseline', 'funding_cut']:
        data = summary[summary['scenario'] == scenario]
        ax4.plot(data['year'], data['art_mean'], 
                color=colors[scenario], linewidth=3,
                label=scenario.replace('_', ' ').title())
    
    ax4.axvline(x=2025, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Funding Cut Begins')
    ax4.set_title('ART Coverage Over Time', fontweight='bold', fontsize=12)
    ax4.set_xlabel('Year')
    ax4.set_ylabel('ART Coverage (%)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(1985, 2100)
    
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, 'comprehensive_1985_2100_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved comprehensive plot: {plot_path}")
    return summary


def create_key_year_analysis(df, output_dir):
    """Analyze key milestone years."""
    
    print("\n🎯 KEY YEAR IMPACT ANALYSIS")
    print("=" * 30)
    
    key_years = [2025, 2030, 2040, 2050, 2075, 2100]
    results = []
    
    for year in key_years:
        year_data = df[df['year'] == year]
        if not year_data.empty:
            baseline = year_data[year_data['scenario'] == 'baseline']['prevalence_pct'].mean()
            funding_cut = year_data[year_data['scenario'] == 'funding_cut']['prevalence_pct'].mean()
            
            if not (pd.isna(baseline) or pd.isna(funding_cut)):
                diff = funding_cut - baseline
                rel_diff = (diff / baseline) * 100
                
                results.append({
                    'year': year,
                    'baseline_prevalence': baseline,
                    'funding_cut_prevalence': funding_cut,
                    'absolute_difference': diff,
                    'relative_difference': rel_diff
                })
                
                print(f"📅 {year}: Baseline {baseline:.2f}% → Funding Cut {funding_cut:.2f}% "
                      f"(+{diff:.2f}pp, +{rel_diff:.1f}%)")
    
    # Create impact visualization
    if results:
        years = [r['year'] for r in results]
        abs_diffs = [r['absolute_difference'] for r in results]
        rel_diffs = [r['relative_difference'] for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Long-term Impact of HIV Funding Cuts: Key Milestones', 
                    fontsize=16, fontweight='bold')
        
        # Absolute impact
        colors = ['orange' if y < 2050 else 'red' for y in years]
        bars1 = ax1.bar(years, abs_diffs, color=colors, alpha=0.8)
        ax1.set_title('Absolute Impact on HIV Prevalence', fontweight='bold')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Additional Prevalence (percentage points)')
        ax1.grid(True, alpha=0.3)
        
        for bar, value in zip(bars1, abs_diffs):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'+{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Relative impact
        bars2 = ax2.bar(years, rel_diffs, color=colors, alpha=0.8)
        ax2.set_title('Relative Impact on HIV Prevalence', fontweight='bold')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Relative Increase (%)')
        ax2.grid(True, alpha=0.3)
        
        for bar, value in zip(bars2, rel_diffs):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'+{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        plot_path = os.path.join(output_dir, 'key_year_impacts.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved key year analysis: {plot_path}")
    
    return results


def create_epidemic_phases_analysis(df, output_dir):
    """Analyze different phases of the epidemic."""
    
    print("\n📊 EPIDEMIC PHASES ANALYSIS")
    print("=" * 30)
    
    # Define epidemic phases
    phases = {
        'Pre-epidemic (1985-1990)': (1985, 1990),
        'Emergence (1990-2000)': (1990, 2000),
        'Expansion (2000-2010)': (2000, 2010),
        'Scale-up (2010-2025)': (2010, 2025),
        'Post-funding cut (2025-2050)': (2025, 2050),
        'Long-term (2050-2100)': (2050, 2100)
    }
    
    phase_data = []
    
    for phase_name, (start_year, end_year) in phases.items():
        phase_df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
        
        if not phase_df.empty:
            for scenario in ['baseline', 'funding_cut']:
                scenario_data = phase_df[phase_df['scenario'] == scenario]
                if not scenario_data.empty:
                    avg_prevalence = scenario_data['prevalence_pct'].mean()
                    avg_incidence = scenario_data['incidence_per_1000'].mean()
                    avg_mortality = scenario_data['hiv_mortality_per_1000'].mean()
                    
                    phase_data.append({
                        'phase': phase_name,
                        'scenario': scenario,
                        'avg_prevalence': avg_prevalence,
                        'avg_incidence': avg_incidence,
                        'avg_mortality': avg_mortality
                    })
    
    # Create phase comparison plot
    if phase_data:
        phase_df = pd.DataFrame(phase_data)
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('HIV Epidemic by Phases: 1985-2100', fontsize=16, fontweight='bold')
        
        phases_order = list(phases.keys())
        
        # Prevalence by phase
        ax1 = axes[0]
        baseline_prev = [phase_df[(phase_df['phase'] == p) & (phase_df['scenario'] == 'baseline')]['avg_prevalence'].values[0] 
                        if len(phase_df[(phase_df['phase'] == p) & (phase_df['scenario'] == 'baseline')]) > 0 else 0 
                        for p in phases_order]
        funding_prev = [phase_df[(phase_df['phase'] == p) & (phase_df['scenario'] == 'funding_cut')]['avg_prevalence'].values[0] 
                       if len(phase_df[(phase_df['phase'] == p) & (phase_df['scenario'] == 'funding_cut')]) > 0 else 0 
                       for p in phases_order]
        
        x = np.arange(len(phases_order))
        width = 0.35
        
        ax1.bar(x - width/2, baseline_prev, width, label='Baseline', color='#2E8B57', alpha=0.8)
        ax1.bar(x + width/2, funding_prev, width, label='Funding Cut', color='#DC143C', alpha=0.8)
        
        ax1.set_title('Average HIV Prevalence by Phase', fontweight='bold')
        ax1.set_ylabel('HIV Prevalence (%)')
        ax1.set_xticks(x)
        ax1.set_xticklabels([p.split('(')[0].strip() for p in phases_order], rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        plot_path = os.path.join(output_dir, 'epidemic_phases_analysis.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved phases analysis: {plot_path}")
    
    return phase_data


def generate_summary_statistics(df, key_year_results, output_dir):
    """Generate comprehensive summary statistics."""
    
    print("\n📋 GENERATING SUMMARY STATISTICS")
    print("=" * 32)
    
    # Overall study statistics
    total_simulations = len(df['replication'].unique()) * len(df['scenario'].unique())
    total_observations = len(df)
    study_period = f"{df['year'].min()}-{df['year'].max()}"
    
    # Final year comparison
    final_year = df['year'].max()
    final_data = df[df['year'] == final_year]
    baseline_final = final_data[final_data['scenario'] == 'baseline']['prevalence_pct'].mean()
    funding_cut_final = final_data[final_data['scenario'] == 'funding_cut']['prevalence_pct'].mean()
    
    summary_stats = {
        'study_overview': {
            'period': study_period,
            'total_simulations': total_simulations,
            'total_observations': total_observations,
            'population_size': int(df['total_population'].mean()),
            'scenarios': list(df['scenario'].unique()),
            'replications_per_scenario': df.groupby('scenario')['replication'].nunique().to_dict()
        },
        'final_year_results': {
            'year': int(final_year),
            'baseline_prevalence': float(baseline_final),
            'funding_cut_prevalence': float(funding_cut_final),
            'absolute_difference': float(funding_cut_final - baseline_final),
            'relative_difference': float((funding_cut_final - baseline_final) / baseline_final * 100)
        },
        'key_milestone_impacts': {str(r['year']): r for r in key_year_results}
    }
    
    # Save summary
    summary_path = os.path.join(output_dir, 'comprehensive_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary_stats, f, indent=2, default=str)
    
    print(f"✅ Saved summary statistics: {summary_path}")
    
    # Print key findings
    print("\n🎯 FINAL SUMMARY - KEY FINDINGS")
    print("=" * 35)
    print(f"📅 Study Period: {study_period}")
    print(f"🎲 Total Simulations: {total_simulations}")
    print(f"📊 Total Observations: {total_observations:,}")
    print(f"\\n🔴 CRITICAL IMPACT BY {int(final_year)}:")
    print(f"   Baseline Scenario: {baseline_final:.2f}% HIV prevalence")
    print(f"   Funding Cut Scenario: {funding_cut_final:.2f}% HIV prevalence")
    print(f"   Impact: +{funding_cut_final - baseline_final:.2f} percentage points (+{(funding_cut_final - baseline_final) / baseline_final * 100:.1f}%)")
    
    return summary_stats


def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python final_analysis.py <results_csv> <output_dir>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Run comprehensive analysis
    df = load_data(results_file)
    summary_stats = create_comprehensive_trajectory_plot(df, output_dir)
    key_year_results = create_key_year_analysis(df, output_dir)
    phase_data = create_epidemic_phases_analysis(df, output_dir)
    final_summary = generate_summary_statistics(df, key_year_results, output_dir)
    
    print("\\n🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
    print("=" * 40)
    print(f"📁 All results saved to: {output_dir}")
    print("\\n📊 Generated Visualizations:")
    print("   • comprehensive_1985_2100_analysis.png")
    print("   • key_year_impacts.png") 
    print("   • epidemic_phases_analysis.png")
    print("\\n📋 Summary Files:")
    print("   • comprehensive_summary.json")


if __name__ == "__main__":
    main()
