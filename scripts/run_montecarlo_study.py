#!/usr/bin/env python3
"""
Comprehensive Monte Carlo Simulation Study for HIV Epidemic Model
Executes 50 independent replications per scenario (baseline vs funding cuts)
"""

import argparse
import multiprocessing as mp
import os
import sys
import json
import pandas as pd
import numpy as np
import time
from datetime import datetime
import logging
from functools import partial

# Add src to path for model imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel

# Global variable for progress tracking
simulation_counter = 0
total_simulations = 0


def setup_logging(output_dir):
    """Setup logging for Monte Carlo study."""
    log_file = os.path.join(
        output_dir, f"montecarlo_run_{datetime.now():%Y%m%d_%H%M%S}.log"
    )
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def run_single_simulation(args_tuple):
    """
    Run a single simulation replication.
    Args_tuple: (replication_id, scenario, params_dict, random_seed)
    """
    replication_id, scenario, params_dict, random_seed = args_tuple
    
    try:
        # Set random seed for reproducibility with process-specific offset
        process_seed = (random_seed + replication_id + hash(scenario)) % (2**31 - 1)
        np.random.seed(process_seed)
        
        print(f"Starting {scenario} replication {replication_id} "
              f"with seed {process_seed}")
        
        # Load parameters
        params = load_parameters(params_dict['config_file'])
        
        # Apply scenario-specific modifications
        if scenario == 'funding_cut':
            params.funding_cut_scenario = True
            params.funding_cut_year = params_dict['art_funding_cut_year']
            params.funding_cut_magnitude = params_dict[
                'art_funding_cut_magnitude'
            ]
            params.kp_prevention_cut_magnitude = params_dict[
                'kp_prevention_cut_magnitude'
            ]
        else:
            params.funding_cut_scenario = False
        
        # Override initial population size if specified
        if 'population_size' in params_dict:
            params.initial_population = params_dict['population_size']
        
        # Run simulation
        start_time = time.time()
        model = EnhancedHIVModel(
            params=params,
            start_year=params_dict['start_year'],
            seed=process_seed,
        )
        
        # Calculate simulation years from start year to end year
        total_years = params_dict['end_year'] - params_dict['start_year']
        results_df = model.run_simulation(years=total_years)
        
        end_time = time.time()
        
        # Filter to requested year range (model already starts at start_year)
        results_df = results_df[
            (results_df['year'] >= params_dict['start_year']) &
            (results_df['year'] <= params_dict['end_year'])
        ]
        
        # Calculate derived metrics
        results_df['incidence_per_1000'] = np.where(
            results_df['susceptible'] > 0,
            (results_df['new_infections'] / results_df['susceptible']) *
            1000.0,
            0
        )
        results_df['prevalence_pct'] = np.where(
            results_df['total_population'] > 0,
            (results_df['hiv_infections'] / results_df['total_population']) *
            100.0,
            0
        )
        results_df['hiv_mortality_per_1000'] = np.where(
            results_df['total_population'] > 0,
            (results_df['deaths_hiv'] / results_df['total_population']) *
            1000.0,
            0
        )
        results_df['art_coverage_pct'] = np.where(
            results_df['hiv_infections'] > 0,
            (results_df['on_art'] / results_df['hiv_infections']) * 100.0,
            0
        )
        
        # Add metadata
        results_df['replication'] = replication_id
        results_df['scenario'] = scenario
        results_df['runtime_seconds'] = end_time - start_time
        
        return results_df
        
    except Exception as e:
        print(f"Error in replication {replication_id}, "
              f"scenario {scenario}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Monte Carlo Study of HIV Epidemic Model"
    )
    parser.add_argument(
        "--config",
        default=os.path.join(
            os.path.dirname(__file__), "../config/parameters.json"
        ),
        help="Path to parameters configuration file"
    )
    parser.add_argument(
        "--population-size", type=int, default=50000,
        help="Number of agents in simulation (default: 50000)"
    )
    parser.add_argument(
        "--replications", type=int, default=50,
        help="Number of replications per scenario (default: 50)"
    )
    parser.add_argument(
        "--start-year", type=int, default=2020,
        help="Simulation start year (default: 2020)"
    )
    parser.add_argument(
        "--end-year", type=int, default=2050,
        help="Simulation end year (default: 2050)"
    )
    parser.add_argument(
        "--art-funding-cut-year", type=int, default=2025,
        help="Year when ART funding cut begins (default: 2025)"
    )
    parser.add_argument(
        "--art-funding-cut-magnitude", type=float, default=0.3,
        help="ART funding cut magnitude (default: 0.3 = 30% cut)"
    )
    parser.add_argument(
        "--kp-prevention-cut-magnitude", type=float, default=0.4,
        help="Key population prevention cut (default: 0.4 = 40% cut)"
    )
    parser.add_argument(
        "--processes", type=int, default=None,
        help="Number of parallel processes (default: all CPU cores)"
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(
            os.path.dirname(__file__), "../results/montecarlo_study"
        ),
        help="Output directory for results"
    )
    parser.add_argument(
        "--random-seed", type=int, default=42,
        help="Base random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, f"study_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup logging
    logger = setup_logging(output_dir)
    logger.info("Starting Monte Carlo simulation study")
    
    # Prepare simulation parameters
    params_dict = {
        'config_file': args.config,
        'population_size': args.population_size,
        'start_year': args.start_year,
        'end_year': args.end_year,
        'art_funding_cut_year': args.art_funding_cut_year,
        'art_funding_cut_magnitude': args.art_funding_cut_magnitude,
        'kp_prevention_cut_magnitude': args.kp_prevention_cut_magnitude
    }
    
    # Generate simulation tasks
    scenarios = ['baseline', 'funding_cut']
    simulation_tasks = []
    
    for scenario in scenarios:
        for replication in range(args.replications):
            # Generate unique seed for each replication
            seed = args.random_seed + (len(scenarios) * replication) + \
                scenarios.index(scenario)
            simulation_tasks.append(
                (replication + 1, scenario, params_dict, seed)
            )
    
    total_simulations = len(simulation_tasks)
    logger.info(f"Total simulations to run: {total_simulations}")
    logger.info(f"Scenarios: {scenarios}")
    logger.info(f"Replications per scenario: {args.replications}")
    logger.info(f"Population size: {args.population_size}")
    logger.info(f"Time period: {args.start_year} to {args.end_year}")
    
    # Determine number of processes
    if args.processes is None:
        processes = mp.cpu_count()
    else:
        processes = min(args.processes, mp.cpu_count())
    
    logger.info(f"Using {processes} parallel processes")
    
    # Run simulations in parallel
    logger.info("Starting parallel simulations...")
    start_time = time.time()
    
    with mp.Pool(processes=processes) as pool:
        results = pool.map(run_single_simulation, simulation_tasks)
    
    end_time = time.time()
    total_runtime = end_time - start_time
    
    logger.info(f"All simulations completed in {total_runtime:.2f} seconds")
    
    # Filter successful results
    successful_results = [r for r in results if r is not None]
    failed_count = len(results) - len(successful_results)
    
    if failed_count > 0:
        logger.warning(f"{failed_count} simulations failed")
    
    logger.info(f"{len(successful_results)} simulations successful")
    
    # Combine all results
    if successful_results:
        logger.info("Combining simulation results...")
        combined_df = pd.concat(successful_results, ignore_index=True)
        
        # Save raw results
        results_file = os.path.join(output_dir, "montecarlo_results.csv")
        combined_df.to_csv(results_file, index=False)
        logger.info(f"Raw results saved to: {results_file}")
        
        # Save metadata
        metadata = {
            'study_parameters': {
                'population_size': args.population_size,
                'replications_per_scenario': args.replications,
                'scenarios': scenarios,
                'start_year': args.start_year,
                'end_year': args.end_year,
                'art_funding_cut_year': args.art_funding_cut_year,
                'art_funding_cut_magnitude': args.art_funding_cut_magnitude,
                'kp_prevention_cut_magnitude': (
                    args.kp_prevention_cut_magnitude
                ),
                'random_seed': args.random_seed
            },
            'execution_summary': {
                'total_simulations_requested': total_simulations,
                'successful_simulations': len(successful_results),
                'failed_simulations': failed_count,
                'total_runtime_seconds': total_runtime,
                'parallel_processes': processes,
                'timestamp': timestamp
            },
            'data_structure': {
                'total_rows': len(combined_df),
                'columns': list(combined_df.columns),
                'scenarios_in_data': sorted(combined_df['scenario'].unique()),
                'replications_per_scenario': combined_df.groupby('scenario')[
                    'replication'
                ].nunique().to_dict(),
                'year_range': [
                    int(combined_df['year'].min()),
                    int(combined_df['year'].max())
                ]
            }
        }
        
        metadata_file = os.path.join(output_dir, "study_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Study metadata saved to: {metadata_file}")
        
        # Generate summary statistics
        logger.info("Generating summary statistics...")
        
        # Calculate mean trajectories by scenario
        summary_stats = combined_df.groupby(['scenario', 'year']).agg({
            'prevalence_pct': ['mean', 'std'],
            'incidence_per_1000': ['mean', 'std'],
            'hiv_mortality_per_1000': ['mean', 'std'],
            'art_coverage_pct': ['mean', 'std'],
            'total_population': ['mean', 'std'],
            'new_infections': ['mean', 'std'],
            'deaths_hiv': ['mean', 'std'],
            'births': ['mean', 'std']
        }).round(3)
        
        summary_file = os.path.join(output_dir, "summary_statistics.csv")
        summary_stats.to_csv(summary_file)
        logger.info(f"Summary statistics saved to: {summary_file}")
        
        logger.info("Monte Carlo study completed successfully!")
        logger.info(f"Results directory: {output_dir}")
        
        # Print key findings
        final_year_data = combined_df[combined_df['year'] == args.end_year]
        
        if not final_year_data.empty:
            logger.info("\n=== KEY FINDINGS ===")
            for scenario in scenarios:
                scenario_data = final_year_data[
                    final_year_data['scenario'] == scenario
                ]
                if not scenario_data.empty:
                    prevalence_mean = scenario_data['prevalence_pct'].mean()
                    prevalence_std = scenario_data['prevalence_pct'].std()
                    logger.info(
                        f"{scenario.upper()} {args.end_year}: "
                        f"Prevalence = {prevalence_mean:.2f}% "
                        f"(±{prevalence_std:.2f}%)"
                    )
        
        return output_dir
    
    else:
        logger.error("No successful simulations - cannot generate results")
        return None


if __name__ == "__main__":
    result_dir = main()
    if result_dir:
        print("\nMonte Carlo study completed successfully!")
        print(f"Results saved to: {result_dir}")
        print("\nNext steps:")
        print("1. Analyze results: python "
              "scripts/analyze_montecarlo_results.py "
              f"--input-file {result_dir}/montecarlo_results.csv "
              f"--output-dir {result_dir}/analysis")
        print("2. Generate plots: python "
              "scripts/visualize_montecarlo_results.py "
              f"--input-file {result_dir}/montecarlo_results.csv "
              f"--output-dir {result_dir}/plots")
    else:
        print("Monte Carlo study failed!")
        sys.exit(1)
