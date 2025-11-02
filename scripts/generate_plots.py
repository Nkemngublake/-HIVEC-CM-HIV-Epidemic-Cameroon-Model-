#!/usr/bin/env python3
"""
HIVEC-CM Visualization Tool
Generate comprehensive plots and visualizations:
  - Age-sex stratified charts
  - Regional heatmaps
  - Scenario comparison plots
  - Validation charts
  - Publication-ready figures
  
Consolidates: plot_results.py, plot_prevalence_validation.py,
visualize_saint_seya.py, generate_publication_plots.py, generate_validation_plots.py
"""

import argparse
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def plot_age_sex_trends(results_dir, output_dir):
    """Plot HIV prevalence trends by age and sex."""
    print("\n📊 Generating age-sex trend plots...")
    
    csv_file = os.path.join(results_dir, 'detailed_age_sex_results.csv')
    if not os.path.exists(csv_file):
        print(f"  ⚠️  CSV not found: {csv_file}")
        return
    
    df = pd.read_csv(csv_file)
    age_sex = df[df['type'] == 'prevalence'].copy()
    
    if len(age_sex) == 0:
        print("  ⚠️  No age-sex data found")
        return
    
    # Create comprehensive figure
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('HIV Prevalence by Age and Sex', fontsize=16, fontweight='bold')
    
    # Plot 1: Overall trends by sex
    ax1 = axes[0, 0]
    for sex in ['M', 'F']:
        sex_data = age_sex[age_sex['sex'] == sex]
        by_year = sex_data.groupby('year')['prevalence_pct'].mean()
        label = 'Male' if sex == 'M' else 'Female'
        ax1.plot(by_year.index, by_year.values, label=label, linewidth=2)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('HIV Prevalence (%)')
    ax1.set_title('Overall Prevalence by Sex')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Youth trends
    ax2 = axes[0, 1]
    youth_ages = ['15-19', '20-24']
    for sex in ['M', 'F']:
        youth_data = age_sex[(age_sex['sex'] == sex) &
                             (age_sex['age_group'].isin(youth_ages))]
        by_year = youth_data.groupby('year')['prevalence_pct'].mean()
        label = f"{'Male' if sex == 'M' else 'Female'} 15-24"
        ax2.plot(by_year.index, by_year.values, label=label, linewidth=2)
    ax2.set_xlabel('Year')
    ax2.set_ylabel('HIV Prevalence (%)')
    ax2.set_title('Youth (15-24) Prevalence')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Female heatmap
    ax3 = axes[1, 0]
    female_data = age_sex[age_sex['sex'] == 'F']
    pivot_f = female_data.pivot_table(
        values='prevalence_pct',
        index='age_group',
        columns='year',
        aggfunc='mean'
    )
    years_sample = [y for y in pivot_f.columns if int(y) % 10 == 5
                    or int(y) == min(pivot_f.columns)
                    or int(y) == max(pivot_f.columns)]
    pivot_sample = pivot_f[years_sample]
    sns.heatmap(pivot_sample, annot=False, cmap='YlOrRd', ax=ax3,
                cbar_kws={'label': 'Prevalence %'})
    ax3.set_title('Female Prevalence Heatmap')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('Age Group')
    
    # Plot 4: Final year comparison
    ax4 = axes[1, 1]
    final_year = age_sex['year'].max()
    final_data = age_sex[age_sex['year'] == final_year]
    pivot_final = final_data.pivot_table(
        values='prevalence_pct',
        index='age_group',
        columns='sex'
    )
    pivot_final.plot(kind='bar', ax=ax4, color=['steelblue', 'salmon'])
    ax4.set_xlabel('Age Group')
    ax4.set_ylabel('HIV Prevalence (%)')
    ax4.set_title(f'Final Year ({final_year}) by Age and Sex')
    ax4.legend(['Male', 'Female'])
    ax4.grid(True, alpha=0.3, axis='y')
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, 'age_sex_trends.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file}")


def plot_regional_heatmap(results_dir, output_dir):
    """Plot regional prevalence heatmap."""
    print("\n📊 Generating regional heatmap...")
    
    csv_file = os.path.join(results_dir, 'detailed_age_sex_results.csv')
    if not os.path.exists(csv_file):
        print(f"  ⚠️  CSV not found")
        return
    
    df = pd.read_csv(csv_file)
    regional = df[df['type'] == 'regional_prevalence'].copy()
    
    if len(regional) == 0:
        print("  ⚠️  No regional data found")
        return
    
    # Overall regional prevalence by year
    regional_avg = regional.groupby(['year', 'region'])['prevalence_pct'].mean().reset_index()
    pivot = regional_avg.pivot(index='region', columns='year', values='prevalence_pct')
    
    # Sample years for readability
    years_sample = [y for y in pivot.columns if int(y) % 10 == 5
                    or int(y) == min(pivot.columns)
                    or int(y) == max(pivot.columns)]
    pivot_sample = pivot[years_sample]
    
    plt.figure(figsize=(14, 8))
    sns.heatmap(pivot_sample, annot=True, fmt='.1f', cmap='YlOrRd',
                cbar_kws={'label': 'Prevalence %'})
    plt.title('Regional HIV Prevalence Over Time', fontsize=14, fontweight='bold')
    plt.xlabel('Year')
    plt.ylabel('Region')
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, 'regional_heatmap.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file}")


