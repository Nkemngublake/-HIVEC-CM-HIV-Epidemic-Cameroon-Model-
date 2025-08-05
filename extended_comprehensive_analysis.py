#!/usr/bin/env python3
"""
EXTENDED Comprehensive HIV Scenario Analysis (1990-2100)
========================================================
Long-term projections with enhanced parameters to 2100!
"""

import sys
sys.path.insert(0, '.')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from src.models.hiv_model import ModelParameters, EnhancedHIVModel

def run_extended_comprehensive_analysis():
    """Run the full 1990-2100 analysis with enhanced parameters."""
    print("🚀 EXTENDED COMPREHENSIVE HIV ANALYSIS: Cameroon 1990-2100")
    print("=" * 70)
    print("Long-term projections with enhanced parameters!")
    
    unique_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"📋 Analysis ID: {unique_id}")
    print()
    
    # Baseline scenario (1990-2100)
    print("1️⃣ Running BASELINE scenario (1990-2100)...")
    params_baseline = ModelParameters(
        funding_cut_scenario=False,
        initial_population=50000  # Medium size for balance of speed/accuracy
    )
    
    model_baseline = EnhancedHIVModel(params_baseline)
    model_baseline.current_year = 1990  # Set start year
    results_baseline = model_baseline.run_simulation(years=110, dt=0.5)  # Extended to 110 years
    
    # Verify correct years
    print(f"   ✅ Baseline years: {results_baseline['year'].min():.0f}-{results_baseline['year'].max():.0f}")
    
    # Funding cut scenario (1990-2100)
    print("2️⃣ Running FUNDING CUT scenario (1990-2100)...")
    params_cut = ModelParameters(
        funding_cut_scenario=True,
        funding_cut_year=2025,
        initial_population=50000
    )
    
    model_cut = EnhancedHIVModel(params_cut)
    model_cut.current_year = 1990  # Set start year
    results_cut = model_cut.run_simulation(years=110, dt=0.5)  # Extended to 110 years
    
    # Verify correct years
    print(f"   ✅ Funding cut years: {results_cut['year'].min():.0f}-{results_cut['year'].max():.0f}")
    print()
    
    # Create comprehensive visualization
    create_extended_comprehensive_plots(results_baseline, results_cut, unique_id)
    
    # Create summary report
    create_extended_summary_report(results_baseline, results_cut, unique_id)
    
    # Save data
    save_extended_data(results_baseline, results_cut, unique_id)

