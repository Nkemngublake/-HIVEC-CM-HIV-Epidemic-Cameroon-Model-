#!/usr/bin/env python3
"""
HIVEC-CM Results Analysis Tool
Comprehensive analysis of simulation results:
  - Detection gap analysis
  - Enhanced results processing
  - Scenario comparison
  - CSV regeneration and extraction
  
Consolidates: analyze_detection_gaps.py, analyze_enhanced_results.py,
analyze_saint_seya_results.py, compare_scenarios.py,
regenerate_detailed_csv.py, extract_detailed_results.py
"""

import argparse
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def analyze_detection_gaps(results_dir):
    """Analyze testing and detection gaps."""
    print("\n" + "=" * 80)
    print("DETECTION GAP ANALYSIS")
    print("=" * 80)
    
    # Load results
    json_file = os.path.join(results_dir, 'detailed_results.json')
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print("\n📊 Testing and Detection Coverage")
    print("-" * 80)
    
    # Analyze by year
    for year in sorted(data.keys())[-5:]:  # Last 5 years
        year_data = data[year]
        
        # Treatment cascade
        cascade = year_data.get('treatment_cascade_95_95_95', {})
        if cascade:
            print(f"\nYear {year}:")
            diagnosed = cascade.get('diagnosed_coverage', 0)
            on_art = cascade.get('on_art_coverage', 0)
            suppressed = cascade.get('virally_suppressed_coverage', 0)
            
            print(f"  Diagnosed:    {diagnosed:.1%}")
            print(f"  On ART:       {on_art:.1%}")
            print(f"  Suppressed:   {suppressed:.1%}")
            
            # Calculate gaps
            undiagnosed_gap = 1.0 - diagnosed if diagnosed < 1.0 else 0
            treatment_gap = diagnosed - on_art if diagnosed > on_art else 0
            suppression_gap = on_art - suppressed if on_art > suppressed else 0
            
            print(f"  Gaps:")
            print(f"    Undiagnosed:  {undiagnosed_gap:.1%}")
            print(f"    Not on ART:   {treatment_gap:.1%}")
            print(f"    Not suppressed: {suppression_gap:.1%}")


