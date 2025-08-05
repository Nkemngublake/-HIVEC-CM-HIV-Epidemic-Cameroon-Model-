#!/usr/bin/env python3
"""
CORRECTED Comprehensive HIV Scenario Analysis (1990-2050)
========================================================
Fixed date handling - no more year 4000 issues!
"""

import sys
sys.path.insert(0, '.')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from src.models.hiv_model import ModelParameters, EnhancedHIVModel

def run_corrected_comprehensive_analysis():
    """Run the full 1990-2050 analysis with corrected dates."""
    print("🔧 CORRECTED COMPREHENSIVE HIV ANALYSIS: Cameroon 1990-2050")
    print("=" * 70)
    print("Fixed date handling - proper 1990-2050 range!")
    
    unique_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"📋 Analysis ID: {unique_id}")
    print()
    
    # Baseline scenario (1990-2050)
    print("1️⃣ Running BASELINE scenario (1990-2050)...")
    params_baseline = ModelParameters(
        funding_cut_scenario=False,
        initial_population=50000  # Medium size for balance of speed/accuracy
    )
    
    model_baseline = EnhancedHIVModel(params_baseline)
    model_baseline.current_year = 1990  # Set start year
    results_baseline = model_baseline.run_simulation(years=60, dt=0.5)
    
    # Verify correct years (don't add anything!)
    print(f"   ✅ Baseline years: {results_baseline['year'].min():.0f}-{results_baseline['year'].max():.0f}")
    
    # Funding cut scenario (1990-2050)
    print("2️⃣ Running FUNDING CUT scenario (1990-2050)...")
    params_cut = ModelParameters(
        funding_cut_scenario=True,
        funding_cut_year=2025,
        initial_population=50000
    )
    
    model_cut = EnhancedHIVModel(params_cut)
    model_cut.current_year = 1990  # Set start year
    results_cut = model_cut.run_simulation(years=60, dt=0.5)
    
    # Verify correct years (don't add anything!)
    print(f"   ✅ Funding cut years: {results_cut['year'].min():.0f}-{results_cut['year'].max():.0f}")
    print()
    
    # Create comprehensive visualization
    create_corrected_comprehensive_plots(results_baseline, results_cut, unique_id)
    
    # Create summary report
    create_corrected_summary_report(results_baseline, results_cut, unique_id)
    
    # Save data
    save_corrected_data(results_baseline, results_cut, unique_id)

