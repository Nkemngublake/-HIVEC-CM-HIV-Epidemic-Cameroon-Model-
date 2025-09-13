#!/usr/bin/env python3
"""
Compute milestone years from Monte Carlo results, with summary statistics.

Examples of milestones:
- Incidence falls below a threshold (per 1,000 or per 100,000)
- Prevalence below a threshold (%)
- ART coverage exceeds a threshold (%)

Outputs JSON and CSV summaries.
"""

import argparse
import os
import json
import csv
import numpy as np
import pandas as pd


def first_year_crossing(series_year, series_val, direction: str, threshold: float):
    """Return first year where series crosses threshold.
    direction: 'below' or 'above'
    """
    if direction == 'below':
        mask = series_val < threshold
    else:
        mask = series_val > threshold
    if not mask.any():
        return None
    idx = np.argmax(mask)  # first True
    return int(series_year.iloc[idx])


def summarize_years(years):
    arr = np.array([y for y in years if y is not None], dtype=float)
    if arr.size == 0:
        return {'mean': None, 'median': None, 'ci_lower': None, 'ci_upper': None, 'n': 0}
    return {
        'mean': float(np.mean(arr)),
        'median': float(np.median(arr)),
        'ci_lower': float(np.percentile(arr, 2.5)),
        'ci_upper': float(np.percentile(arr, 97.5)),
        'n': int(arr.size),
    }


def main():
    p = argparse.ArgumentParser(description="Compute milestone years from Monte Carlo results")
    p.add_argument("--input-file", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--incidence-threshold", type=float, default=1.0, help="Threshold for incidence (per chosen scale)")
    p.add_argument("--incidence-scale", choices=["per1000", "per100000"], default="per1000")
    p.add_argument("--prevalence-threshold", type=float, default=2.0, help="Prevalence (%) threshold")
    p.add_argument("--art-threshold", type=float, default=90.0, help="ART coverage (%) threshold")
    args = p.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    df = pd.read_csv(args.input_file)

    inc_col = 'incidence_per_1000' if args.incidence_scale == 'per1000' else 'incidence_per_100000'
    if inc_col not in df.columns:
        # derive if needed
        if args.incidence_scale == 'per100000' and 'incidence_per_1000' in df.columns:
            df['incidence_per_100000'] = df['incidence_per_1000'] * 100.0
        else:
            raise SystemExit(f"Incidence column not found: {inc_col}")

    results = {}
    labels_rows = []

    for scenario in sorted(df['scenario'].unique()):
        scen = df[df['scenario'] == scenario]
        years_inc = []
        years_prev = []
        years_art = []
        for rep, rep_df in scen.groupby('replication'):
            rep_df = rep_df.sort_values('year')
            y = rep_df['year']
            inc_y = first_year_crossing(y, rep_df[inc_col], 'below', args.incidence_threshold)
            prev_y = first_year_crossing(y, rep_df['prevalence_pct'], 'below', args.prevalence_threshold)
            art_y = first_year_crossing(y, rep_df['art_coverage_pct'], 'above', args.art_threshold)
            years_inc.append(inc_y)
            years_prev.append(prev_y)
            years_art.append(art_y)
        results[scenario] = {
            'incidence_below': summarize_years(years_inc),
            'prevalence_below': summarize_years(years_prev),
            'art_above': summarize_years(years_art),
        }

        # Labels
        labels_rows.append([f"milestone_incidence_below_{args.incidence_threshold}_{scenario}", results[scenario]['incidence_below']['median']])
        labels_rows.append([f"milestone_prevalence_below_{args.prevalence_threshold}_{scenario}", results[scenario]['prevalence_below']['median']])
        labels_rows.append([f"milestone_art_above_{args.art_threshold}_{scenario}", results[scenario]['art_above']['median']])

    with open(os.path.join(args.output_dir, 'milestones.json'), 'w') as f:
        json.dump(results, f, indent=2)

    with open(os.path.join(args.output_dir, 'milestones_labels.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['label', 'value']); w.writerows(labels_rows)

    print(f"Saved milestones to {args.output_dir}")


if __name__ == '__main__':
    main()

