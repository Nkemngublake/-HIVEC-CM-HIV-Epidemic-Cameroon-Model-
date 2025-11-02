#!/usr/bin/env python3
"""
HIVEC-CM Unified Simulation Runner
Comprehensive simulation execution with multiple modes:
  1. Single scenario simulation
  2. All policy scenarios execution
  3. Monte Carlo uncertainty analysis
  
Consolidates: run_simulation.py, run_all_scenarios.py, run_enhanced_montecarlo.py, run_study_pipeline.py
"""

import argparse
import os
import sys
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel
from hivec_cm.scenarios.scenario_definitions import SCENARIO_REGISTRY, list_scenarios


def print_banner(mode):
    """Print execution banner."""
    print("=" * 80)
    print("HIVEC-CM: HIV Epidemic Cameroon Model")
    print(f"Mode: {mode.upper()}")
    print("=" * 80)
    print()


def save_detailed_results(model, output_dir, scenario_id):
    """
    Save comprehensive detailed results: JSON + flattened CSV.
    Includes age-sex stratification, regional data, and all dimensions.
    """
    print(f"\n📊 Saving detailed results...")
    
    # 1. Save complete JSON with all data dimensions
    json_file = os.path.join(output_dir, 'detailed_results.json')
    detailed_data = {}
    
    for year_data in model.history:
        year = year_data['year']
        detailed_data[year] = {
            'aggregate': {
                'population': year_data.get('population', 0),
                'susceptible': year_data.get('susceptible', 0),
                'infected': year_data.get('infected', 0),
                'on_art': year_data.get('on_art', 0),
                'deaths': year_data.get('deaths', 0),
                'new_infections': year_data.get('new_infections', 0),
                'prevalence': year_data.get('prevalence', 0)
            },
            'age_sex_prevalence': year_data.get('age_sex_prevalence', {}),
            'regional_prevalence': year_data.get('regional_prevalence', {}),
            'treatment_cascade_95_95_95': year_data.get('treatment_cascade_95_95_95', {}),
            'incidence_by_age_sex': year_data.get('incidence_by_age_sex', {}),
            'mortality_by_age_sex': year_data.get('mortality_by_age_sex', {}),
            'art_coverage_by_region': year_data.get('art_coverage_by_region', {}),
            'key_populations': year_data.get('key_populations', {})
        }
    
    with open(json_file, 'w') as f:
        json.dump(detailed_data, f, indent=2)
    print(f"  ✓ Saved JSON: {json_file}")
    
    # 2. Create flattened CSV for easy analysis
    csv_file = os.path.join(output_dir, 'detailed_age_sex_results.csv')
    rows = []
    
    for year_data in model.history:
        year = year_data['year']
        
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
                        'population': values.get('population', 0),
                        'infected': values.get('infected', 0),
                        'prevalence_pct': values.get('prevalence', 0) * 100
                    })
        
        # Regional prevalence by age-sex
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
                                    'region': region,
                                    'age_group': age_group,
                                    'sex': sex,
                                    'population': values.get('population', 0),
                                    'infected': values.get('infected', 0),
                                    'prevalence_pct': values.get('prevalence', 0) * 100
                                })
    
    df = pd.DataFrame(rows)
    df.to_csv(csv_file, index=False)
    print(f"  ✓ Saved CSV: {csv_file} ({len(df):,} rows)")
    
    # 3. Save metadata
    metadata_file = os.path.join(output_dir, 'run_metadata.json')
    metadata = {
        'scenario_id': scenario_id,
        'execution_time': datetime.now().isoformat(),
        'model_version': '4.0',
        'years_simulated': len(model.history),
        'data_dimensions': list(detailed_data[list(detailed_data.keys())[0]].keys()),
        'output_files': {
            'json': os.path.basename(json_file),
            'csv': os.path.basename(csv_file),
            'metadata': os.path.basename(metadata_file)
        }
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✓ Saved metadata: {metadata_file}")


def run_single_scenario(args):
    """Execute a single scenario simulation."""
    print_banner("Single Scenario")
    
    # Load parameters
    params = load_parameters(args.config)
    params.initial_population = args.population
    
    # Get scenario if specified
    scenario_id = args.scenario if hasattr(args, 'scenario') else 'S0_baseline'
    if scenario_id in SCENARIO_REGISTRY:
        scenario_class = SCENARIO_REGISTRY[scenario_id]
        scenario = scenario_class()
        print(f"Scenario: {scenario.name}")
        print(f"Description: {scenario.description}\n")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, f"simulation_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize and run model
    print(f"Initializing model with {args.population:,} agents...")
    model = EnhancedHIVModel(params)
    
    print(f"Running simulation: {params.start_year} to {params.end_year}")
    start_time = time.time()
    model.run(years=params.end_year - params.start_year)
    duration = time.time() - start_time
    
    print(f"\n✓ Simulation completed in {duration:.1f} seconds")
    
    # Save results
    save_detailed_results(model, output_dir, scenario_id)
    
    # Save basic CSV
    basic_csv = os.path.join(output_dir, 'results.csv')
    df = pd.DataFrame(model.history)
    df.to_csv(basic_csv, index=False)
    print(f"  ✓ Saved basic results: {basic_csv}")
    
    print(f"\n📁 All results saved to: {output_dir}")
    return output_dir


def run_all_scenarios(args):
    """Execute all 9 policy scenarios."""
    print_banner("All Policy Scenarios")
    
    # List available scenarios
    scenarios = list_scenarios()
    print(f"Executing {len(scenarios)} scenarios:")
    for i, s in enumerate(scenarios, 1):
        print(f"  {i}. {s['id']}: {s['name']}")
    print()
    
    # Create base output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.join(args.output, f"scenarios_{timestamp}")
    os.makedirs(base_dir, exist_ok=True)
    
    results_summary = []
    
    for scenario_info in scenarios:
        scenario_id = scenario_info['id']
        
        print(f"\n{'=' * 80}")
        print(f"RUNNING: {scenario_id}")
        print(f"{'=' * 80}")
        
        # Get scenario configuration
        scenario_class = SCENARIO_REGISTRY[scenario_id]
        scenario = scenario_class()
        
        print(f"Scenario: {scenario.name}")
        print(f"Description: {scenario.description}\n")
        
        # Create scenario output directory
        scenario_dir = os.path.join(base_dir, scenario_id)
        os.makedirs(scenario_dir, exist_ok=True)
        
        # Load fresh parameters for each scenario
        params = load_parameters(args.config)
        params.initial_population = args.population
        
        # Initialize model
        print(f"Initializing model with {args.population:,} agents...")
        model = EnhancedHIVModel(params)
        
        # Run simulation
        print(f"Running: {params.start_year} to {params.end_year}")
        start_time = time.time()
        model.run(years=params.end_year - params.start_year)
        duration = time.time() - start_time
        
        print(f"✓ Completed in {duration:.1f} seconds")
        
        # Save detailed results
        save_detailed_results(model, scenario_dir, scenario_id)
        
        # Save basic CSV
        df = pd.DataFrame(model.history)
        df.to_csv(os.path.join(scenario_dir, 'results.csv'), index=False)
        
        # Collect summary
        final_year = model.history[-1]
        results_summary.append({
            'scenario_id': scenario_id,
            'scenario_name': scenario.name,
            'duration_seconds': duration,
            'final_prevalence': final_year.get('prevalence', 0),
            'final_population': final_year.get('population', 0),
            'final_infections': final_year.get('infected', 0),
            'total_new_infections': sum(y.get('new_infections', 0) for y in model.history),
            'output_directory': scenario_dir
        })
        
        print(f"✓ Scenario complete: {scenario_dir}")
    
    # Save summary
    summary_file = os.path.join(base_dir, 'scenarios_summary.csv')
    pd.DataFrame(results_summary).to_csv(summary_file, index=False)
    print(f"\n{'=' * 80}")
    print(f"✓ ALL SCENARIOS COMPLETED")
    print(f"📁 Results: {base_dir}")
    print(f"📊 Summary: {summary_file}")
    print(f"{'=' * 80}")
    
    return base_dir


def run_montecarlo(args):
    """Execute Monte Carlo uncertainty analysis."""
    print_banner("Monte Carlo Analysis")
    
    print(f"Running {args.runs} Monte Carlo simulations")
    print(f"Varying parameters with ±{args.uncertainty * 100}% uncertainty\n")
    
    # Load base parameters
    base_params = load_parameters(args.config)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, f"montecarlo_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = []
    
    for run_idx in range(args.runs):
        print(f"\n{'=' * 80}")
        print(f"Monte Carlo Run {run_idx + 1}/{args.runs}")
        print(f"{'=' * 80}")
        
        # Create parameter variation
        params = load_parameters(args.config)
        params.initial_population = args.population
        
        # Vary key parameters within uncertainty bounds
        variation_factor = 1.0 + np.random.uniform(-args.uncertainty, args.uncertainty)
        params.initial_prevalence *= variation_factor
        
        # Initialize and run
        model = EnhancedHIVModel(params)
        
        start_time = time.time()
        model.run(years=params.end_year - params.start_year)
        duration = time.time() - start_time
        
        print(f"✓ Run {run_idx + 1} completed in {duration:.1f} seconds")
        
        # Save individual run
        run_dir = os.path.join(output_dir, f"run_{run_idx + 1:04d}")
        os.makedirs(run_dir, exist_ok=True)
        
        df = pd.DataFrame(model.history)
        df['run_id'] = run_idx + 1
        df.to_csv(os.path.join(run_dir, 'results.csv'), index=False)
        
        all_results.append(df)
        
        # Collect final year stats
        final = model.history[-1]
        print(f"  Final prevalence: {final.get('prevalence', 0):.2%}")
        print(f"  Final infections: {final.get('infected', 0):,.0f}")
    
    # Aggregate results
    print(f"\n{'=' * 80}")
    print("Aggregating Monte Carlo results...")
    combined_df = pd.concat(all_results, ignore_index=True)
    combined_file = os.path.join(output_dir, 'all_runs_combined.csv')
    combined_df.to_csv(combined_file, index=False)
    
    # Calculate statistics
    stats_by_year = combined_df.groupby('year').agg({
        'prevalence': ['mean', 'std', 'min', 'max'],
        'infected': ['mean', 'std', 'min', 'max'],
        'new_infections': ['mean', 'std', 'min', 'max']
    })
    
    stats_file = os.path.join(output_dir, 'statistics_by_year.csv')
    stats_by_year.to_csv(stats_file)
    
    print(f"✓ Monte Carlo analysis complete")
    print(f"📁 Results: {output_dir}")
    print(f"📊 Combined results: {combined_file}")
    print(f"📈 Statistics: {stats_file}")
    print(f"{'=' * 80}")
    
    return output_dir


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='HIVEC-CM Unified Simulation Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single scenario
  %(prog)s --mode single --scenario S0_baseline --population 25000
  
  # All scenarios
  %(prog)s --mode scenarios --population 50000 --output results/policy_analysis
  
  # Monte Carlo (100 runs)
  %(prog)s --mode montecarlo --runs 100 --population 10000 --uncertainty 0.2
        """
    )
    
    parser.add_argument('--mode', type=str, required=True,
                       choices=['single', 'scenarios', 'montecarlo'],
                       help='Execution mode: single scenario, all scenarios, or Monte Carlo')
    
    parser.add_argument('--scenario', type=str, default='S0_baseline',
                       help='Scenario ID for single mode (default: S0_baseline)')
    
    parser.add_argument('--population', type=int, default=25000,
                       help='Number of agents (default: 25000)')
    
    parser.add_argument('--config', type=str, default='config/parameters.json',
                       help='Configuration file (default: config/parameters.json)')
    
    parser.add_argument('--output', type=str, default='results',
                       help='Output directory (default: results/)')
    
    parser.add_argument('--runs', type=int, default=100,
                       help='Number of Monte Carlo runs (default: 100)')
    
    parser.add_argument('--uncertainty', type=float, default=0.15,
                       help='Parameter uncertainty for Monte Carlo (default: 0.15 = ±15%%)')
    
    args = parser.parse_args()
    
    # Execute based on mode
    if args.mode == 'single':
        output_dir = run_single_scenario(args)
    elif args.mode == 'scenarios':
        output_dir = run_all_scenarios(args)
    elif args.mode == 'montecarlo':
        output_dir = run_montecarlo(args)
    
    print(f"\n✓ Execution complete!")
    print(f"📁 Output: {output_dir}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
