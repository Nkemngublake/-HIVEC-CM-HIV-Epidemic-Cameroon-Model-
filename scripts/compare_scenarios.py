import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt


def ensure_outdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['prevalence_pct'] = out['hiv_prevalence'] * 100.0
    out['incidence_per_1000'] = (
        (out['new_infections'] / out['susceptible'])
        .replace([float('inf')], 0.0)
        * 1000.0
    )
    out['mortality_per_1000'] = (
        (out['deaths_hiv'] / out['total_population'])
        .replace([float('inf')], 0.0)
        * 1000.0
    )
    return out


def plot_two_series(x1, y1, x2, y2, title, xlabel, ylabel, labels, filename):
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(x1, y1, label=labels[0], linewidth=2.2, color='#1f77b4')
    ax.plot(x2, y2, label=labels[1], linewidth=2.2, color='#d62728')

    # Funding cut marker
    ax.axvline(x=2025, color='black', linestyle='--', linewidth=1.2)
    ax.text(2026, ax.get_ylim()[1] * 0.9, 'Funding Cut', fontsize=9)

    ax.set_title(title, fontsize=16, weight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.8)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved plot: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare baseline vs. funding-cut scenario and produce merged "
            "figures."
        )
    )
    parser.add_argument(
        '--baseline-file', required=True,
        help='Path to baseline simulation_results.csv'
    )
    parser.add_argument(
        '--scenario-file', required=True,
        help='Path to funding cut simulation_results.csv'
    )
    parser.add_argument('--baseline-label', default='Baseline')
    parser.add_argument('--scenario-label', default='Funding cut (2025)')
    parser.add_argument(
        '--output-dir', required=True,
        help='Directory to write comparison figures'
    )
    args = parser.parse_args()

    ensure_outdir(args.output_dir)

    base = pd.read_csv(args.baseline_file)
    scen = pd.read_csv(args.scenario_file)

    base_i = compute_indicators(base)
    scen_i = compute_indicators(scen)

    # Align on shared years (inner join on year)
    merged = pd.merge(
        base_i[
            [
                'year',
                'prevalence_pct',
                'incidence_per_1000',
                'mortality_per_1000',
            ]
        ],
        scen_i[
            [
                'year',
                'prevalence_pct',
                'incidence_per_1000',
                'mortality_per_1000',
            ]
        ],
        on='year', suffixes=('_base', '_scen'), how='inner'
    )

    # 1. Prevalence
    plot_two_series(
        merged['year'], merged['prevalence_pct_base'],
        merged['year'], merged['prevalence_pct_scen'],
        'HIV Prevalence: Baseline vs Funding Cut (2025)',
        'Year', 'Prevalence (%)',
        [args.baseline_label, args.scenario_label],
        os.path.join(args.output_dir, 'compare_prevalence.png')
    )

    # 2. Incidence rate per 1,000 susceptible
    plot_two_series(
        merged['year'], merged['incidence_per_1000_base'],
        merged['year'], merged['incidence_per_1000_scen'],
        (
            'HIV Incidence Rate (per 1,000 Susceptible):\n'
            'Baseline vs Funding Cut (2025)'
        ),
        'Year', 'Incidence per 1,000',
        [args.baseline_label, args.scenario_label],
        os.path.join(args.output_dir, 'compare_incidence.png')
    )

    # 3. HIV-related mortality per 1,000 population
    plot_two_series(
        merged['year'], merged['mortality_per_1000_base'],
        merged['year'], merged['mortality_per_1000_scen'],
        (
            'HIV-Related Mortality (per 1,000 Population):\n'
            'Baseline vs Funding Cut (2025)'
        ),
        'Year', 'Mortality per 1,000',
        [args.baseline_label, args.scenario_label],
        os.path.join(args.output_dir, 'compare_mortality.png')
    )


if __name__ == '__main__':
    main()
