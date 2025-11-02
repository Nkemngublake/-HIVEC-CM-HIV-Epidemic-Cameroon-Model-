#!/usr/bin/env python3
"""
HIVEC-CM Validation and Testing Tool
Comprehensive validation and testing:
  - Parameter validation
  - Model benchmarking
  - Milestone computation
  - Comprehensive validation tests
  
Consolidates: validate_scenario_parameters.py, comprehensive_validation.py,
compute_milestones.py, benchmark_transmission.py
"""

import argparse
import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel


def validate_parameters(config_file):
    """Validate model parameters."""
    print("=" * 80)
    print("PARAMETER VALIDATION")
    print("=" * 80)
    print(f"Config file: {config_file}\n")
    
    if not os.path.exists(config_file):
        print(f"❌ Config file not found: {config_file}")
        return False
    
    try:
        params = load_parameters(config_file)
        
        print("✓ Parameters loaded successfully\n")
        
        # Check key parameters
        checks = []
        
        # Population
        if hasattr(params, 'initial_population'):
            pop = params.initial_population
            checks.append(('Population', pop > 0 and pop <= 50000000,
                          f"{pop:,}"))
        
        # Years
        if hasattr(params, 'start_year') and hasattr(params, 'end_year'):
            start = params.start_year
            end = params.end_year
            checks.append(('Year range', start < end and start >= 1980 and end <= 2100,
                          f"{start} - {end}"))
        
        # Prevalence
        if hasattr(params, 'initial_prevalence'):
            prev = params.initial_prevalence
            checks.append(('Initial prevalence', prev >= 0 and prev <= 0.5,
                          f"{prev:.2%}"))
        
        # Transmission rate
        if hasattr(params, 'base_transmission_rate'):
            trans = params.base_transmission_rate
            checks.append(('Transmission rate', trans >= 0 and trans <= 1.0,
                          f"{trans:.4f}"))
        
        # Display validation results
        print("VALIDATION CHECKS:")
        print("-" * 80)
        for check_name, passed, value in checks:
            status = "✓" if passed else "❌"
            print(f"{status} {check_name:<25} {value}")
        
        all_passed = all(c[1] for c in checks)
        
        print("\n" + "=" * 80)
        if all_passed:
            print("✓ ALL VALIDATION CHECKS PASSED")
        else:
            print("❌ SOME VALIDATION CHECKS FAILED")
        print("=" * 80)
        
        return all_passed
    
    except Exception as e:
        print(f"❌ Error loading parameters: {e}")
        return False


