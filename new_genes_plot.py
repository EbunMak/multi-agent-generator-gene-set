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
    new_genes = df["# New"].dropna()

    # Compute mean
    mean_val = new_genes.mean()

    # Prepare output dir relative to CSV file
    base_dir = os.path.dirname(csv_path)
    plot_dir = os.path.join(base_dir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    plt.figure(figsize=(10, 6))
    hist_color = "#b2df8a"
    kde_color = "#33a02c"

    # Histogram
    plt.hist(
        new_genes,
        bins=25,
        density=True,
        alpha=0.6,
        color=hist_color,
        edgecolor="black",
        label="Histogram"
    )

    # KDE
    kde = gaussian_kde(new_genes, bw_method=0.3)
    x_vals = np.linspace(new_genes.min(), new_genes.max(), 600)
    y_vals = kde(x_vals)
    plt.plot(
        x_vals,
        y_vals,
        linewidth=2.5,
        color=kde_color,
        label="Density Curve"
    )

    # Mean Line
    plt.axvline(
        mean_val,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Mean = {mean_val:.2f}"
    )

    # Labels + Title
    plt.title("Distribution of New Genes Added to Gene Sets",
              fontsize=18, fontweight="bold")
    plt.xlabel("New Genes Added", fontsize=16, fontweight="bold")
    plt.ylabel("Density", fontsize=16, fontweight="bold")
    plt.legend(fontsize=14, frameon=True)

    plt.grid(alpha=0.15)
    plt.tight_layout()

    #  Save Outputs
    base_name = os.path.join(plot_dir, "new_genes_distribution")

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
        "--comparison_csv",
        type=str,
        required=False,
        default="out/genesets/evaluation/gene_set_comparison.csv",
        help="Path to the gene set comparison CSV file."
    )

    args = parser.parse_args()
    make_plot(args.comparison_csv)
