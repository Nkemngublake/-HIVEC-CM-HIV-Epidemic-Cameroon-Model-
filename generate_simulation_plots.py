
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

# Add the src directory to the Python path to find hivec_cm
sys.path.append(os.path.abspath('src'))

from hivec_cm.models.model import EnhancedHIVModel
from hivec_cm.models.parameters import load_parameters

def generate_simulation_plots():
    """
    Runs the HIV model and generates a series of plots visualizing the epidemic over time.
    """
    output_dir = "simulation_frames"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Saving plot frames to '{output_dir}/'")

    # 1. Initialize and run the model
    # Using a smaller population and 1-year timestep for faster generation of frames
    params = load_parameters('config/parameters.json')
    params.initial_population = 50000
    model = EnhancedHIVModel(params, start_year=1990)
    results_df = model.run_simulation(years=60, dt=1.0)

    # 2. Create plots for each year
    for index, row in results_df.iterrows():
        year = int(row['year'])
        print(f"Generating frame for year {year}...")

        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'HIV Epidemic Simulation - Cameroon: Year {year}', fontsize=20, weight='bold')
        fig.patch.set_facecolor('white')


        # --- Plot 1: HIV Prevalence ---
        axs[0, 0].plot(results_df['year'][:index+1], results_df['hiv_prevalence'][:index+1] * 100, 'r-', linewidth=2.5)
        axs[0, 0].set_title('HIV Prevalence', fontsize=14)
        axs[0, 0].set_xlabel('Year', fontsize=12)
        axs[0, 0].set_ylabel('Prevalence (%)', fontsize=12)
        axs[0, 0].set_xlim([1990, 2050])
        axs[0, 0].set_ylim([0, results_df['hiv_prevalence'].max() * 100 * 1.1])
        axs[0, 0].grid(True, linestyle='--', alpha=0.6)

        # --- Plot 2: ART Coverage ---
        axs[0, 1].plot(results_df['year'][:index+1], results_df['art_coverage'][:index+1] * 100, 'b-', linewidth=2.5)
        axs[0, 1].set_title('ART Coverage Among Infected', fontsize=14)
        axs[0, 1].set_xlabel('Year', fontsize=12)
        axs[0, 1].set_ylabel('Coverage (%)', fontsize=12)
        axs[0, 1].set_xlim([1990, 2050])
        axs[0, 1].set_ylim([0, 100])
        axs[0, 1].grid(True, linestyle='--', alpha=0.6)

        # --- Plot 3: Total Population ---
        axs[1, 0].plot(results_df['year'][:index+1], results_df['total_population'][:index+1], 'g-', linewidth=2.5)
        axs[1, 0].set_title('Total Population', fontsize=14)
        axs[1, 0].set_xlabel('Year', fontsize=12)
        axs[1, 0].set_ylabel('Population Count', fontsize=12)
        axs[1, 0].set_xlim([1990, 2050])
        axs[1, 0].set_ylim([results_df['total_population'].min() * 0.9, results_df['total_population'].max() * 1.1])
        axs[1, 0].grid(True, linestyle='--', alpha=0.6)

        # --- Plot 4: New Infections ---
        axs[1, 1].plot(results_df['year'][:index+1], results_df['new_infections'][:index+1], 'm-', linewidth=2.5)
        axs[1, 1].set_title('Annual New HIV Infections', fontsize=14)
        axs[1, 1].set_xlabel('Year', fontsize=12)
        axs[1, 1].set_ylabel('Number of Infections', fontsize=12)
        axs[1, 1].set_xlim([1990, 2050])
        axs[1, 1].set_ylim([0, results_df['new_infections'].max() * 1.1])
        axs[1, 1].grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        frame_path = os.path.join(output_dir, f"frame_{year}.png")
        plt.savefig(frame_path, dpi=100, facecolor=fig.get_facecolor())
        plt.close(fig)

    print("\n" + "="*50)
    print(f"Successfully generated {len(results_df)} plot frames in the '{output_dir}' directory.")
    print("You can now use a tool like FFmpeg to combine these frames into a video.")
    print("\nTo create a video from these frames, run the following command in your terminal:")
    print(f"ffmpeg -framerate 10 -i {output_dir}/frame_%d.png -c:v libx264 -r 30 -pix_fmt yuv420p hiv_simulation.mp4")
    print("="*50)

if __name__ == "__main__":
    generate_simulation_plots()