def compute_milestones(results_dir):
    """Compute key HIV epidemic milestones."""
    print("=" * 80)
    print("MILESTONE COMPUTATION")
    print("=" * 80)
    print(f"Results: {results_dir}\n")
    
    # Load results
    json_file = os.path.join(results_dir, 'detailed_results.json')
    if not os.path.exists(json_file):
        print(f"❌ Results not found: {json_file}")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    milestones = []
    
    # 1. Peak prevalence
    max_prev = 0
    peak_year = None
    for year_str in sorted(data.keys()):
        agg = data[year_str].get('aggregate', {})
        prev = agg.get('prevalence', 0)
        if prev > max_prev:
            max_prev = prev
            peak_year = year_str
    
    milestones.append(('Peak Prevalence', peak_year, f"{max_prev:.2%}"))
    
    # 2. First year achieving 90-90-90
    first_90_90_90 = None
    for year_str in sorted(data.keys()):
        cascade = data[year_str].get('treatment_cascade_95_95_95', {})
        diag = cascade.get('diagnosed_coverage', 0)
        art = cascade.get('on_art_coverage', 0)
        supp = cascade.get('virally_suppressed_coverage', 0)
        
        if diag >= 0.90 and art >= 0.90 and supp >= 0.90:
            first_90_90_90 = year_str
            break
    
    if first_90_90_90:
        milestones.append(('First 90-90-90', first_90_90_90, 'Achieved'))
    else:
        milestones.append(('First 90-90-90', 'Not achieved', '-'))
    
    # 3. First year achieving 95-95-95
    first_95_95_95 = None
    for year_str in sorted(data.keys()):
        cascade = data[year_str].get('treatment_cascade_95_95_95', {})
        diag = cascade.get('diagnosed_coverage', 0)
        art = cascade.get('on_art_coverage', 0)
        supp = cascade.get('virally_suppressed_coverage', 0)
        
        if diag >= 0.95 and art >= 0.95 and supp >= 0.95:
            first_95_95_95 = year_str
            break
    
    if first_95_95_95:
        milestones.append(('First 95-95-95', first_95_95_95, 'Achieved'))
    else:
        milestones.append(('First 95-95-95', 'Not achieved', '-'))
    
    # 4. Prevalence < 1% (low prevalence)
    first_low_prev = None
    for year_str in sorted(data.keys()):
        agg = data[year_str].get('aggregate', {})
        prev = agg.get('prevalence', 0)
        if prev < 0.01:
            first_low_prev = year_str
            break
    
    if first_low_prev:
        milestones.append(('Prevalence < 1%', first_low_prev, 'Achieved'))
    else:
        milestones.append(('Prevalence < 1%', 'Not achieved', '-'))
    
    # 5. Incidence reduction (compare final to baseline)
    baseline_year = sorted(data.keys())[0]
    final_year = sorted(data.keys())[-1]
    
    baseline_inc = data[baseline_year].get('aggregate', {}).get('new_infections', 0)
    final_inc = data[final_year].get('aggregate', {}).get('new_infections', 0)
    
    if baseline_inc > 0:
        reduction = (baseline_inc - final_inc) / baseline_inc
        milestones.append(('Incidence Reduction',
                          f"{baseline_year} → {final_year}",
                          f"{reduction:.1%}"))
    
    # Display milestones
    print("KEY MILESTONES:")
    print("-" * 80)
    print(f"{'Milestone':<25} {'Year/Period':<20} {'Value'}")
    print("-" * 80)
    for milestone, year, value in milestones:
        print(f"{milestone:<25} {year:<20} {value}")
    
    print("\n" + "=" * 80)
    
    # Save to file
    milestone_file = os.path.join(results_dir, 'milestones.json')
    milestone_data = {m[0]: {'year': m[1], 'value': m[2]} for m in milestones}
    with open(milestone_file, 'w') as f:
        json.dump(milestone_data, f, indent=2)
    
    print(f"✓ Milestones saved: {milestone_file}")
    print("=" * 80)


def benchmark_model(args):
    """Benchmark model performance."""
    print("=" * 80)
    print("MODEL BENCHMARKING")
    print("=" * 80)
    
    params = load_parameters(args.config)
    params.initial_population = args.population
    
    print(f"Configuration: {args.config}")
    print(f"Population: {args.population:,}")
    print(f"Years: {params.start_year} - {params.end_year}\n")
    
    print("Initializing model...")
    import time
    init_start = time.time()
    model = EnhancedHIVModel(params)
    init_time = time.time() - init_start
    
    print(f"✓ Initialization: {init_time:.2f} seconds\n")
    
    print("Running simulation...")
    run_start = time.time()
    model.run(years=params.end_year - params.start_year)
    run_time = time.time() - run_start
    
    print(f"✓ Simulation: {run_time:.2f} seconds\n")
    
    # Performance metrics
    total_years = params.end_year - params.start_year
    years_per_sec = total_years / run_time if run_time > 0 else 0
    agents_years_per_sec = (args.population * total_years) / run_time if run_time > 0 else 0
    
    print("PERFORMANCE METRICS:")
    print("-" * 80)
    print(f"  Total time: {run_time:.2f} seconds")
    print(f"  Years simulated: {total_years}")
    print(f"  Agent-years: {args.population * total_years:,}")
    print(f"  Speed: {years_per_sec:.2f} years/second")
    print(f"  Throughput: {agents_years_per_sec:,.0f} agent-years/second")
    
    # Memory estimate (rough)
    history_size = len(model.history)
    print(f"\n  History records: {history_size}")
    
    print("\n" + "=" * 80)
    print("✓ BENCHMARK COMPLETE")
    print("=" * 80)


