#!/usr/bin/env python3
"""
Visualization Script for Monte Carlo HIV Study Results
Generates publication-ready plots with confidence intervals and statistical annotations
"""

import argparse
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import logging


def setup_plotting_style(formats=("png",), dpi=300):
    """Setup publication-ready plotting style."""
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")
    
    # Configure matplotlib for publication quality
    plt.rcParams.update({
        'font.size': 12,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16,
        'figure.dpi': dpi,
        'savefig.dpi': dpi,
        'savefig.bbox': 'tight'
    })
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['ps.fonttype'] = 42

def _save_multi(filepath_base: str, formats=("png",)):
    for fmt in formats:
        out = f"{os.path.splitext(filepath_base)[0]}.{fmt}"
        plt.savefig(out)


def _pair_replication_metric(df, metric):
    """Construct a paired DataFrame by year and replication with baseline and funding_cut columns.

    Returns a DataFrame with columns: year, replication, baseline, funding_cut
    Filters out rows where either scenario is missing for that year/replication.
    """
    subset = df[['year', 'replication', 'scenario', metric]].dropna()
    wide = subset.pivot_table(index=['year', 'replication'], columns='scenario', values=metric)
    wide = wide.reset_index()
    if 'baseline' in wide.columns and 'funding_cut' in wide.columns:
        wide = wide.dropna(subset=['baseline', 'funding_cut'])
    else:
        wide = wide.iloc[0:0]  # empty
    return wide


def _ci_from_samples(samples, confidence=0.95):
    import numpy as _np
    clean = _np.array(samples)
    clean = clean[~_np.isnan(clean)]
    if clean.size == 0:
        return _np.nan, _np.nan, _np.nan
    mean = float(_np.mean(clean))
    if clean.size == 1:
        return mean, mean, mean
    from scipy import stats as _stats
    sem = _stats.sem(clean)
    h = sem * _stats.t.ppf((1 + confidence) / 2.0, clean.size - 1)
    return mean, float(mean - h), float(mean + h)


def plot_difference_trajectory(df, metric, output_dir, title_suffix=""):
    """Plot funding_cut - baseline difference with 95% CI by year."""
    paired = _pair_replication_metric(df, metric)
    if paired.empty:
        return None
    years = sorted(paired['year'].unique())
    diffs_mean, diffs_lo, diffs_hi = [], [], []
    for y in years:
        s = paired[paired['year'] == y]
        diffs = s['funding_cut'].values - s['baseline'].values
        m, lo, hi = _ci_from_samples(diffs)
        diffs_mean.append(m); diffs_lo.append(lo); diffs_hi.append(hi)

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.plot(years, diffs_mean, color='#A23B72', linewidth=2.5, label='Difference')
    ax.fill_between(years, diffs_lo, diffs_hi, color='#A23B72', alpha=0.2)
    ax.axhline(0, color='black', linewidth=1, linestyle='--')
    ax.set_xlabel('Year'); ax.set_ylabel(f"{metric.replace('_',' ').title()} (Δ Funding Cut - Baseline)")
    ax.set_title(f"Difference in {metric.replace('_',' ').title()} by Year{title_suffix}")
    ax.grid(True, alpha=0.3)

    filename = f"{metric}_difference_trajectory"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    return filepath


def plot_ratio_trajectory(df, metric, output_dir, title_suffix=""):
    """Plot funding_cut / baseline ratio with 95% CI by year (paired replicates)."""
    paired = _pair_replication_metric(df, metric)
    if paired.empty:
        return None
    years = sorted(paired['year'].unique())
    rr_mean, rr_lo, rr_hi = [], [], []
    from numpy import log, exp
    from scipy import stats as _stats
    for y in years:
        s = paired[paired['year'] == y]
        # Avoid division by zero; drop non-positive baseline values
        valid = s['baseline'].values > 0
        if not valid.any():
            rr_mean.extend([np.nan]); rr_lo.extend([np.nan]); rr_hi.extend([np.nan])
            continue
        r = s['funding_cut'].values[valid] / s['baseline'].values[valid]
        r = r[~np.isnan(r)]
        if r.size == 0:
            rr_mean.append(np.nan); rr_lo.append(np.nan); rr_hi.append(np.nan)
            continue
        lr = log(r)
        m = lr.mean()
        if lr.size > 1:
            sem = _stats.sem(lr)
            h = sem * _stats.t.ppf(0.975, lr.size - 1)
            lo = exp(m - h); hi = exp(m + h)
        else:
            lo = hi = exp(m)
        rr_mean.append(exp(m)); rr_lo.append(lo); rr_hi.append(hi)

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.plot(years, rr_mean, color='#2E86AB', linewidth=2.5, label='Rate/Proportion Ratio')
    ax.fill_between(years, rr_lo, rr_hi, color='#2E86AB', alpha=0.2)
    ax.axhline(1.0, color='black', linewidth=1, linestyle='--')
    ax.set_xlabel('Year'); ax.set_ylabel(f"{metric.replace('_',' ').title()} Ratio (Funding / Baseline)")
    ax.set_title(f"Ratio of {metric.replace('_',' ').title()} by Year{title_suffix}")
    ax.grid(True, alpha=0.3)

    filename = f"{metric}_ratio_trajectory"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    return filepath


