import argparse
import os
import pandas as pd

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel
from analysis.analyzer import ModelAnalyzer, save_analysis_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="HIVEC-CM CLI: run simulations and generate analysis",
    )
    parser.add_argument(
        "--config",
        default="config/parameters.json",
        help="Path to parameter configuration JSON",
    )
    parser.add_argument("--population", type=int, default=None, help="Initial population size override")
    parser.add_argument("--years", type=int, default=35, help="Years to simulate")
    parser.add_argument("--dt", type=float, default=0.1, help="Time step in years")
    parser.add_argument("--start-year", type=int, default=1990, help="Simulation start year")
    parser.add_argument("--output", default="results", help="Output directory")
    parser.add_argument("--no-plots", action="store_true", help="Skip analysis plots")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument(
        "--mixing-method",
        choices=["binned", "scan"],
        default="binned",
        help="Partner selection method (binned: fast; scan: baseline)",
    )
    parser.add_argument(
        "--use-numba",
        action="store_true",
        help="Enable Numba-accelerated Poisson sampling when available",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not os.path.exists(args.config):
        raise FileNotFoundError(f"Config file not found: {args.config}")

    params = load_parameters(args.config)
    if args.population is not None:
        params.initial_population = args.population

    os.makedirs(args.output, exist_ok=True)

    model = EnhancedHIVModel(
        params,
        start_year=args.start_year,
        seed=args.seed,
        use_numba=args.use_numba if args.use_numba else None,
        mixing_method=args.mixing_method,
    )
    results = model.run_simulation(years=args.years, dt=args.dt)

    results_path = os.path.join(args.output, "simulation_results.csv")
    results.to_csv(results_path, index=False)

    if not args.no_plots:
        analyzer = ModelAnalyzer(results, None)
        save_analysis_results(analyzer, os.path.join(args.output, "analysis"))

    print("\n✓ Simulation completed")
    print(f"Results: {results_path}")
    if not args.no_plots:
        print(f"Dashboard: {args.output}/analysis/comprehensive_analysis_dashboard.png")


if __name__ == "__main__":
    main()
