
import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse

def create_publication_plot(x, y, title, xlabel, ylabel, filename_base, color, area_fill=True, formats=("png",), dpi=300):
    """Creates a single, high-quality plot for publication."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(x, y, color=color, linewidth=2.5)
    if area_fill:
        ax.fill_between(x, y, color=color, alpha=0.1)

    ax.set_title(title, fontsize=16, weight='bold', pad=20)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, which='major', linestyle='--', linewidth=0.5)
    
    # Add a vertical line and text for the funding cut if present in title text (optional)
    # Note: the caller may pass a title containing magnitude/year; we still draw a reference line if provided
    if hasattr(create_publication_plot, '_funding_cut_year') and create_publication_plot._funding_cut_year is not None:
        fcy = create_publication_plot._funding_cut_year
        ax.axvline(x=fcy, color='black', linestyle='--', linewidth=1.5)
        ax.text(fcy + 1, ax.get_ylim()[1] * 0.9, f'Funding Cut', rotation=0, va='center', fontsize=10)

    # Configure output
    plt.tight_layout()
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['ps.fonttype'] = 42
    for fmt in formats:
        out = f"{os.path.splitext(filename_base)[0]}.{fmt}"
        plt.savefig(out, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved plot(s): {filename_base} ({', '.join(formats)})")

def create_population_composition_plot(df, output_dir, formats=("png",), dpi=300):
    """Stacked area plot of susceptible vs PLHIV over time (single run)."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    years = df['year']
    susceptible = df['susceptible']
    plhiv = df['hiv_infections']
    ax.stackplot(years, susceptible, plhiv, labels=['Susceptible', 'PLHIV'], colors=['#2ca02c', '#d62728'], alpha=0.7)
    ax.set_title('Population Composition Over Time', fontsize=16, weight='bold', pad=20)
    ax.set_xlabel('Year'); ax.set_ylabel('Population')
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.rcParams['pdf.fonttype'] = 42; plt.rcParams['ps.fonttype'] = 42
    base = os.path.join(output_dir, 'population_composition')
    for fmt in formats:
        plt.savefig(f"{base}.{fmt}", dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved plot(s): {base} ({', '.join(formats)})")

def create_cascade_final_year_plot(df, output_dir, formats=("png",), dpi=300):
    """Final year ART cascade percentages among PLHIV (single run)."""
    if not {'tested','diagnosed','on_art','hiv_infections'}.issubset(df.columns):
        return
    fy = int(df['year'].max())
    last = df[df['year'] == fy].iloc[-1]
    infected = max(1, last['hiv_infections'])
    vals = [last.get('tested', 0) / infected * 100.0,
            last.get('diagnosed', 0) / infected * 100.0,
            last.get('on_art', 0) / infected * 100.0]
    labels = ['Tested', 'Diagnosed', 'On ART']
    colors = ['#ff7f0e', '#1f77b4', '#2ca02c']
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(labels, vals, color=colors, alpha=0.85)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 2, f"{v:.1f}%", ha='center')
    ax.set_ylim(0, 100)
    ax.set_title(f'Final-Year ART Cascade ({fy})', fontsize=16, weight='bold')
    ax.set_ylabel('Percentage of PLHIV')
    plt.tight_layout()
    base = os.path.join(output_dir, 'final_year_art_cascade')
    plt.rcParams['pdf.fonttype'] = 42; plt.rcParams['ps.fonttype'] = 42
    for fmt in formats:
        plt.savefig(f"{base}.{fmt}", dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved plot(s): {base} ({', '.join(formats)})")

def main():
    parser = argparse.ArgumentParser(description="Generate publication-ready plots from HIVEC-CM simulation results.")
    parser.add_argument("--results-file", default="results/simulation_results.csv")
    parser.add_argument("--output-dir", default="results/publication_plots")
    parser.add_argument("--formats", nargs='+', default=["png"], choices=["png", "pdf", "svg"], help="Output formats")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for raster outputs")
    parser.add_argument("--funding-cut-year", type=int, default=2025, help="Funding cut year for annotation")
    parser.add_argument("--funding-cut-magnitude", type=float, default=0.5, help="Funding cut magnitude for titles (e.g., 0.5 = 50%)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    df = pd.read_csv(args.results_file)

    # Calculate Incidence Rate (per 1,000 susceptible)
    df['incidence_rate'] = (df['new_infections'] / df['susceptible']) * 1000

    # Calculate Mortality Rate (per 1,000 population)
    df['mortality_rate'] = (df['deaths_hiv'] / df['total_population']) * 1000

    # --- Create Plots ---
    # 1. Prevalence
    # Attach funding cut year for annotation
    create_publication_plot._funding_cut_year = args.funding_cut_year
    title_suffix = f"With {int(args.funding_cut_magnitude*100)}% Funding Cut in {args.funding_cut_year}"
    prevalence_title = f"Projected HIV Prevalence in Cameroon (1985-2100)\n{title_suffix}"
    create_publication_plot(
        df['year'], df['hiv_prevalence'] * 100,
        prevalence_title,
        'Year', 'HIV Prevalence (%)',
        os.path.join(args.output_dir, 'hiv_prevalence'),
        '#d62728', # Red
        formats=tuple(args.formats), dpi=args.dpi
    )

    # 2. Incidence
    incidence_title = f"Projected HIV Incidence Rate in Cameroon (1985-2100)\n{title_suffix}"
    create_publication_plot(
        df['year'], df['incidence_rate'],
        incidence_title,
        'Year', 'Incidence Rate (per 1,000 Susceptible)',
        os.path.join(args.output_dir, 'hiv_incidence'),
        '#1f77b4', # Blue
        formats=tuple(args.formats), dpi=args.dpi
    )

    # 3. Mortality
    mortality_title = f"Projected HIV-Related Mortality Rate in Cameroon (1985-2100)\n{title_suffix}"
    create_publication_plot(
        df['year'], df['mortality_rate'],
        mortality_title,
        'Year', 'Mortality Rate (per 1,000 Population)',
        os.path.join(args.output_dir, 'hiv_mortality'),
        '#2ca02c', # Green
        formats=tuple(args.formats), dpi=args.dpi
    )

    # 4. Population composition (stacked area)
    create_population_composition_plot(df, args.output_dir, formats=tuple(args.formats), dpi=args.dpi)

    # 5. Final-year ART cascade
    create_cascade_final_year_plot(df, args.output_dir, formats=tuple(args.formats), dpi=args.dpi)

if __name__ == "__main__":
    main()