def plot_art_cascade_trajectories(df, output_dir, title_suffix=""):
    """Plot testing, diagnosis, and treatment rates among PLHIV with CIs over time."""
    # Compute cascade rates per row
    work = df.copy()
    # Guard against zero division
    for col in ['tested', 'diagnosed', 'on_art', 'hiv_infections']:
        if col not in work.columns:
            return None
    work['testing_rate'] = np.where(work['hiv_infections'] > 0, work['tested'] / work['hiv_infections'] * 100.0, np.nan)
    work['diagnosis_rate'] = np.where(work['hiv_infections'] > 0, work['diagnosed'] / work['hiv_infections'] * 100.0, np.nan)
    work['treatment_rate'] = np.where(work['hiv_infections'] > 0, work['on_art'] / work['hiv_infections'] * 100.0, np.nan)

    metrics = ['testing_rate', 'diagnosis_rate', 'treatment_rate']
    labels = {'testing_rate': 'Tested among PLHIV (%)', 'diagnosis_rate': 'Diagnosed among PLHIV (%)', 'treatment_rate': 'On ART among PLHIV (%)'}
    colors = {'baseline': '#2E86AB', 'funding_cut': '#A23B72'}

    fig, axes = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
    years = sorted(work['year'].unique())
    for i, met in enumerate(metrics):
        ax = axes[i]
        for scen in ['baseline', 'funding_cut']:
            scen_data = work[work['scenario'] == scen]
            means, lo, hi = [], [], []
            for y in years:
                vals = scen_data[scen_data['year'] == y][met].values
                m, l, h = _ci_from_samples(vals)
                means.append(m); lo.append(l); hi.append(h)
            ax.plot(years, means, color=colors[scen], linewidth=2, label=scen.replace('_',' ').title())
            ax.fill_between(years, lo, hi, color=colors[scen], alpha=0.2)
        ax.set_ylabel(labels[met])
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel('Year')
    axes[0].set_title(f'ART Cascade Trajectories{title_suffix}')
    axes[0].legend()

    filename = "art_cascade_trajectories"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    return filepath


def calculate_confidence_intervals(data, confidence_level=0.95):
    """Calculate confidence intervals for plotting."""
    if len(data) == 0:
        return np.nan, np.nan, np.nan
    
    mean_val = np.mean(data)
    std_val = np.std(data)
    n = len(data)
    
    # Use t-distribution for small samples
    from scipy import stats
    sem = std_val / np.sqrt(n)
    h = sem * stats.t.ppf((1 + confidence_level) / 2., n - 1)
    
    return mean_val, mean_val - h, mean_val + h