def comprehensive_validation(results_dir, validation_targets):
    """Comprehensive validation against historical data."""
    print("=" * 80)
    print("COMPREHENSIVE VALIDATION")
    print("=" * 80)
    print(f"Results: {results_dir}")
    print(f"Validation data: {validation_targets}\n")
    
    # Load simulation results
    json_file = os.path.join(results_dir, 'detailed_results.json')
    if not os.path.exists(json_file):
        print(f"❌ Results not found: {json_file}")
        return
    
    with open(json_file, 'r') as f:
        sim_data = json.load(f)
    
    # Load validation targets
    if not os.path.exists(validation_targets):
        print(f"❌ Validation data not found: {validation_targets}")
        return
    
    val_df = pd.read_csv(validation_targets)
    
    print("VALIDATION ANALYSIS:")
    print("-" * 80)
    
    # Compare prevalence
    errors = []
    for _, row in val_df.iterrows():
        year = str(int(row['year']))
        target_prev = row['prevalence']
        
        if year in sim_data:
            sim_prev = sim_data[year].get('aggregate', {}).get('prevalence', 0)
            error = abs(sim_prev - target_prev)
            errors.append(error)
            
            status = "✓" if error < 0.01 else "⚠️" if error < 0.02 else "❌"
            print(f"{status} Year {year}: Target={target_prev:.2%}, "
                  f"Simulated={sim_prev:.2%}, Error={error:.3%}")
    
    if errors:
        mae = np.mean(errors)
        rmse = np.sqrt(np.mean([e**2 for e in errors]))
        
        print("\n" + "-" * 80)
        print(f"SUMMARY:")
        print(f"  Mean Absolute Error (MAE): {mae:.3%}")
        print(f"  Root Mean Square Error (RMSE): {rmse:.3%}")
        print(f"  Max Error: {max(errors):.3%}")
        
        quality = "Excellent" if mae < 0.01 else "Good" if mae < 0.02 else "Needs improvement"
        print(f"  Validation quality: {quality}")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HIVEC-CM Validation and Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate parameters
  %(prog)s --mode validate --config config/parameters.json
  
  # Compute milestones
  %(prog)s --mode milestones --dir results/S0_baseline
  
  # Benchmark performance
  %(prog)s --mode benchmark --config config/parameters.json --population 25000
  
  # Comprehensive validation
  %(prog)s --mode comprehensive --dir results/S0_baseline \\
           --validation data/validation_targets/prevalence_unaids.csv
        """
    )
    
    parser.add_argument('--mode', type=str, required=True,
                       choices=['validate', 'milestones', 'benchmark', 'comprehensive'],
                       help='Validation mode')
    
    parser.add_argument('--config', type=str, default='config/parameters.json',
                       help='Configuration file')
    
    parser.add_argument('--dir', type=str,
                       help='Results directory')
    
    parser.add_argument('--population', type=int, default=25000,
                       help='Population for benchmarking')
    
    parser.add_argument('--validation', type=str,
                       help='Validation targets CSV file')
    
    args = parser.parse_args()
    
    # Execute based on mode
    if args.mode == 'validate':
        validate_parameters(args.config)
    
    elif args.mode == 'milestones':
        if not args.dir:
            print("❌ --dir required for milestones mode")
            return 1
        compute_milestones(args.dir)
    
    elif args.mode == 'benchmark':
        benchmark_model(args)
    
    elif args.mode == 'comprehensive':
        if not args.dir or not args.validation:
            print("❌ --dir and --validation required for comprehensive mode")
            return 1
        comprehensive_validation(args.dir, args.validation)
    
    print("\n✓ Validation complete!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
