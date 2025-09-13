
import argparse
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel

def main():
    """Main function to run the HIV model from the command line."""
    parser = argparse.ArgumentParser(description="Run the HIVEC-CM model.")
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "../config/parameters.json"),
        help="Path to the parameter configuration file (JSON)."
    )
    parser.add_argument(
        "--population",
        type=int,
        default=1000,
        help="Initial population size."
    )
    parser.add_argument(
        "--years",
        type=int,
        default=35,
        help="Number of years to simulate."
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=0.1,
        help="Time step for the simulation (in years)."
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=1985,
        help="The start year of the simulation."
    )
    parser.add_argument(
        "--funding-cut-scenario",
        action="store_true",
        help="Enable the funding cut scenario."
    )
    parser.add_argument(
        "--funding-cut-magnitude",
        type=float,
        default=0.5,
        help="The magnitude of the funding cut (e.g., 0.5 for 50%)."
    )
    parser.add_argument(
        "--kp-prevention-cut-magnitude",
        type=float,
        default=0.95,
        help="The magnitude of the funding cut for KP prevention activities."
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save the simulation results."
    )
    args = parser.parse_args()

    # Load parameters
    params = load_parameters(args.config)
    params.initial_population = args.population
    params.funding_cut_scenario = args.funding_cut_scenario
    if params.funding_cut_scenario:
        params.funding_cut_year = 2025 # Hardcoded for now
        # These will be used in the model logic
        params.funding_cut_magnitude = args.funding_cut_magnitude
        params.kp_prevention_cut_magnitude = args.kp_prevention_cut_magnitude


    # Initialize and run the model
    model = EnhancedHIVModel(params, start_year=args.start_year)
    results_df = model.run_simulation(years=args.years, dt=args.dt)

    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    results_df.to_csv(os.path.join(args.output_dir, "simulation_results.csv"), index=False)

    print(f"Simulation complete. Results saved to '{args.output_dir}'")

if __name__ == "__main__":
    main()