def plot_trajectory_comparison(df, metric, output_dir, title_suffix="", funding_cut_year=2025, log_scale=False, ylabel_override=None):
    """Plot trajectory comparison between scenarios with confidence intervals."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    years = sorted(df['year'].unique())
    scenarios = sorted(df['scenario'].unique())
    
    colors = {'baseline': '#2E86AB', 'funding_cut': '#A23B72'}
    
    for scenario in scenarios:
        scenario_data = df[df['scenario'] == scenario]
        
        means = []
        ci_lowers = []
        ci_uppers = []
        
        for year in years:
            year_data = scenario_data[scenario_data['year'] == year]
            if not year_data.empty:
                values = year_data[metric].values
                mean_val, ci_low, ci_high = calculate_confidence_intervals(values)
                means.append(mean_val)
                ci_lowers.append(ci_low)
                ci_uppers.append(ci_high)
            else:
                means.append(np.nan)
                ci_lowers.append(np.nan)
                ci_uppers.append(np.nan)
        
        # Plot mean trajectory
        label = scenario.replace('_', ' ').title()
        ax.plot(years, means, color=colors[scenario], linewidth=2.5, 
                label=label, marker='o', markersize=4)
        
        # Plot confidence interval
        ax.fill_between(years, ci_lowers, ci_uppers, 
                       color=colors[scenario], alpha=0.2)
    
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel_override or metric.replace('_', ' ').title())
    ax.set_title(f'{metric.replace("_", " ").title()} Trajectories{title_suffix}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    if log_scale:
        ax.set_yscale('log')
    
    # Add annotation for funding cut year
    ax.axvline(x=funding_cut_year, color='red', linestyle='--', alpha=0.7,
               label='Funding Cut Begins')
    
    filename = f"{metric}_trajectory_comparison"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    
    return filepath


def plot_final_year_comparison(df, output_dir):
    """Plot final year comparison across all metrics."""
    final_year = df['year'].max()
    final_data = df[df['year'] == final_year]
    
    metrics = ['prevalence_pct', 'incidence_per_1000', 'hiv_mortality_per_1000', 
               'art_coverage_pct']
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.ravel()
    
    for i, metric in enumerate(metrics):
        ax = axes[i]
        
        # Create box plot
        sns.boxplot(data=final_data, x='scenario', y=metric, ax=ax)
        
        # Add mean markers
        for scenario in final_data['scenario'].unique():
            scenario_data = final_data[final_data['scenario'] == scenario]
            mean_val = scenario_data[metric].mean()
            scenario_idx = list(final_data['scenario'].unique()).index(scenario)
            ax.scatter(scenario_idx, mean_val, color='red', s=100, 
                      marker='D', zorder=10, label='Mean' if i == 0 else "")
        
        ax.set_title(f'{metric.replace("_", " ").title()} ({final_year})')
        ax.set_xlabel('Scenario')
        ax.set_ylabel(metric.replace('_', ' ').title())
    
    # Add legend to first subplot
    if len(axes) > 0:
        axes[0].legend()
    
    plt.suptitle(f'Final Year ({final_year}) Comparison Across Key Metrics', 
                 fontsize=16)
    plt.tight_layout()
    
    filename = f"final_year_{final_year}_comparison"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    
    return filepath


def plot_cumulative_impacts(df, output_dir):
    """Plot cumulative impacts over the study period."""
    # Calculate cumulative metrics by replication and scenario
    cumulative_data = []
    
    for scenario in df['scenario'].unique():
        for replication in df['replication'].unique():
            rep_data = df[(df['scenario'] == scenario) & 
                         (df['replication'] == replication)]
            
            if not rep_data.empty:
                cumulative_data.append({
                    'scenario': scenario,
                    'replication': replication,
                    'total_new_infections': rep_data['new_infections'].sum(),
                    'total_hiv_deaths': rep_data['deaths_hiv'].sum(),
                    'total_births': rep_data['births'].sum()
                })
    
    cumulative_df = pd.DataFrame(cumulative_data)
    
    if cumulative_df.empty:
        return None
    
    # Create comparison plots
    metrics = ['total_new_infections', 'total_hiv_deaths', 'total_births']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for i, metric in enumerate(metrics):
        ax = axes[i]
        
        # Create violin plot
        sns.violinplot(data=cumulative_df, x='scenario', y=metric, ax=ax)
        
        # Add statistical annotation
        baseline_values = cumulative_df[cumulative_df['scenario'] == 'baseline'][metric]
        funding_cut_values = cumulative_df[cumulative_df['scenario'] == 'funding_cut'][metric]
        
        if len(baseline_values) > 0 and len(funding_cut_values) > 0:
            from scipy.stats import ttest_ind
            t_stat, p_val = ttest_ind(baseline_values, funding_cut_values)
            
            # Add significance annotation
            y_max = max(cumulative_df[metric].max(), 
                       baseline_values.max(), 
                       funding_cut_values.max())
            
            significance_text = f"p = {p_val:.3f}"
            if p_val < 0.001:
                significance_text = "p < 0.001***"
            elif p_val < 0.01:
                significance_text = f"p = {p_val:.3f}**"
            elif p_val < 0.05:
                significance_text = f"p = {p_val:.3f}*"
            
            ax.annotate(significance_text, 
                       xy=(0.5, 0.95), xycoords='axes fraction',
                       ha='center', va='top', fontsize=10,
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(f'{metric.replace("_", " ").title()}')
        ax.set_xlabel('Scenario')
        ax.set_ylabel('Cumulative Count')
    
    plt.suptitle('Cumulative Impacts Over Study Period', fontsize=16)
    plt.tight_layout()
    
    filename = "cumulative_impacts_comparison"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    
    return filepath


def plot_time_series_panels(df, output_dir):
    """Create comprehensive time series panel plots."""
    metrics = ['prevalence_pct', 'incidence_per_1000', 'hiv_mortality_per_1000', 
               'art_coverage_pct', 'total_population']
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    axes = axes.ravel()
    
    for i, metric in enumerate(metrics):
        if i < len(axes):
            ax = axes[i]
            
            years = sorted(df['year'].unique())
            scenarios = sorted(df['scenario'].unique())
            
            colors = {'baseline': '#2E86AB', 'funding_cut': '#A23B72'}
            
            for scenario in scenarios:
                scenario_data = df[df['scenario'] == scenario]
                
                # Calculate yearly statistics
                yearly_stats = scenario_data.groupby('year')[metric].agg([
                    'mean', 'std', 'count'
                ]).reset_index()
                
                means = yearly_stats['mean'].values
                stds = yearly_stats['std'].values
                
                # Plot mean with error bars
                label = scenario.replace('_', ' ').title()
                ax.errorbar(yearly_stats['year'], means, yerr=stds, 
                           color=colors[scenario], linewidth=2, 
                           label=label, marker='o', markersize=3,
                           capsize=3, capthick=1)
            
            ax.set_xlabel('Year')
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_title(f'{metric.replace("_", " ").title()}')
            ax.legend()
            ax.grid(True, alpha=0.3)
    
    # Remove empty subplot if metrics < axes
    if len(metrics) < len(axes):
        fig.delaxes(axes[-1])
    
    plt.suptitle('HIV Epidemic Trajectories: Monte Carlo Results', fontsize=16)
    plt.tight_layout()
    
    filename = "comprehensive_time_series"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    
    return filepath


def generate_executive_summary_plot(df, metadata, output_dir, funding_cut_year=2025, funding_cut_magnitude=0.30):
    """Generate executive summary visualization."""
    fig = plt.figure(figsize=(16, 12))
    
    # Create grid layout
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.5], width_ratios=[1, 1])
    
    # 1. Prevalence trajectory (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    years = sorted(df['year'].unique())
    
    for scenario in ['baseline', 'funding_cut']:
        scenario_data = df[df['scenario'] == scenario]
        yearly_means = scenario_data.groupby('year')['prevalence_pct'].mean()
        
        color = '#2E86AB' if scenario == 'baseline' else '#A23B72'
        label = scenario.replace('_', ' ').title()
        
        ax1.plot(yearly_means.index, yearly_means.values, 
                color=color, linewidth=3, label=label, marker='o')
    
    ax1.set_title('HIV Prevalence Trajectory', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Prevalence (%)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Final year comparison (top right)
    ax2 = fig.add_subplot(gs[0, 1])
    final_year = df['year'].max()
    final_data = df[df['year'] == final_year]
    
    sns.boxplot(data=final_data, x='scenario', y='prevalence_pct', ax=ax2)
    ax2.set_title(f'Final Prevalence ({final_year})', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Scenario')
    ax2.set_ylabel('Prevalence (%)')
    
    # 3. Cumulative impacts (bottom left)
    ax3 = fig.add_subplot(gs[1, 0])
    
    cumulative_infections = df.groupby(['scenario', 'replication'])['new_infections'].sum().reset_index()
    sns.barplot(data=cumulative_infections, x='scenario', y='new_infections', ax=ax3)
    ax3.set_title('Cumulative New Infections', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Scenario')
    ax3.set_ylabel('Total New Infections')
    
    # 4. Key statistics summary (bottom right)
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')
    
    # Calculate key statistics
    baseline_final = final_data[final_data['scenario'] == 'baseline']['prevalence_pct']
    funding_cut_final = final_data[final_data['scenario'] == 'funding_cut']['prevalence_pct']
    
    if len(baseline_final) > 0 and len(funding_cut_final) > 0:
        baseline_mean = baseline_final.mean()
        funding_cut_mean = funding_cut_final.mean()
        difference = funding_cut_mean - baseline_mean
        relative_change = (difference / baseline_mean) * 100
        
        stats_text = f"""
        Key Findings ({final_year}):
        
        Baseline Prevalence: {baseline_mean:.1f}%
        Funding Cut Prevalence: {funding_cut_mean:.1f}%
        
        Absolute Difference: {difference:+.1f}%
        Relative Change: {relative_change:+.1f}%
        
        Study Parameters:
        • Population: {metadata.get('study_parameters', {}).get('population_size', 'N/A'):,}
        • Replications: {metadata.get('study_parameters', {}).get('replications_per_scenario', 'N/A')}
        • Time Period: {metadata.get('study_parameters', {}).get('start_year', 'N/A')}-{metadata.get('study_parameters', {}).get('end_year', 'N/A')}
        """
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    # 5. Study information panel (bottom)
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis('off')
    
    info_text = f"""
    Monte Carlo HIV Epidemic Study - Cameroon Model
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Impact of HIV Funding Cuts on Epidemic Trajectories (Baseline vs {int(funding_cut_magnitude*100)}% ART Funding Cut from {funding_cut_year})
    """
    
    ax5.text(0.5, 0.5, info_text, transform=ax5.transAxes, 
            fontsize=12, ha='center', va='center', style='italic',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    plt.tight_layout()
    
    filename = "executive_summary"
    filepath = os.path.join(output_dir, filename)
    _save_multi(filepath)
    plt.close()
    
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Generate visualizations for Monte Carlo HIV study results"
    )
    parser.add_argument(
        "--input-file", required=True,
        help="Path to montecarlo_results.csv"
    )
    parser.add_argument(
        "--metadata-file", 
        help="Path to study_metadata.json (optional)"
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory to save plots"
    )
    parser.add_argument(
        "--formats", nargs='+', default=["png"], choices=["png", "pdf", "svg"],
        help="Image formats to save (default: png)"
    )
    parser.add_argument(
        "--dpi", type=int, default=300, help="DPI for raster outputs (default: 300)"
    )
    parser.add_argument(
        "--confidence-level", type=float, default=0.95,
        help="Confidence level for intervals (default: 0.95)"
    )
    parser.add_argument("--funding-cut-year", type=int, default=2025)
    parser.add_argument("--funding-cut-magnitude", type=float, default=0.30)
    parser.add_argument("--incidence-scale", choices=["per1000", "per100000"], default="per1000",
                        help="Incidence scale for plots (default per1000)")
    parser.add_argument("--mortality-scale", choices=["per1000", "per100000"], default="per1000",
                        help="Mortality scale for plots (default per1000)")
    parser.add_argument("--log-metrics", nargs='*', default=[],
                        help="Metric names to plot with log y-scale (e.g., incidence_per_1000)")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Setup plotting style
    setup_plotting_style(tuple(args.formats), args.dpi)
    # Bind saver with formats
    global _save_multi
    def _save_multi(filepath_base: str, formats=tuple(args.formats)):
        for fmt in formats:
            out = f"{os.path.splitext(filepath_base)[0]}.{fmt}"
            plt.savefig(out)
    
    # Load data
    logger.info(f"Loading data from {args.input_file}")
    df = pd.read_csv(args.input_file)
    
    # Load metadata if available
    metadata = {}
    if args.metadata_file and os.path.exists(args.metadata_file):
        with open(args.metadata_file, 'r') as f:
            metadata = json.load(f)
    
    logger.info(f"Loaded {len(df)} observations")
    logger.info(f"Generating visualizations...")
    
    # Generate plots
    plots_created = []
    
    # 1. Key metric trajectories (respect scale options)
    key_metrics = ['prevalence_pct', 'art_coverage_pct']
    # Incidence scaling
    inc_metric = 'incidence_per_1000'
    inc_ylabel = 'Incidence Rate (per 1,000)'
    if args.incidence_scale == 'per100000':
        # derive per 100,000 if not present
        if 'incidence_per_100000' not in df.columns and 'incidence_per_1000' in df.columns:
            df['incidence_per_100000'] = df['incidence_per_1000'] * 100.0
        inc_metric = 'incidence_per_100000'
        inc_ylabel = 'Incidence Rate (per 100,000)'
    key_metrics.append(inc_metric)
    # Mortality scaling
    mort_metric = 'hiv_mortality_per_1000'
    mort_ylabel = 'HIV Mortality (per 1,000)'
    if args.mortality_scale == 'per100000':
        if 'hiv_mortality_per_100000' not in df.columns and 'hiv_mortality_per_1000' in df.columns:
            df['hiv_mortality_per_100000'] = df['hiv_mortality_per_1000'] * 100.0
        mort_metric = 'hiv_mortality_per_100000'
        mort_ylabel = 'HIV Mortality (per 100,000)'
    key_metrics.append(mort_metric)
    
    for metric in key_metrics:
        if metric in df.columns:
            ylabel = None
            if metric == inc_metric:
                ylabel = inc_ylabel
            elif metric == mort_metric:
                ylabel = mort_ylabel
            plot_path = plot_trajectory_comparison(
                df, metric, args.output_dir, funding_cut_year=args.funding_cut_year,
                log_scale=(metric in args.log_metrics), ylabel_override=ylabel)
            plots_created.append(plot_path)
            logger.info(f"Created: {os.path.basename(plot_path)}")

    # Difference and ratio trajectories for key metrics
    diff_metrics = ['prevalence_pct', inc_metric, mort_metric]
    for metric in diff_metrics:
        if metric in df.columns:
            dp = plot_difference_trajectory(df, metric, args.output_dir, title_suffix=f" (Funding Cut − Baseline)")
            if dp:
                plots_created.append(dp)
            rp = plot_ratio_trajectory(df, metric, args.output_dir)
            if rp:
                plots_created.append(rp)
    
    # 2. Final year comparison
    final_plot = plot_final_year_comparison(df, args.output_dir)
    plots_created.append(final_plot)
    logger.info(f"Created: {os.path.basename(final_plot)}")
    
    # 3. Cumulative impacts
    cumulative_plot = plot_cumulative_impacts(df, args.output_dir)
    if cumulative_plot:
        plots_created.append(cumulative_plot)
        logger.info(f"Created: {os.path.basename(cumulative_plot)}")

    # 3b. ART cascade trajectories
    cascade_plot = plot_art_cascade_trajectories(df, args.output_dir, title_suffix=f" (Funding Cut Year {args.funding_cut_year})")
    if cascade_plot:
        plots_created.append(cascade_plot)
        logger.info(f"Created: {os.path.basename(cascade_plot)}")
    
    # 4. Comprehensive time series
    timeseries_plot = plot_time_series_panels(df, args.output_dir)
    plots_created.append(timeseries_plot)
    logger.info(f"Created: {os.path.basename(timeseries_plot)}")
    
    # 5. Executive summary
    summary_plot = generate_executive_summary_plot(df, metadata, args.output_dir, funding_cut_year=args.funding_cut_year, funding_cut_magnitude=args.funding_cut_magnitude)
    plots_created.append(summary_plot)
    logger.info(f"Created: {os.path.basename(summary_plot)}")
    
    # Save plot inventory
    plot_inventory = {
        'generation_timestamp': datetime.now().isoformat(),
        'input_file': args.input_file,
        'plots_created': [os.path.basename(p) for p in plots_created],
        'plot_descriptions': {
            'trajectory_comparison': 'Time series trajectories with confidence intervals',
            'final_year_comparison': 'Box plots of final year metrics',
            'cumulative_impacts': 'Total cumulative impacts over study period',
            'comprehensive_time_series': 'Multi-panel time series overview',
            'executive_summary': 'Key findings summary visualization'
        }
    }
    
    inventory_file = os.path.join(args.output_dir, "plot_inventory.json")
    with open(inventory_file, 'w') as f:
        json.dump(plot_inventory, f, indent=2)
    
    logger.info(f"Visualization complete! Created {len(plots_created)} plots")
    logger.info(f"Plots saved to: {args.output_dir}")
    logger.info(f"Plot inventory saved to: {inventory_file}")


if __name__ == "__main__":
    main()
