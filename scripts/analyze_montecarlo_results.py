#!/usr/bin/env python3
"""
Statistical Analysis Framework for Monte Carlo HIV Study
Generates confidence intervals, significance tests, and summary statistics
"""

import argparse
import os
import json
import logging
from datetime import datetime

import numpy as np
import pandas as pd
import scipy.stats as stats


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def setup_logging(output_dir: str):
    log_file = os.path.join(output_dir, f"analysis_{datetime.now():%Y%m%d_%H%M%S}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


def calculate_confidence_intervals(data: np.ndarray, confidence_level=0.95):
    if data is None or len(data) == 0:
        return np.nan, np.nan, np.nan
    clean = data[~np.isnan(data)]
    if len(clean) == 0:
        return np.nan, np.nan, np.nan
    mean_val = float(np.mean(clean))
    if len(clean) == 1:
        return mean_val, mean_val, mean_val
    sem = stats.sem(clean)
    h = sem * stats.t.ppf((1 + confidence_level) / 2.0, len(clean) - 1)
    return mean_val, float(mean_val - h), float(mean_val + h)


def perform_significance_test(baseline_data, treatment_data, test_year):
    base = baseline_data[~np.isnan(baseline_data)]
    treat = treatment_data[~np.isnan(treatment_data)]
    if len(base) == 0 or len(treat) == 0:
        return {
            'year': test_year, 't_statistic': np.nan, 'p_value': np.nan,
            'cohens_d': np.nan, 'baseline_mean': np.nan,
            'treatment_mean': np.nan, 'difference': np.nan,
            'significant': False,
        }
    try:
        t_stat, p_val = stats.ttest_ind(base, treat)
    except Exception:
        t_stat, p_val = np.nan, np.nan
    # Cohen's d
    pooled_std = np.sqrt(
        ((len(base) - 1) * np.var(base, ddof=1) + (len(treat) - 1) * np.var(treat, ddof=1)) /
        (len(base) + len(treat) - 2)
    )
    d = (np.mean(treat) - np.mean(base)) / pooled_std if pooled_std > 0 else np.nan
    return {
        'year': test_year,
        't_statistic': float(t_stat) if np.isfinite(t_stat) else np.nan,
        'p_value': float(p_val) if np.isfinite(p_val) else np.nan,
        'cohens_d': float(d) if np.isfinite(d) else np.nan,
        'baseline_mean': float(np.mean(base)),
        'treatment_mean': float(np.mean(treat)),
        'difference': float(np.mean(treat) - np.mean(base)),
        'significant': bool(p_val < 0.05) if np.isfinite(p_val) else False,
    }


def analyze_trajectory_statistics(df: pd.DataFrame, metrics):
    results = {}
    years = sorted(df['year'].unique())
    for metric in metrics:
        if metric not in df.columns:
            continue
        results[metric] = {
            'years': [int(y) for y in years],
            'baseline': {'mean': [], 'ci_lower': [], 'ci_upper': []},
            'funding_cut': {'mean': [], 'ci_lower': [], 'ci_upper': []},
        }
        for year in years:
            subset = df[df['year'] == year]
            for scenario in ['baseline', 'funding_cut']:
                vals = subset[subset['scenario'] == scenario][metric].values
                m, lo, hi = calculate_confidence_intervals(vals)
                results[metric][scenario]['mean'].append(m)
                results[metric][scenario]['ci_lower'].append(lo)
                results[metric][scenario]['ci_upper'].append(hi)
    return results


def calculate_summary_statistics_by_decade(df: pd.DataFrame, metrics):
    results = {}
    decades = {'2020s': (2020, 2029), '2030s': (2030, 2039), '2040s': (2040, 2049)}
    for name, (start_y, end_y) in decades.items():
        dec = df[(df['year'] >= start_y) & (df['year'] <= end_y)]
        if dec.empty:
            continue
        results[name] = {}
        for metric in metrics:
            if metric not in dec.columns:
                continue
            stats_by_scen = {}
            for scen in ['baseline', 'funding_cut']:
                vals = dec[dec['scenario'] == scen][metric].values
                if len(vals) == 0:
                    continue
                stats_by_scen[scen] = {
                    'mean': float(np.mean(vals)),
                    'median': float(np.median(vals)),
                    'std': float(np.std(vals)),
                    'q25': float(np.percentile(vals, 25)),
                    'q75': float(np.percentile(vals, 75)),
                    'min': float(np.min(vals)),
                    'max': float(np.max(vals)),
                    'n_observations': int(len(vals)),
                }
            results[name][metric] = stats_by_scen
    return results


def calculate_cumulative_impacts(df: pd.DataFrame):
    out = {}
    for scen in ['baseline', 'funding_cut']:
        sub = df[df['scenario'] == scen]
        if sub.empty:
            continue
        rep = sub.groupby('replication').agg({
            'new_infections': 'sum', 'deaths_hiv': 'sum', 'births': 'sum'
        }).reset_index()
        out[scen] = {
            'total_new_infections': {
                'mean': float(rep['new_infections'].mean()),
                'std': float(rep['new_infections'].std()),
                'median': float(rep['new_infections'].median()),
            },
            'total_hiv_deaths': {
                'mean': float(rep['deaths_hiv'].mean()),
                'std': float(rep['deaths_hiv'].std()),
                'median': float(rep['deaths_hiv'].median()),
            },
            'total_births': {
                'mean': float(rep['births'].mean()),
                'std': float(rep['births'].std()),
                'median': float(rep['births'].median()),
            },
        }
    if 'baseline' in out and 'funding_cut' in out:
        base_inf = df[df['scenario'] == 'baseline'].groupby('replication')['new_infections'].sum()
        cut_inf = df[df['scenario'] == 'funding_cut'].groupby('replication')['new_infections'].sum()
        diff_inf = cut_inf.values - base_inf.values
        base_d = df[df['scenario'] == 'baseline'].groupby('replication')['deaths_hiv'].sum()
        cut_d = df[df['scenario'] == 'funding_cut'].groupby('replication')['deaths_hiv'].sum()
        diff_d = cut_d.values - base_d.values
        out['excess_impacts'] = {
            'excess_infections': {
                'mean': float(np.mean(diff_inf)), 'std': float(np.std(diff_inf)),
                'median': float(np.median(diff_inf)),
                'ci_lower': float(np.percentile(diff_inf, 2.5)),
                'ci_upper': float(np.percentile(diff_inf, 97.5)),
            },
            'excess_deaths': {
                'mean': float(np.mean(diff_d)), 'std': float(np.std(diff_d)),
                'median': float(np.median(diff_d)),
                'ci_lower': float(np.percentile(diff_d, 2.5)),
                'ci_upper': float(np.percentile(diff_d, 97.5)),
            },
        }
    return out


def main():
    parser = argparse.ArgumentParser(description="Statistical Analysis of Monte Carlo HIV Study")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--confidence-level", type=float, default=0.95)
    parser.add_argument("--test-years", nargs='+', type=int, default=[2030, 2040, 2050])
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    logger = setup_logging(args.output_dir)
    logger.info("Starting statistical analysis of Monte Carlo results")

    df = pd.read_csv(args.input_file)
    logger.info(f"Loaded {len(df)} observations")

    metrics = ['prevalence_pct', 'incidence_per_1000', 'hiv_mortality_per_1000', 'art_coverage_pct', 'total_population']

    trajectory_stats = analyze_trajectory_statistics(df, metrics)
    with open(os.path.join(args.output_dir, "trajectory_statistics.json"), 'w') as f:
        json.dump(trajectory_stats, f, indent=2, cls=NumpyEncoder)

    significance_results = {}
    for year in args.test_years:
        yd = df[df['year'] == year]
        if yd.empty:
            continue
        significance_results[str(year)] = {}
        for metric in metrics:
            if metric in df.columns:
                res = perform_significance_test(
                    yd[yd['scenario'] == 'baseline'][metric].values,
                    yd[yd['scenario'] == 'funding_cut'][metric].values,
                    year,
                )
                significance_results[str(year)][metric] = res
    with open(os.path.join(args.output_dir, "significance_tests.json"), 'w') as f:
        json.dump(significance_results, f, indent=2, cls=NumpyEncoder)

    decade_stats = calculate_summary_statistics_by_decade(df, metrics)
    with open(os.path.join(args.output_dir, "decade_statistics.json"), 'w') as f:
        json.dump(decade_stats, f, indent=2, cls=NumpyEncoder)

    cumulative = calculate_cumulative_impacts(df)
    with open(os.path.join(args.output_dir, "cumulative_impacts.json"), 'w') as f:
        json.dump(cumulative, f, indent=2, cls=NumpyEncoder)

    # Executive summary
    final_year = int(df['year'].max())
    final_data = df[df['year'] == final_year]
    summary = {
        'study_overview': {
            'total_simulations': int(len(df['replication'].unique()) * len(df['scenario'].unique())),
            'scenarios': list(map(str, df['scenario'].unique())),
            'replications_per_scenario': {k: int(v) for k, v in df.groupby('scenario')['replication'].nunique().to_dict().items()},
            'time_period': f"{int(df['year'].min())} to {final_year}",
            'confidence_level': args.confidence_level,
        },
        'key_findings': {},
        'significance_summary': {},
    }
    for metric in metrics:
        if metric in final_data.columns:
            base = final_data[final_data['scenario'] == 'baseline'][metric].values
            cut = final_data[final_data['scenario'] == 'funding_cut'][metric].values
            if len(base) > 0 and len(cut) > 0:
                bm, blo, bhi = calculate_confidence_intervals(base)
                cm, clo, chi = calculate_confidence_intervals(cut)
                summary['key_findings'][metric] = {
                    'final_year': final_year,
                    'baseline': {'mean': bm, 'ci_lower': blo, 'ci_upper': bhi},
                    'funding_cut': {'mean': cm, 'ci_lower': clo, 'ci_upper': chi},
                    'absolute_difference': float(cm - bm),
                    'relative_difference_pct': float((cm - bm) / bm * 100) if bm != 0 else np.nan,
                }
    significant_years = {}
    for year_str, yr in significance_results.items():
        sig_metrics = [m for m, res in yr.items() if res.get('significant')]
        if sig_metrics:
            significant_years[year_str] = sig_metrics
    summary['significance_summary'] = {
        'years_tested': args.test_years,
        'significant_differences_by_year': significant_years,
        'total_significant_tests': int(sum(len(v) for v in significant_years.values())),
    }
    with open(os.path.join(args.output_dir, "executive_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2, cls=NumpyEncoder)

    logging.info("Statistical analysis completed successfully")
    logging.info(f"Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()

