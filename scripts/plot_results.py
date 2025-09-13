
import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse

def plot_simulation_results(results_file, output_dir):
    """
    Loads simulation results and generates a dashboard of plots.
    """
    print(f"Loading results from {results_file}...")
    try:
        df = pd.read_csv(results_file)
    except FileNotFoundError:
        print(f"Error: The file {results_file} was not found.")
        return

    print("Generating plots...")
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('HIVEC-CM Simulation Results Dashboard', fontsize=20, weight='bold')
    fig.patch.set_facecolor('white')

    # --- Plot 1: HIV Prevalence ---
    axs[0, 0].plot(df['year'], df['hiv_prevalence'] * 100, 'r-', linewidth=2, label='HIV Prevalence')
    axs[0, 0].set_title('HIV Prevalence Over Time', fontsize=14)
    axs[0, 0].set_xlabel('Year', fontsize=12)
    axs[0, 0].set_ylabel('Prevalence (%)', fontsize=12)
    axs[0, 0].grid(True, linestyle='--', alpha=0.6)
    axs[0, 0].legend()

    # --- Plot 2: ART Coverage ---
    axs[0, 1].plot(df['year'], df['art_coverage'] * 100, 'b-', linewidth=2, label='ART Coverage')
    axs[0, 1].set_title('ART Coverage Among Infected Population', fontsize=14)
    axs[0, 1].set_xlabel('Year', fontsize=12)
    axs[0, 1].set_ylabel('Coverage (%)', fontsize=12)
    axs[0, 1].grid(True, linestyle='--', alpha=0.6)
    axs[0, 1].legend()

    # --- Plot 3: Population Dynamics ---
    axs[1, 0].plot(df['year'], df['total_population'], 'g-', linewidth=2, label='Total Population')
    axs[1, 0].plot(df['year'], df['hiv_infections'], 'm-', linewidth=2, label='HIV Infections')
    axs[1, 0].set_title('Population Dynamics', fontsize=14)
    axs[1, 0].set_xlabel('Year', fontsize=12)
    axs[1, 0].set_ylabel('Number of Individuals', fontsize=12)
    axs[1, 0].grid(True, linestyle='--', alpha=0.6)
    axs[1, 0].legend()

    # --- Plot 4: New Infections ---
    axs[1, 1].plot(df['year'], df['new_infections'], 'k-', linewidth=2, label='New Infections')
    axs[1, 1].set_title('Annual New HIV Infections', fontsize=14)
    axs[1, 1].set_xlabel('Year', fontsize=12)
    axs[1, 1].set_ylabel('Number of New Infections', fontsize=12)
    axs[1, 1].grid(True, linestyle='--', alpha=0.6)
    axs[1, 1].legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save the figure in the requested output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "simulation_dashboard.png")
    plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor())
    print(f"Successfully saved dashboard to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Plot simulation results from the HIVEC-CM model.")
    parser.add_argument(
        "--results-file",
        default="results/simulation_results.csv",
        help="Path to the simulation results CSV file."
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save the plot dashboard."
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    plot_simulation_results(args.results_file, args.output_dir)

if __name__ == "__main__":
    main()
