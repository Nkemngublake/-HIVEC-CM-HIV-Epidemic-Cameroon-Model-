"""
Main Entry Point for HIVEC-CM
=============================

Command-line interface and orchestration for the HIVEC-CM (HIV Epidemic Cameroon Model)
with configuration management and comprehensive analysis pipeline.
"""

import argparse
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from hivec_cm.models.model import EnhancedHIVModel
from hivec_cm.models.parameters import load_parameters, ModelParameters
from models.calibrator import run_comprehensive_calibration
from analysis.analyzer import ModelAnalyzer, save_analysis_results
from utils.data_loader import load_cameroon_data, validate_data


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='HIV/AIDS Epidemiological Model for Cameroon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default parameters
  python -m src.main
  
  # Run with custom configuration
  python -m src.main --config config/custom.yaml
  
  # Run calibration only
  python -m src.main --calibrate-only
  
  # Run with specific parameters
  python -m src.main --years 30 --population 100000
        """
    )
    
    # Basic simulation parameters
    parser.add_argument('--config', type=str, default='config/parameters.json',
                       help='Parameter configuration file path (JSON)')
    parser.add_argument('--years', type=int, default=35,
                       help='Simulation duration in years')
    parser.add_argument('--population', type=int, default=75000,
                       help='Initial population size')
    parser.add_argument('--dt', type=float, default=0.1,
                       help='Time step for simulation')
    
    # Model options
    parser.add_argument('--calibrate', action='store_true',
                       help='Run calibration before simulation')
    parser.add_argument('--calibrate-only', action='store_true',
                       help='Run calibration only (no full simulation)')
    parser.add_argument('--calibration-method', type=str, 
                       choices=['differential_evolution', 'nelder_mead'],
                       default='differential_evolution',
                       help='Calibration method to use')
    
    # Output options
    parser.add_argument('--output', type=str, default='results',
                       help='Output directory')
    parser.add_argument('--no-plots', action='store_true',
                       help='Skip generating plots')
    parser.add_argument('--save-config', action='store_true',
                       help='Save used configuration to output directory')
    
    # Data options
    parser.add_argument('--data-file', type=str,
                       help='Custom data file for calibration')
    parser.add_argument('--validate-data', action='store_true',
                       help='Validate input data before running')
    
    # Logging options
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--log-file', type=str,
                       help='Log file path')
    
    return parser


def load_configuration(config_path: str, args: argparse.Namespace) -> dict:
    """Build a simple runtime configuration from CLI options.

    Parameters themselves are loaded via JSON using `load_parameters`.
    """
    return {
        'simulation': {
            'years': args.years,
            'dt': args.dt,
        },
        'calibration': {
            'method': args.calibration_method,
        },
        'io': {
            'config_path': config_path,
            'output': args.output,
        },
    }


def run_calibration(config: dict, data_file: str = None) -> ModelParameters:
    """Run model calibration."""
    logging.info("Starting model calibration...")
    
    # Load calibration data
    try:
        calibration_data = load_cameroon_data(data_file)
        logging.info(f"Loaded calibration data: {len(calibration_data)} records")
    except Exception as e:
        logging.error(f"Failed to load calibration data: {e}")
        raise
    
    # Run calibration
    calibration_results = run_comprehensive_calibration(
        calibration_data, 
        EnhancedHIVModel,
        config.get('calibration', {}).get('method', 'differential_evolution')
    )
    
    # Log calibration results
    best_params = calibration_results['best_parameters']
    objective_value = calibration_results['objective_value']
    validation_metrics = calibration_results['validation_metrics']
    
    logging.info(f"Calibration completed with objective value: {objective_value:.4f}")
    logging.info(f"Validation MAE: {validation_metrics['MAE']:.3f}")
    logging.info(f"Validation R²: {validation_metrics['R_squared']:.3f}")
    
    return best_params, calibration_results


def run_simulation(params: ModelParameters, config: dict, *, start_year: int = 1990) -> tuple:
    """Run the main HIV epidemic simulation."""
    logging.info("Starting epidemic simulation...")
    
    # Load data for validation
    try:
        validation_data = load_cameroon_data()
    except Exception:
        validation_data = None
        logging.warning("No validation data available")
    
    # Initialize and run model
    model = EnhancedHIVModel(params, validation_data, start_year=start_year)
    
    simulation_config = config.get('simulation', {})
    results = model.run_simulation(
        years=simulation_config.get('years', 35),
        dt=simulation_config.get('dt', 0.1)
    )
    
    logging.info(f"Simulation completed: {len(results)} time points")
    
    return results, validation_data


def run_analysis(results, validation_data, config: dict, output_dir: str):
    """Run comprehensive analysis and generate outputs."""
    logging.info("Starting comprehensive analysis...")
    
    # Initialize analyzer
    analyzer = ModelAnalyzer(results, validation_data)
    
    # Run all analyses
    epidemic_indicators = analyzer.calculate_epidemic_indicators()
    transmission_dynamics = analyzer.analyze_transmission_dynamics()
    intervention_impact = analyzer.analyze_intervention_impact()
    validation_metrics = analyzer.validate_against_real_data()
    
    # Save results
    analysis_output_dir = os.path.join(output_dir, 'analysis')
    save_analysis_results(analyzer, analysis_output_dir)
    
    # Print summary
    print_summary(epidemic_indicators, validation_metrics)
    
    return analyzer


def print_summary(epidemic_indicators: dict, validation_metrics: dict = None):
    """Print simulation summary to console."""
    print("\n" + "="*60)
    print("HIV/AIDS EPIDEMIC MODEL - SIMULATION SUMMARY")
    print("="*60)
    
    print(f"Peak HIV Prevalence: {epidemic_indicators['peak_prevalence'] * 100:.2f}% "
          f"(Year: {epidemic_indicators['peak_year']:.0f})")
    print(f"Final HIV Prevalence: {epidemic_indicators['final_prevalence'] * 100:.2f}%")
    print(f"Final ART Coverage: {epidemic_indicators['final_art_coverage'] * 100:.1f}%")
    print(f"Total HIV Infections: {epidemic_indicators['total_infections']:,}")
    print(f"Estimated Deaths: {epidemic_indicators['cumulative_deaths']:,}")
    
    if validation_metrics:
        print(f"\nModel Validation:")
        print(f"Mean Absolute Error: {validation_metrics['mae']:.2f} percentage points")
        print(f"R-squared: {validation_metrics['r_squared']:.3f}")
        print(f"Correlation: {validation_metrics['correlation']:.3f}")
    
    print("="*60)


def save_run_metadata(config: dict, output_dir: str, 
                     calibration_results: dict = None,
                     params: ModelParameters = None):
    """Save run metadata and configuration."""
    metadata = {
        'run_info': {
            'timestamp': datetime.now().isoformat(),
            'model_version': '3.0',
            'description': 'Enhanced HIV/AIDS Epidemiological Model for Cameroon'
        },
        'configuration': config,
    }
    
    if calibration_results:
        metadata['calibration'] = {
            'method': calibration_results['calibration_method'],
            'objective_value': calibration_results['objective_value'],
            'validation_metrics': calibration_results['validation_metrics']
        }
    if params is not None:
        try:
            from dataclasses import asdict
            metadata['parameters'] = asdict(params)
        except Exception:
            pass
    
    metadata_path = os.path.join(output_dir, 'run_metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    logging.info(f"Run metadata saved to {metadata_path}")


def main():
    """Main execution function."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    logging.info("Starting HIV/AIDS Epidemiological Model")
    logging.info(f"Command line arguments: {vars(args)}")
    
    try:
        # Load configuration and parameters
        config = load_configuration(args.config, args)
        if not os.path.exists(args.config):
            raise FileNotFoundError(f"Config file not found: {args.config}")
        params = load_parameters(args.config)
        # Allow CLI to override initial population from config
        if args.population is not None:
            try:
                params.initial_population = int(args.population)
                logging.info(f"Overriding initial population to {params.initial_population}")
            except Exception:
                logging.warning("Failed to apply population override; using config value")

        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Validate data if requested
        if args.validate_data:
            logging.info("Validating input data...")
            validate_data(args.data_file)
        
        calibration_results = None
        
        # Run calibration if requested
        if args.calibrate or args.calibrate_only:
            best_params, calibration_results = run_calibration(config, args.data_file)
            # Apply population override to calibrated params as well
            if args.population is not None:
                try:
                    best_params.initial_population = int(args.population)
                except Exception:
                    pass
        else:
            # Use parameters from JSON (possibly overridden above)
            best_params = params
        
        # Exit early if calibration-only
        if args.calibrate_only:
            logging.info("Calibration completed. Exiting as requested.")
            return
        
        # Run main simulation
        results, validation_data = run_simulation(best_params, config, start_year=1990)
        
        # Save raw results
        results_path = os.path.join(args.output, 'simulation_results.csv')
        results.to_csv(results_path, index=False)
        logging.info(f"Simulation results saved to {results_path}")
        
        # Run analysis
        if not args.no_plots:
            analyzer = run_analysis(results, validation_data, config, args.output)
        
        # Save configuration if requested
        if args.save_config:
            config_path = os.path.join(args.output, 'used_configuration.yaml')
            ConfigManager().save_config(config, config_path)
            logging.info(f"Configuration saved to {config_path}")
        
        # Save run metadata
        save_run_metadata(config, args.output, calibration_results, params=best_params)
        
        logging.info(f"All outputs saved to {args.output}")
        print(f"\n✓ Model run completed successfully!")
        print(f"📁 Results saved to: {args.output}")
        print(f"📊 Analysis dashboard: {args.output}/analysis/comprehensive_analysis_dashboard.png")
        print(f"📋 Full report: {args.output}/analysis/comprehensive_analysis_report.txt")
        
    except Exception as e:
        logging.error(f"Model execution failed: {e}")
        raise


if __name__ == "__main__":
    main()