def create_corrected_comprehensive_plots(baseline, funding_cut, unique_id):
    """Create comprehensive plots with correct dates."""
    print("📊 Creating corrected comprehensive visualization...")
    
    # Create main comparison figure
    fig, axes = plt.subplots(3, 3, figsize=(20, 16))
    fig.suptitle('HIV/AIDS Epidemic Scenarios: Cameroon 1990-2050\\n' + 
                 'Baseline vs 50% Funding Cuts from 2025 (CORRECTED DATES)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
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
    ax.set_xlabel('Year')
    ax.set_ylabel('HIV Prevalence (%)')
    ax.set_title('A. HIV Prevalence', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 2: People Living with HIV
    ax = axes[0, 1]
    ax.plot(baseline['year'], baseline['hiv_infections']/1000, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['hiv_infections']/1000, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('People Living with HIV (thousands)')
    ax.set_title('B. People Living with HIV', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 3: Annual New Infections
    ax = axes[0, 2]
    ax.plot(baseline['year'], baseline['new_infections'], 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['new_infections'], 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual New Infections')
    ax.set_title('C. HIV Incidence', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 4: ART Coverage
    ax = axes[1, 0]
    ax.plot(baseline['year'], baseline['art_coverage']*100, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['art_coverage']*100, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('ART Coverage (%)')
    ax.set_title('D. Antiretroviral Treatment Coverage', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 5: HIV-Related Deaths
    ax = axes[1, 1]
    ax.plot(baseline['year'], baseline['deaths_hiv'], 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], funding_cut['deaths_hiv'], 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual HIV Deaths')
    ax.set_title('E. HIV-Related Mortality', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 6: People on ART
    people_on_art_baseline = baseline['art_coverage'] * baseline['hiv_infections'] / 1000
    people_on_art_funding = funding_cut['art_coverage'] * funding_cut['hiv_infections'] / 1000
    
    ax = axes[1, 2]
    ax.plot(baseline['year'], people_on_art_baseline, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], people_on_art_funding, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('People on ART (thousands)')
    ax.set_title('F. People Receiving Treatment', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 7: Incidence Rate (per 100,000)
    incidence_rate_baseline = baseline['new_infections'] / baseline['total_population'] * 100000
    incidence_rate_funding = funding_cut['new_infections'] / funding_cut['total_population'] * 100000
    
    ax = axes[2, 0]
    ax.plot(baseline['year'], incidence_rate_baseline, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], incidence_rate_funding, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Incidence Rate (per 100,000)')
    ax.set_title('G. HIV Incidence Rate', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 8: Mortality Rate (per 100,000)
    mortality_rate_baseline = baseline['deaths_hiv'] / baseline['total_population'] * 100000
    mortality_rate_funding = funding_cut['deaths_hiv'] / funding_cut['total_population'] * 100000
    
    ax = axes[2, 1]
    ax.plot(baseline['year'], mortality_rate_baseline, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], mortality_rate_funding, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Mortality Rate (per 100,000)')
    ax.set_title('H. HIV Mortality Rate', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    # Panel 9: Treatment Gap
    treatment_gap_baseline = (baseline['hiv_infections'] - 
                             baseline['art_coverage'] * baseline['hiv_infections']) / 1000
    treatment_gap_funding = (funding_cut['hiv_infections'] - 
                            funding_cut['art_coverage'] * funding_cut['hiv_infections']) / 1000
    
    ax = axes[2, 2]
    ax.plot(baseline['year'], treatment_gap_baseline, 
            color=baseline_color, linewidth=3, label='Baseline')
    ax.plot(funding_cut['year'], treatment_gap_funding, 
            color=funding_color, linewidth=3, linestyle='--', label='Funding Cuts')
    ax.axvline(x=2025, color=cut_line_color, linestyle=':', alpha=0.7, linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Treatment Gap (thousands)')
    ax.set_title('I. Unmet Treatment Need', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1990, 2050)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Save figure
    output_path = f'Simulation_results_scenarios/CORRECTED_Comprehensive_{unique_id}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"   📊 Comprehensive chart saved: {output_path}")

def create_corrected_summary_report(baseline, funding_cut, unique_id):
    """Create summary of key findings with correct dates."""
    
    # Get 2050 data
    baseline_2050 = baseline.iloc[-1]
    funding_2050 = funding_cut.iloc[-1]
    
    print()
    print("📈 KEY FINDINGS (2050) - CORRECTED:")
    print(f"   Date verification: {baseline_2050['year']:.0f}")
    
    prev_change = ((funding_2050['hiv_prevalence'] - baseline_2050['hiv_prevalence']) / 
                  baseline_2050['hiv_prevalence']) * 100
    art_change = ((funding_2050['art_coverage'] - baseline_2050['art_coverage']) / 
                 baseline_2050['art_coverage']) * 100
    
    print(f"   • HIV Prevalence: {baseline_2050['hiv_prevalence']*100:.2f}% → {funding_2050['hiv_prevalence']*100:.2f}% ({prev_change:+.1f}%)")
    print(f"   • People Living with HIV: {baseline_2050['hiv_infections']:,.0f} → {funding_2050['hiv_infections']:,.0f}")
    print(f"   • ART Coverage: {baseline_2050['art_coverage']*100:.1f}% → {funding_2050['art_coverage']*100:.1f}% ({art_change:+.1f}%)")
    print(f"   • New Infections: {baseline_2050['new_infections']:,.0f} → {funding_2050['new_infections']:,.0f}")
    print(f"   • HIV Deaths: {baseline_2050['deaths_hiv']:,.0f} → {funding_2050['deaths_hiv']:,.0f}")
    
    # Calculate cumulative impact (2025-2050)
    post_2025_baseline = baseline[baseline['year'] >= 2025]
    post_2025_funding = funding_cut[funding_cut['year'] >= 2025]
    
    additional_infections = sum(post_2025_funding['new_infections'] - post_2025_baseline['new_infections'])
    additional_deaths = sum(post_2025_funding['deaths_hiv'] - post_2025_baseline['deaths_hiv'])
    
    print()
    print("📊 CUMULATIVE IMPACT (2025-2050):")
    print(f"   • Additional HIV infections: {additional_infections:,.0f}")
    print(f"   • Additional HIV deaths: {additional_deaths:,.0f}")

def save_corrected_data(baseline, funding_cut, unique_id):
    """Save corrected data to CSV files."""
    
    # Save complete datasets
    baseline_path = f'Simulation_results_scenarios/CORRECTED_Baseline_{unique_id}.csv'
    baseline.to_csv(baseline_path, index=False)
    
    funding_path = f'Simulation_results_scenarios/CORRECTED_FundingCut_{unique_id}.csv'
    funding_cut.to_csv(funding_path, index=False)
    
    # Create summary comparison
    key_years = [1990, 2000, 2010, 2020, 2025, 2030, 2040, 2050]
    comparison_data = []
    
    for year in key_years:
        baseline_row = baseline[baseline['year'].round() == year]
        funding_row = funding_cut[funding_cut['year'].round() == year]
        
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
    comparison_path = f'Simulation_results_scenarios/CORRECTED_Comparison_{unique_id}.csv'
    comparison_df.to_csv(comparison_path, index=False)
    
    print()
    print("💾 DATA SAVED:")
    print(f"   • Baseline: {baseline_path}")
    print(f"   • Funding cut: {funding_path}")
    print(f"   • Comparison: {comparison_path}")

def main():
    """Main execution with error handling."""
    try:
        run_corrected_comprehensive_analysis()
        
        print()
        print("✅ CORRECTED COMPREHENSIVE ANALYSIS COMPLETE!")
        print("=" * 60)
        print("🔧 Date issue resolved - proper 1990-2050 range")
        print("📊 Publication-ready charts generated")
        print("💾 Complete datasets saved")
        print("🏆 Ready for policy analysis!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
