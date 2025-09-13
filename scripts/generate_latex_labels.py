#!/usr/bin/env python3
"""
Generate LaTeX inputs (study_config.tex, labels.tex, fig_paths.tex) from a study directory.

Usage:
  python scripts/generate_latex_labels.py \
    --study-dir results/montecarlo_study/study_YYYYMMDD_HHMMSS \
    --out-dir manuscripts

This creates:
  manuscripts/study_config.tex  # macros for StudyDir, years, funding cut params, etc.
  manuscripts/labels.tex        # macros for all labels in labels.json
  manuscripts/fig_paths.tex     # macros for commonly used figure paths
"""

import argparse
import json
import os
import re


def to_macro_name(key: str) -> str:
    # Convert label key to CamelCase macro name with prefix Lbl
    parts = re.split(r"[^A-Za-z0-9]+", key)
    parts = [p for p in parts if p]
    camel = ''.join(s[:1].upper() + s[1:] for s in parts)
    return f"Lbl{camel}"


def write_study_config(study_dir: str, out_dir: str):
    meta_path = os.path.join(study_dir, 'study_metadata.json')
    study_params = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            md = json.load(f)
        study_params = md.get('study_parameters', {})
    start_year = study_params.get('start_year', '')
    end_year = study_params.get('end_year', '')
    pop = study_params.get('population_size', '')
    reps = study_params.get('replications_per_scenario', '')
    fcy = study_params.get('art_funding_cut_year', '')
    fcm = study_params.get('art_funding_cut_magnitude', '')
    kp = study_params.get('kp_prevention_cut_magnitude', '')

    os.makedirs(out_dir, exist_ok=True)
    cfg_path = os.path.join(out_dir, 'study_config.tex')
    with open(cfg_path, 'w') as f:
        f.write('% Auto-generated study configuration\n')
        f.write(f"\\newcommand{{\\StudyDir}}{{{study_dir}}}\n")
        f.write(f"\\newcommand{{\\StartYear}}{{{start_year}}}\n")
        f.write(f"\\newcommand{{\\EndYear}}{{{end_year}}}\n")
        f.write(f"\\newcommand{{\\Population}}{{{pop}}}\n")
        f.write(f"\\newcommand{{\\Replications}}{{{reps}}}\n")
        f.write(f"\\newcommand{{\\FundingCutYear}}{{{fcy}}}\n")
        try:
            pct = int(round(float(fcm) * 100)) if fcm not in ('', None) else ''
        except Exception:
            pct = ''
        f.write(f"\\newcommand{{\\FundingCutMagnitudePct}}{{{pct}}}\n")
        if kp not in ('', None):
            try:
                kpp = int(round(float(kp) * 100))
            except Exception:
                kpp = ''
        else:
            kpp = ''
        f.write(f"\\newcommand{{\\KpPreventionCutPct}}{{{kpp}}}\n")
    return cfg_path


def write_labels(study_dir: str, out_dir: str):
    labels_path = os.path.join(study_dir, 'analysis', 'labels.json')
    if not os.path.exists(labels_path):
        return None
    with open(labels_path) as f:
        labels = json.load(f)
    out_path = os.path.join(out_dir, 'labels.tex')
    with open(out_path, 'w') as f:
        f.write('% Auto-generated label macros\n')
        for k, v in labels.items():
            macro = to_macro_name(k)
            # Sanitize value
            if isinstance(v, float):
                vs = f"{v:.1f}"
            else:
                vs = str(v)
            f.write(f"\\newcommand{{\\{macro}}}{{{vs}}}\n")
    return out_path


def write_fig_paths(study_dir: str, out_dir: str):
    """Write macros with figure paths relative to out_dir.

    This ensures LaTeX includes work when compiling from the manuscripts dir.
    """
    exec_path = os.path.join(study_dir, 'analysis', 'executive_summary.json')
    final_year = ''
    try:
        with open(exec_path) as f:
            execd = json.load(f)
        period = execd.get('study_overview', {}).get('time_period', '')
        if ' to ' in period:
            final_year = period.split(' to ')[-1]
    except Exception:
        pass

    plots_abs = os.path.join(study_dir, 'plots')
    # Compute relative paths from the LaTeX output directory (out_dir)
    plots = os.path.relpath(plots_abs, start=out_dir)

    out_path = os.path.join(out_dir, 'fig_paths.tex')
    with open(out_path, 'w') as f:
        f.write('% Auto-generated figure path macros\n')
        f.write(f"\\newcommand{{\\FigPrevTraj}}{{{plots}/prevalence_pct_trajectory_comparison.png}}\n")
        f.write(f"\\newcommand{{\\FigPrevDiff}}{{{plots}/prevalence_pct_difference_trajectory.png}}\n")
        f.write(f"\\newcommand{{\\FigPrevRatio}}{{{plots}/prevalence_pct_ratio_trajectory.png}}\n")
        if final_year:
            f.write(f"\\newcommand{{\\FigFinalYear}}{{{plots}/final_year_{final_year}_comparison.png}}\n")
        else:
            f.write(f"\\newcommand{{\\FigFinalYear}}{{{plots}/final_year_*_comparison.png}}\n")
        f.write(f"\\newcommand{{\\FigTimeseries}}{{{plots}/comprehensive_time_series.png}}\n")
        f.write(f"\\newcommand{{\\FigCumImp}}{{{plots}/cumulative_impacts_comparison.png}}\n")
        f.write(f"\\newcommand{{\\FigCascade}}{{{plots}/art_cascade_trajectories.png}}\n")
        f.write(f"\\newcommand{{\\FigExecSum}}{{{plots}/executive_summary.png}}\n")
    return out_path


def main():
    ap = argparse.ArgumentParser(description='Generate LaTeX includes from study outputs')
    ap.add_argument('--study-dir', required=True, help='Path to study directory')
    ap.add_argument('--out-dir', default='manuscripts', help='Output directory for .tex includes')
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    cfg = write_study_config(args.study_dir, args.out_dir)
    lbl = write_labels(args.study_dir, args.out_dir)
    fig = write_fig_paths(args.study_dir, args.out_dir)
    print('Wrote:', cfg)
    if lbl:
        print('Wrote:', lbl)
    else:
        print('labels.json not found; skipped labels.tex')
    print('Wrote:', fig)


if __name__ == '__main__':
    main()
