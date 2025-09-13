#!/usr/bin/env python3
"""
End-to-end Monte Carlo pipeline runner

1) Runs the Monte Carlo study (baseline vs funding_cut)
2) Analyzes statistics and significance
3) Generates publication-ready plots (multi-format)

Example (small test):
  python scripts/run_study_pipeline.py \
    --config config/parameters.json \
    --population-size 10000 --replications 5 \
    --start-year 2020 --end-year 2030 \
    --processes 1 --formats png pdf
"""

import argparse
import os
import sys
import subprocess
from glob import glob


def most_recent_study_dir(base_dir: str) -> str | None:
    paths = glob(os.path.join(base_dir, "study_*/"))
    if not paths:
        return None
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return paths[0].rstrip("/")


def run(cmd: list[str]):
    print("\n$", " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(f"Command failed: {' '.join(cmd)}")
    if proc.stdout:
        print(proc.stdout)
    return proc


def main():
    parser = argparse.ArgumentParser(description="Run Monte Carlo + Analysis + Plots pipeline")
    parser.add_argument("--config", default="config/parameters.json")
    parser.add_argument("--population-size", type=int, default=50000)
    parser.add_argument("--replications", type=int, default=50)
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2050)
    parser.add_argument("--art-funding-cut-year", type=int, default=2025)
    parser.add_argument("--art-funding-cut-magnitude", type=float, default=0.30)
    parser.add_argument("--kp-prevention-cut-magnitude", type=float, default=0.40)
    parser.add_argument("--processes", type=int, default=0, help="0 uses all cores")
    parser.add_argument("--output-dir", default="results/montecarlo_study")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--formats", nargs='+', default=["png"], choices=["png", "pdf", "svg"])
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--compute-milestones", action='store_true', help="Compute milestone years and export summary")
    parser.add_argument("--incidence-threshold", type=float, default=1.0)
    parser.add_argument("--incidence-threshold-scale", choices=["per1000","per100000"], default="per1000")
    parser.add_argument("--prevalence-threshold", type=float, default=2.0)
    parser.add_argument("--art-threshold", type=float, default=90.0)
    parser.add_argument("--generate-report", action='store_true', help="Generate compact PDF report from plots and labels")
    # Single-run publication plots
    parser.add_argument("--include-single-run", action='store_true', help="Also run a single simulation and generate publication plots")
    parser.add_argument("--single-population", type=int, default=None, help="Single-run population override")
    parser.add_argument("--single-years", type=float, default=60.0, help="Single-run duration in years")
    parser.add_argument("--single-dt", type=float, default=1.0, help="Single-run dt")
    parser.add_argument("--single-start-year", type=int, default=1990, help="Single-run start year")

    args = parser.parse_args()

    # 1) Monte Carlo run
    mc_cmd = [
        sys.executable, "scripts/run_montecarlo_study.py",
        "--config", args.config,
        "--population-size", str(args.population_size),
        "--replications", str(args.replications),
        "--start-year", str(args.start_year),
        "--end-year", str(args.end_year),
        "--art-funding-cut-year", str(args.art_funding_cut_year),
        "--art-funding-cut-magnitude", str(args.art_funding_cut_magnitude),
        "--kp-prevention-cut-magnitude", str(args.kp_prevention_cut_magnitude),
        "--output-dir", args.output_dir,
        "--random-seed", str(args.random_seed),
    ]
    if args.processes and args.processes > 0:
        mc_cmd.extend(["--processes", str(args.processes)])
    run(mc_cmd)

    study_dir = most_recent_study_dir(args.output_dir)
    if not study_dir:
        raise SystemExit("Could not locate study directory")

    results_csv = os.path.join(study_dir, "montecarlo_results.csv")
    metadata_json = os.path.join(study_dir, "study_metadata.json")
    analysis_dir = os.path.join(study_dir, "analysis")
    plots_dir = os.path.join(study_dir, "plots")

    # 2) Statistical analysis
    run([
        sys.executable, "scripts/analyze_montecarlo_results.py",
        "--input-file", results_csv,
        "--output-dir", analysis_dir,
    ])

    # Export labels for LaTeX/manuscripts
    run([
        sys.executable, "scripts/export_labels.py",
        "--analysis-dir", analysis_dir,
    ])

    if args.compute_milestones:
        run([
            sys.executable, "scripts/compute_milestones.py",
            "--input-file", results_csv,
            "--output-dir", analysis_dir,
            "--incidence-threshold", str(args.incidence_threshold),
            "--incidence-scale", args.incidence_threshold_scale,
            "--prevalence-threshold", str(args.prevalence_threshold),
            "--art-threshold", str(args.art_threshold),
        ])

    # 3) Visualization (publication-ready; multi-format)
    run([
        sys.executable, "scripts/visualize_montecarlo_results.py",
        "--input-file", results_csv,
        "--metadata-file", metadata_json,
        "--output-dir", plots_dir,
        "--funding-cut-year", str(args.art_funding_cut_year),
        "--funding-cut-magnitude", str(args.art_funding_cut_magnitude),
        "--incidence-scale", args.incidence_threshold_scale,
        "--mortality-scale", args.incidence_threshold_scale,
        "--formats", *args.formats,
        "--dpi", str(args.dpi),
    ])

    # Optionally run single simulation + publication plots
    if args.include_single_run:
        single_dir = os.path.join(study_dir, "single_run")
        os.makedirs(single_dir, exist_ok=True)
        single_results = os.path.join(single_dir, "simulation_results.csv")

        sim_cmd = [
            sys.executable, "scripts/run_simulation.py",
            "--config", args.config,
            "--population", str(args.single_population or args.population_size),
            "--years", str(int(args.single_years)),
            "--dt", str(args.single_dt),
            "--start-year", str(args.single_start_year),
            "--output-dir", single_dir,
        ]
        run(sim_cmd)

        run([
            sys.executable, "scripts/generate_publication_plots.py",
            "--results-file", single_results,
            "--output-dir", os.path.join(single_dir, "publication_plots"),
            "--formats", *args.formats,
            "--dpi", str(args.dpi),
            "--funding-cut-year", str(args.art_funding_cut_year),
            "--funding-cut-magnitude", str(args.art_funding_cut_magnitude),
        ])

    print("\nPipeline complete!")
    print("Study dir:", study_dir)
    print("Analysis:", analysis_dir)
    print("Plots:", plots_dir)
    if args.include_single_run:
        print("Single-run publication plots:", os.path.join(study_dir, "single_run", "publication_plots"))
    if args.generate_report:
        run([
            sys.executable, "scripts/generate_report.py",
            "--study-dir", study_dir,
        ])


if __name__ == "__main__":
    main()