def create_extended_comprehensive_plots(baseline, funding_cut, unique_id):
    """Create comprehensive plots with extended timeframe to 2100."""
    print("📊 Creating extended comprehensive visualization (1990-2100)...")
    
    # Create main comparison figure
    fig, axes = plt.subplots(3, 3, figsize=(24, 18))
    fig.suptitle('HIV/AIDS Epidemic Scenarios: Cameroon 1990-2100\\n' + 
                 'Baseline vs 50% Funding Cuts from 2025 (LONG-TERM PROJECTIONS)', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # Colors
    baseline_color = '#1f77b4'  # Blue
    funding_color = '#d62728'   # Red
    cut_line_color = '#ff7f0e'  # Orange
    
    # Panel 1: HIV Prevalence
    ax = axes[0, 0]
    ax.plot(baseline['year'], baseline['hiv_prevalence']*100, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['hiv_prevalence']*100, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2002, color='green', linestyle=':', alpha=0.7, linewidth=2, label='ART Start')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2, label='Funding Cuts')
    ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1, label='Mid-Century')
    ax.set_xlabel('Year')
    ax.set_ylabel('HIV Prevalence (%)')
    ax.set_title('A. HIV Prevalence (Long-term)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2100)
    
    # Panel 2: People Living with HIV
    ax = axes[0, 1]
    ax.plot(baseline['year'], baseline['hiv_infections']/1000, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['hiv_infections']/1000, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1)
    ax.set_xlabel('Year')
    ax.set_ylabel('People Living with HIV (thousands)')
    ax.set_title('B. People Living with HIV', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2100)
    
    # Panel 3: Annual New Infections
    ax = axes[0, 2]
    ax.plot(baseline['year'], baseline['new_infections'], 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['new_infections'], 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual New Infections')
    ax.set_title('C. HIV Incidence', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2100)
    
    # Panel 4: ART Coverage
    ax = axes[1, 0]
    ax.plot(baseline['year'], baseline['art_coverage']*100, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['art_coverage']*100, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1)
    ax.set_xlabel('Year')
    ax.set_ylabel('ART Coverage (%)')
    ax.set_title('D. Antiretroviral Treatment Coverage', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2100)
    
    # Panel 5: HIV-Related Deaths
    ax = axes[1, 1]
    ax.plot(baseline['year'], baseline['deaths_hiv'], 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['deaths_hiv'], 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual HIV Deaths')
    ax.set_title('E. HIV-Related Mortality', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2100)
    
    # Panel 6: People on ART
    people_on_art_baseline = baseline['art_coverage'] * baseline['hiv_infections'] / 1000
    people_on_art_funding = funding_cut['art_coverage'] * funding_cut['hiv_infections'] / 1000
    
    ax = axes[1, 2]
    ax.plot(baseline['year'], people_on_art_baseline, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], people_on_art_funding, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1)
    ax.set_xlabel('Year')
    ax.set_ylabel('People on ART (thousands)')
    ax.set_title('F. People Receiving Treatment', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2100)
    
    # Panel 7: Cumulative Impact Over Time
    # Calculate cumulative additional infections from funding cuts
    baseline_df = pd.DataFrame(baseline)
    funding_df = pd.DataFrame(funding_cut)
    
    # Post-2025 cumulative impact
    post_2025_baseline = baseline_df[baseline_df['year'] >= 2025].copy()
    post_2025_funding = funding_df[funding_df['year'] >= 2025].copy()
    
    if len(post_2025_baseline) > 0 and len(post_2025_funding) > 0:
        additional_infections = (post_2025_funding['new_infections'].values - 
                               post_2025_baseline['new_infections'].values)
        cumulative_additional = np.cumsum(additional_infections)
        
        ax = axes[2, 0]
        ax.plot(post_2025_funding['year'], cumulative_additional, 
                color='red', linewidth=3, label='Cumulative Additional Infections')
        ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1)
        ax.set_xlabel('Year')
        ax.set_ylabel('Cumulative Additional Infections')
        ax.set_title('G. Long-term Cumulative Impact', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(2025, 2100)
    
    # Panel 8: Long-term Prevalence Trajectory
    ax = axes[2, 1]
    
    # Focus on post-2020 trends
    recent_baseline = baseline_df[baseline_df['year'] >= 2020]
    recent_funding = funding_df[funding_df['year'] >= 2020]
    
    ax.plot(recent_baseline['year'], recent_baseline['hiv_prevalence']*100, 
            color=baseline_color, linewidth=3, label='Baseline Trajectory')
    ax.plot(recent_funding['year'], recent_funding['hiv_prevalence']*100, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cut Trajectory')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.axvline(x=2050, color='purple', linestyle=':', alpha=0.5, linewidth=1)
    ax.set_xlabel('Year')
    ax.set_ylabel('HIV Prevalence (%)')
    ax.set_title('H. Recent & Future Trends (2020-2100)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2020, 2100)
    
    # Panel 9: Century Summary - Key Milestones
    ax = axes[2, 2]
    
    # Calculate key statistics for different periods
    periods = ['1990-2000', '2000-2020', '2020-2050', '2050-2100']
    baseline_avg = []
    funding_avg = []
    
    for period in periods:
        start, end = map(int, period.split('-'))
        period_baseline = baseline_df[(baseline_df['year'] >= start) & (baseline_df['year'] < end)]
        period_funding = funding_df[(funding_df['year'] >= start) & (funding_df['year'] < end)]
        
        if len(period_baseline) > 0:
            baseline_avg.append(period_baseline['hiv_prevalence'].mean() * 100)
            funding_avg.append(period_funding['hiv_prevalence'].mean() * 100)
        else:
            baseline_avg.append(0)
            funding_avg.append(0)
    
    x = np.arange(len(periods))
    width = 0.35
    
    ax.bar(x - width/2, baseline_avg, width, label='Baseline', color=baseline_color, alpha=0.8)
    ax.bar(x + width/2, funding_avg, width, label='Funding Cuts', color=funding_color, alpha=0.8)
    
    ax.set_xlabel('Time Period')
    ax.set_ylabel('Average HIV Prevalence (%)')
    ax.set_title('I. Century Overview by Period', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(periods, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Save figure
    output_path = f'Simulation_results_scenarios/EXTENDED_Comprehensive_{unique_id}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"   📊 Extended comprehensive chart saved: {output_path}")

def create_extended_summary_report(baseline, funding_cut, unique_id):
    """Create summary of key findings for extended timeframe."""
    
    # Convert to DataFrames for easier analysis
    baseline_df = pd.DataFrame(baseline)
    funding_df = pd.DataFrame(funding_cut)
    
    # Get key year data
    data_2050 = baseline_df[baseline_df['year'].round() == 2050]
    data_2100 = baseline_df[baseline_df['year'].round() == 2100]
    
    funding_2050 = funding_df[funding_df['year'].round() == 2050]
    funding_2100 = funding_df[funding_df['year'].round() == 2100]
    
    print()
    print("📈 EXTENDED KEY FINDINGS (1990-2100):")
    print("=" * 50)
    
    if len(data_2050) > 0:
        b50 = data_2050.iloc[0]
        f50 = funding_2050.iloc[0]
        
        print(f"🎯 2050 PROJECTIONS:")
        print(f"   • Baseline prevalence: {b50['hiv_prevalence']*100:.2f}%")
        print(f"   • Funding cut prevalence: {f50['hiv_prevalence']*100:.2f}%")
        print(f"   • People living with HIV: {b50['hiv_infections']:,.0f} vs {f50['hiv_infections']:,.0f}")
        print(f"   • ART coverage: {b50['art_coverage']*100:.1f}% vs {f50['art_coverage']*100:.1f}%")
    
    if len(data_2100) > 0:
        b100 = data_2100.iloc[0]
        f100 = funding_2100.iloc[0]
        
        print(f"🔮 2100 PROJECTIONS:")
        print(f"   • Baseline prevalence: {b100['hiv_prevalence']*100:.2f}%")
        print(f"   • Funding cut prevalence: {f100['hiv_prevalence']*100:.2f}%") 
        print(f"   • People living with HIV: {b100['hiv_infections']:,.0f} vs {f100['hiv_infections']:,.0f}")
        print(f"   • ART coverage: {b100['art_coverage']*100:.1f}% vs {f100['art_coverage']*100:.1f}%")
    
    # Calculate century-long cumulative impact
    post_2025_baseline = baseline_df[baseline_df['year'] >= 2025]
    post_2025_funding = funding_df[funding_df['year'] >= 2025]
    
    total_additional_infections = sum(post_2025_funding['new_infections'] - post_2025_baseline['new_infections'])
    total_additional_deaths = sum(post_2025_funding['deaths_hiv'] - post_2025_baseline['deaths_hiv'])
    
    print()
    print("📊 CENTURY-LONG CUMULATIVE IMPACT (2025-2100):")
    print(f"   • Total additional HIV infections: {total_additional_infections:,.0f}")
    print(f"   • Total additional HIV deaths: {total_additional_deaths:,.0f}")
    print(f"   • Average annual excess infections: {total_additional_infections/75:.0f}")
    print(f"   • Average annual excess deaths: {total_additional_deaths/75:.0f}")

def save_extended_data(baseline, funding_cut, unique_id):
    """Save extended data to CSV files."""
    
    # Save complete datasets
    baseline_path = f'Simulation_results_scenarios/EXTENDED_Baseline_{unique_id}.csv'
    pd.DataFrame(baseline).to_csv(baseline_path, index=False)
    
    funding_path = f'Simulation_results_scenarios/EXTENDED_FundingCut_{unique_id}.csv'
    pd.DataFrame(funding_cut).to_csv(funding_path, index=False)
    
    # Create extended summary comparison
    key_years = [1990, 2000, 2010, 2020, 2025, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]
    comparison_data = []
    
    baseline_df = pd.DataFrame(baseline)
    funding_df = pd.DataFrame(funding_cut)
    
    for year in key_years:
        baseline_row = baseline_df[baseline_df['year'].round() == year]
        funding_row = funding_df[funding_df['year'].round() == year]
        
        if len(baseline_row) > 0 and len(funding_row) > 0:
            b_data = baseline_row.iloc[0]
            f_data = funding_row.iloc[0]
            
            comparison_data.append({
                'Year': year,
                'Scenario': 'Baseline',
                'HIV_Prevalence_Pct': b_data['hiv_prevalence']*100,
                'People_Living_HIV': b_data['hiv_infections'],
                'Annual_New_Infections': b_data['new_infections'],
                'Annual_HIV_Deaths': b_data['deaths_hiv'],
                'ART_Coverage_Pct': b_data['art_coverage']*100,
                'People_on_ART': b_data['art_coverage'] * b_data['hiv_infections']
            })
            
            comparison_data.append({
                'Year': year,
                'Scenario': 'Funding_Cuts',
                'HIV_Prevalence_Pct': f_data['hiv_prevalence']*100,
                'People_Living_HIV': f_data['hiv_infections'],
                'Annual_New_Infections': f_data['new_infections'],
                'Annual_HIV_Deaths': f_data['deaths_hiv'],
                'ART_Coverage_Pct': f_data['art_coverage']*100,
                'People_on_ART': f_data['art_coverage'] * f_data['hiv_infections']
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_path = f'Simulation_results_scenarios/EXTENDED_Comparison_{unique_id}.csv'
    comparison_df.to_csv(comparison_path, index=False)
    
    print()
    print("💾 EXTENDED DATA SAVED:")
    print(f"   • Baseline (1990-2100): {baseline_path}")
    print(f"   • Funding cut (1990-2100): {funding_path}")
    print(f"   • Extended comparison: {comparison_path}")

def main():
    """Main execution with error handling."""
    try:
        run_extended_comprehensive_analysis()
        
        print()
        print("✅ EXTENDED COMPREHENSIVE ANALYSIS COMPLETE!")
        print("=" * 60)
        print("🚀 Long-term projections to 2100 generated")
        print("📊 Century-scale epidemic modeling complete")
        print("💾 Extended datasets with 110-year timeframe saved")
        print("🔮 Ready for long-term policy planning!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