def plot_treatment_cascade(results_dir, output_dir):
    """Plot 95-95-95 treatment cascade."""
    print("\n📊 Generating treatment cascade plot...")
    
    json_file = os.path.join(results_dir, 'detailed_results.json')
    if not os.path.exists(json_file):
        print(f"  ⚠️  JSON not found")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Extract cascade data by year
    years = []
    diagnosed = []
    on_art = []
    suppressed = []
    
    for year_str in sorted(data.keys()):
        cascade = data[year_str].get('treatment_cascade_95_95_95', {})
        if cascade:
            years.append(int(year_str))
            diagnosed.append(cascade.get('diagnosed_coverage', 0) * 100)
            on_art.append(cascade.get('on_art_coverage', 0) * 100)
            suppressed.append(cascade.get('virally_suppressed_coverage', 0) * 100)
    
    if len(years) == 0:
        print("  ⚠️  No cascade data found")
        return
    
    plt.figure(figsize=(12, 7))
    plt.plot(years, diagnosed, label='Diagnosed', linewidth=2, marker='o')
    plt.plot(years, on_art, label='On ART', linewidth=2, marker='s')
    plt.plot(years, suppressed, label='Virally Suppressed', linewidth=2, marker='^')
    
    plt.axhline(y=95, color='red', linestyle='--', alpha=0.5, label='95% Target')
    
    plt.xlabel('Year')
    plt.ylabel('Coverage (%)')
    plt.title('95-95-95 Treatment Cascade Progress', fontsize=14, fontweight='bold')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, 'treatment_cascade.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file}")


def compare_scenarios_plot(base_dir, output_dir):
    """Generate scenario comparison plots."""
    print("\n📊 Generating scenario comparison plots...")
    
    # Find scenarios
    scenario_dirs = [d for d in os.listdir(base_dir)
                     if os.path.isdir(os.path.join(base_dir, d))
                     and not d.startswith('_')]
    
    if len(scenario_dirs) == 0:
        print("  ⚠️  No scenarios found")
        return
    
    # Load data from each scenario
    scenario_data = {}
    for scenario_id in scenario_dirs:
        json_file = os.path.join(base_dir, scenario_id, 'detailed_results.json')
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                scenario_data[scenario_id] = json.load(f)
    
    if len(scenario_data) == 0:
        print("  ⚠️  No scenario data loaded")
        return
    
    # Plot prevalence trends
    plt.figure(figsize=(14, 8))
    for scenario_id, data in scenario_data.items():
        years = []
        prevalence = []
        for year_str in sorted(data.keys()):
            years.append(int(year_str))
            agg = data[year_str].get('aggregate', {})
            prevalence.append(agg.get('prevalence', 0) * 100)
        
        plt.plot(years, prevalence, label=scenario_id, linewidth=2, marker='o',
                 markersize=4, alpha=0.8)
    
    plt.xlabel('Year')
    plt.ylabel('HIV Prevalence (%)')
    plt.title('Scenario Comparison: HIV Prevalence Trajectories',
              fontsize=14, fontweight='bold')
    plt.legend(loc='best', ncol=2)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, 'scenario_comparison_prevalence.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Saved: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HIVEC-CM Visualization Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Age-sex trends
  %(prog)s --mode age-sex --dir results/S0_baseline --output plots
  
  # Regional heatmap
  %(prog)s --mode regional --dir results/S0_baseline --output plots
  
  # Treatment cascade
  %(prog)s --mode cascade --dir results/S0_baseline --output plots
  
  # Compare scenarios
  %(prog)s --mode compare --dir results/scenarios_20251101 --output plots
  
  # All plots
  %(prog)s --mode all --dir results/S0_baseline --output plots
        """
    )
    
    parser.add_argument('--mode', type=str, required=True,
                       choices=['age-sex', 'regional', 'cascade', 'compare', 'all'],
                       help='Visualization mode')
    
    parser.add_argument('--dir', type=str, required=True,
                       help='Results directory')
    
    parser.add_argument('--output', type=str, default='plots',
                       help='Output directory for plots (default: plots/)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"❌ Directory not found: {args.dir}")
        return 1
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    print("=" * 80)
    print("HIVEC-CM VISUALIZATION TOOL")
    print("=" * 80)
    
    # Generate plots based on mode
    if args.mode in ['age-sex', 'all']:
        plot_age_sex_trends(args.dir, args.output)
    
    if args.mode in ['regional', 'all']:
        plot_regional_heatmap(args.dir, args.output)
    
    if args.mode in ['cascade', 'all']:
        plot_treatment_cascade(args.dir, args.output)
    
    if args.mode == 'compare':
        compare_scenarios_plot(args.dir, args.output)
    
    print(f"\n✓ Visualization complete!")
    print(f"📁 Output: {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
