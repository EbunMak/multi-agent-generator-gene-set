import argparse
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.size": 14
})


def make_plot(csv_path):

    # Load data
    df = pd.read_csv(csv_path)
    similarity = df["% Similarity"].dropna()

    # Compute mean
    mean_val = similarity.mean()

    # Output folder = same directory as CSV
    base_dir = os.path.dirname(csv_path)
    plot_dir = os.path.join(base_dir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    # Create figure
    plt.figure(figsize=(10, 6))

    # Histogram (light pastel blue)
    hist_color = "#aec7e8"
    kde_color = "#1f77b4"

    plt.hist(
        similarity,
        bins=20,
        density=True,
        alpha=0.6,
        color=hist_color,
        edgecolor="black",
        label="Histogram"
    )

    # KDE
    kde = gaussian_kde(similarity)
    x_vals = np.linspace(similarity.min(), similarity.max(), 500)
    y_vals = kde(x_vals)

    plt.plot(
        x_vals, y_vals,
        linewidth=2.5,
        color=kde_color,
        label="Density Curve"
    )

    # Mean line
    plt.axvline(
        mean_val,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Mean = {mean_val:.2f}%"
    )

    
    plt.title("Distribution of % Similarity Across Gene Sets",
              fontsize=18, fontweight="bold")

    plt.xlabel("% Similarity", fontsize=16, fontweight="bold")
    plt.ylabel("Density", fontsize=16, fontweight="bold")

    
    xmin, xmax = similarity.min(), similarity.max()
    plt.xticks(np.arange(int(xmin), int(xmax)+1, 10))

    # Legend
    plt.legend(fontsize=14, frameon=True)

    plt.tight_layout()

    base_name = os.path.join(plot_dir, "similarity_distribution")

    plt.savefig(f"{base_name}.png", dpi=400)
    plt.savefig(f"{base_name}.pdf")
    plt.savefig(f"{base_name}.svg")

    print("\nSaved plots:")
    print(f" - {base_name}.png")
    print(f" - {base_name}.pdf")
    print(f" - {base_name}.svg\n")

    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--similarity_csv",
        type=str,
        required=False,
        default="out/genesets/evaluation/gene_set_similarity.csv",
        help="Path to gene set similarity CSV file."
    )

    args = parser.parse_args()
    make_plot(args.similarity_csv)
