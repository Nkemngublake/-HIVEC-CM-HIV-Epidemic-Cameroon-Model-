#!/usr/bin/env python3
"""
Generate a compact PDF report from a study directory.
Includes key plots and a summary panel with selected labels.
"""

import argparse
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg


def add_image_page(pdf, image_path, title=None):
    if not os.path.exists(image_path):
        return False
    fig = plt.figure(figsize=(11.0, 8.5))
    ax = fig.add_axes([0.05, 0.1, 0.9, 0.8])
    img = mpimg.imread(image_path)
    ax.imshow(img)
    ax.axis('off')
    if title:
        fig.suptitle(title, fontsize=14)
    pdf.savefig(fig)
    plt.close(fig)
    return True


def add_summary_page(pdf, labels_json_path):
    fig = plt.figure(figsize=(11.0, 8.5))
    ax = fig.add_axes([0.05, 0.1, 0.9, 0.8])
    ax.axis('off')
    lines = ["HIVEC-CM Monte Carlo Study: Key Labels"]
    if os.path.exists(labels_json_path):
        with open(labels_json_path) as f:
            labels = json.load(f)
        for k in sorted(labels.keys()):
            lines.append(f"{k}: {labels[k]}")
    else:
        lines.append("(labels.json not found)")
    text = "\n".join(lines)
    ax.text(0.01, 0.99, text, va='top', ha='left', fontsize=10, family='monospace')
    pdf.savefig(fig)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description="Generate compact report PDF from study directory")
    p.add_argument("--study-dir", required=True)
    p.add_argument("--output-file", default=None)
    args = p.parse_args()

    plots_dir = os.path.join(args.study_dir, 'plots')
    analysis_dir = os.path.join(args.study_dir, 'analysis')
    out = args.output_file or os.path.join(args.study_dir, 'report.pdf')

    candidates = [
        'executive_summary.png',
        'comprehensive_time_series.png',
        'prevalence_pct_trajectory_comparison.png',
        'prevalence_pct_difference_trajectory.png',
        'prevalence_pct_ratio_trajectory.png',
        'incidence_per_1000_trajectory_comparison.png',
        'incidence_per_1000_difference_trajectory.png',
        'incidence_per_1000_ratio_trajectory.png',
        'hiv_mortality_per_1000_trajectory_comparison.png',
        'hiv_mortality_per_1000_difference_trajectory.png',
        'hiv_mortality_per_1000_ratio_trajectory.png',
        'final_year_*_comparison.png',
        'cumulative_impacts_comparison.png',
        'art_cascade_trajectories.png',
    ]

    # Expand wildcards
    import glob
    files = []
    for pat in candidates:
        files.extend(sorted(glob.glob(os.path.join(plots_dir, pat))))

    with PdfPages(out) as pdf:
        # Summary labels first
        add_summary_page(pdf, os.path.join(analysis_dir, 'labels.json'))
        # Add images
        for f in files:
            add_image_page(pdf, f, title=os.path.basename(f))

    print(f"Saved report: {out}")


if __name__ == '__main__':
    main()