def analyze_comprehensive_results(results_dir):
    """Comprehensive analysis of all data dimensions."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE RESULTS ANALYSIS")
    print("=" * 80)
    
    # Load JSON
    json_file = os.path.join(results_dir, 'detailed_results.json')
    with open(json_file, 'r') as f:
        detailed_data = json.load(f)
    
    # Check data dimensions
    sample_year = list(detailed_data.keys())[0]
    data_types = list(detailed_data[sample_year].keys())
    
    print(f"\n📁 DATA DIMENSIONS CAPTURED ({len(data_types)} types):")
    print("-" * 80)
    for i, dtype in enumerate(data_types, 1):
        print(f"  {i:2d}. {dtype}")
    
    # Load CSV
    csv_file = os.path.join(results_dir, 'detailed_age_sex_results.csv')
    if os.path.exists(csv_file):
        df = pd.DataFrame(pd.read_csv(csv_file))
        
        print(f"\n📈 FLATTENED CSV STATISTICS:")
        print("-" * 80)
        print(f"  Total rows: {len(df):,}")
        print(f"  Years: {df['year'].min()} - {df['year'].max()}")
        print(f"  Data types: {df['type'].unique().tolist()}")
        
        # Age-sex prevalence
        age_sex = df[df['type'] == 'prevalence']
        if len(age_sex) > 0:
            print(f"\n  Age-Sex Prevalence:")
            print(f"    Rows: {len(age_sex):,}")
            print(f"    Age groups: {sorted(age_sex['age_group'].unique().tolist())}")
            print(f"    Sexes: {age_sex['sex'].unique().tolist()}")
        
        # Regional prevalence
        regional = df[df['type'] == 'regional_prevalence']
        if len(regional) > 0:
            print(f"\n  Regional Prevalence:")
            print(f"    Rows: {len(regional):,}")
            regions = sorted(regional['region'].dropna().unique().tolist())
            print(f"    Regions ({len(regions)}): {', '.join(regions)}")
        
        # Final year prevalence by age/sex
        final_year = df['year'].max()
        final_age_sex = age_sex[age_sex['year'] == final_year]
        
        if len(final_age_sex) > 0:
            print(f"\n  Final Year ({final_year}) Prevalence:")
            print("-" * 80)
            pivot = final_age_sex.pivot_table(
                values='prevalence_pct',
                index='age_group',
                columns='sex',
                aggfunc='mean'
            )
            print(pivot.to_string())
    
    # Treatment cascade final year
    final_year_key = list(detailed_data.keys())[-1]
    cascade = detailed_data[final_year_key].get('treatment_cascade_95_95_95', {})
    if cascade:
        print(f"\n  95-95-95 Cascade ({final_year_key}):")
        print("-" * 80)
        for stage, value in cascade.items():
            if isinstance(value, (int, float)):
                if 'coverage' in stage or 'rate' in stage:
                    print(f"    {stage}: {value:.1%}")
                else:
                    print(f"    {stage}: {value:,.0f}")


def compare_scenarios(base_dir):
    """Compare multiple scenarios."""
    print("\n" + "=" * 80)
    print("SCENARIO COMPARISON")
    print("=" * 80)
    
    # Find all scenario directories
    scenario_dirs = [d for d in os.listdir(base_dir)
                     if os.path.isdir(os.path.join(base_dir, d))
                     and not d.startswith('_')]
    
    if len(scenario_dirs) == 0:
        print("❌ No scenario directories found")
        return
    
    print(f"\nFound {len(scenario_dirs)} scenarios:")
    for s in sorted(scenario_dirs):
        print(f"  • {s}")
    
    comparison_data = []
    
    for scenario_id in sorted(scenario_dirs):
        scenario_path = os.path.join(base_dir, scenario_id)
        
        # Load results
        json_file = os.path.join(scenario_path, 'detailed_results.json')
        if not os.path.exists(json_file):
            continue
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Get final year data
        final_year = sorted(data.keys())[-1]
        final_data = data[final_year]
        
        agg = final_data.get('aggregate', {})
        cascade = final_data.get('treatment_cascade_95_95_95', {})
        
        comparison_data.append({
            'scenario': scenario_id,
            'final_year': final_year,
            'population': agg.get('population', 0),
            'infected': agg.get('infected', 0),
            'prevalence': agg.get('prevalence', 0),
            'on_art': agg.get('on_art', 0),
            'diagnosed_coverage': cascade.get('diagnosed_coverage', 0),
            'art_coverage': cascade.get('on_art_coverage', 0),
            'suppression': cascade.get('virally_suppressed_coverage', 0)
        })
    
    # Create comparison DataFrame
    df_compare = pd.DataFrame(comparison_data)
    
    print(f"\n📊 FINAL YEAR COMPARISON ({final_year}):")
    print("=" * 80)
    print(df_compare.to_string(index=False))
    
    # Save comparison
    output_file = os.path.join(base_dir, 'scenario_comparison.csv')
    df_compare.to_csv(output_file, index=False)
    print(f"\n✓ Comparison saved: {output_file}")


def regenerate_csv(results_dir):
    """Regenerate flattened CSV from JSON."""
    print("\n" + "=" * 80)
    print("REGENERATING CSV FROM JSON")
    print("=" * 80)
    
    json_file = os.path.join(results_dir, 'detailed_results.json')
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"\n📊 Processing {len(data)} years of data...")
    
    rows = []
    for year_str, year_data in data.items():
        year = int(year_str)
        
        # Age-sex prevalence
        age_sex_prev = year_data.get('age_sex_prevalence', {})
        for age_group, sex_data in age_sex_prev.items():
            for sex, values in sex_data.items():
                if isinstance(values, dict):
                    rows.append({
                        'year': year,
                        'type': 'prevalence',
                        'age_group': age_group,
                        'sex': sex,
                        'region': None,
                        'population': values.get('population', 0),
                        'infected': values.get('infected', 0),
                        'prevalence_pct': values.get('prevalence', 0) * 100
                    })
        
        # Regional prevalence
        regional_prev = year_data.get('regional_prevalence', {})
        for region, age_sex_data in regional_prev.items():
            if isinstance(age_sex_data, dict):
                for age_group, sex_data in age_sex_data.items():
                    if isinstance(sex_data, dict):
                        for sex, values in sex_data.items():
                            if isinstance(values, dict):
                                rows.append({
                                    'year': year,
                                    'type': 'regional_prevalence',
                                    'age_group': age_group,
                                    'sex': sex,
                                    'region': region,
                                    'population': values.get('population', 0),
                                    'infected': values.get('infected', 0),
                                    'prevalence_pct': values.get('prevalence', 0) * 100
                                })
    
    df = pd.DataFrame(rows)
    output_file = os.path.join(results_dir, 'detailed_age_sex_results_regenerated.csv')
    df.to_csv(output_file, index=False)
    
    print(f"✓ Regenerated CSV: {output_file}")
    print(f"  Total rows: {len(df):,}")
    print(f"  Years: {df['year'].min()} - {df['year'].max()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HIVEC-CM Results Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Comprehensive analysis
  %(prog)s --mode comprehensive --dir results/Saint_Seya_Simulation_Detailed/S0_baseline
  
  # Detection gaps
  %(prog)s --mode gaps --dir results/scenarios_20251101/S2a_testing
  
  # Compare scenarios
  %(prog)s --mode compare --dir results/scenarios_20251101
  
  # Regenerate CSV
  %(prog)s --mode regenerate --dir results/simulation_20251101_153959
        """
    )
    
    parser.add_argument('--mode', type=str, required=True,
                       choices=['comprehensive', 'gaps', 'compare', 'regenerate'],
                       help='Analysis mode')
    
    parser.add_argument('--dir', type=str, required=True,
                       help='Results directory to analyze')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"❌ Directory not found: {args.dir}")
        return 1
    
    # Execute based on mode
    if args.mode == 'comprehensive':
        analyze_comprehensive_results(args.dir)
    elif args.mode == 'gaps':
        analyze_detection_gaps(args.dir)
    elif args.mode == 'compare':
        compare_scenarios(args.dir)
    elif args.mode == 'regenerate':
        regenerate_csv(args.dir)
    
    print(f"\n✓ Analysis complete!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
