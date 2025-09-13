#!/usr/bin/env python3
"""
Export LaTeX-style labels (JSON/CSV) from analysis outputs

Reads executive_summary.json and cumulative_impacts.json and emits label-value
pairs suitable for manuscript embedding.
"""

import argparse
import os
import json
import csv


def fmt(val, ndigits=1):
    if val is None:
        return ''
    try:
        return f"{float(val):.{ndigits}f}"
    except Exception:
        return str(val)


def main():
    p = argparse.ArgumentParser(description="Export labels for LaTeX/manuscripts")
    p.add_argument("--analysis-dir", required=True, help="Directory with analysis JSONs")
    p.add_argument("--output-json", default=None, help="Path to labels.json")
    p.add_argument("--output-csv", default=None, help="Path to labels.csv")
    p.add_argument("--ndigits", type=int, default=1, help="Rounding digits for floats")
    args = p.parse_args()

    exec_path = os.path.join(args.analysis_dir, "executive_summary.json")
    cum_path = os.path.join(args.analysis_dir, "cumulative_impacts.json")
    if not os.path.exists(exec_path):
        raise SystemExit(f"Not found: {exec_path}")

    with open(exec_path) as f:
        exec_data = json.load(f)
    cum_data = {}
    if os.path.exists(cum_path):
        with open(cum_path) as f:
            cum_data = json.load(f)

    # Build labels
    labels = {}
    fy = exec_data.get('study_overview', {}).get('time_period', '').split(' to ')
    final_year = fy[-1] if fy else ''

    kf = exec_data.get('key_findings', {})
    for metric, vals in kf.items():
        base = vals['baseline']['mean']
        cut = vals['funding_cut']['mean']
        labels[f"final_{metric}_baseline_{final_year}"] = fmt(base, args.ndigits)
        labels[f"final_{metric}_fundingcut_{final_year}"] = fmt(cut, args.ndigits)
        labels[f"final_{metric}_diff_abs_{final_year}"] = fmt(vals['absolute_difference'], args.ndigits)
        labels[f"final_{metric}_diff_rel_pct_{final_year}"] = fmt(vals['relative_difference_pct'], args.ndigits)

    # Cumulative impacts label examples
    excess = cum_data.get('excess_impacts', {})
    if excess:
        labels["excess_infections_mean"] = fmt(excess['excess_infections']['mean'], args.ndigits)
        labels["excess_infections_ci"] = f"{fmt(excess['excess_infections']['ci_lower'], args.ndigits)}–{fmt(excess['excess_infections']['ci_upper'], args.ndigits)}"
        labels["excess_deaths_mean"] = fmt(excess['excess_deaths']['mean'], args.ndigits)
        labels["excess_deaths_ci"] = f"{fmt(excess['excess_deaths']['ci_lower'], args.ndigits)}–{fmt(excess['excess_deaths']['ci_upper'], args.ndigits)}"

    # Defaults for outputs
    out_json = args.output_json or os.path.join(args.analysis_dir, "labels.json")
    out_csv = args.output_csv or os.path.join(args.analysis_dir, "labels.csv")

    with open(out_json, 'w') as f:
        json.dump(labels, f, indent=2)
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["label", "value"])
        for k, v in labels.items():
            w.writerow([k, v])

    print(f"Exported labels: {out_json}, {out_csv}")


if __name__ == "__main__":
    main()

