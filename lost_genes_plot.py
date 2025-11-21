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

    # Compute % Loss
    df["% Loss"] = (df["# Lost"] / df["# Original"]) * 100
    percent_loss = df["% Loss"].dropna()

    # Compute mean
    mean_val = percent_loss.mean()

    # Output directory based on CSV location
    base_dir = os.path.dirname(csv_path)
    plot_dir = os.path.join(base_dir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    # Create figure
    plt.figure(figsize=(10, 6))

    # Histogram (pastel orange)
    hist_color = "#fdbf6f"
    kde_color = "#e66101"

    plt.hist(
        percent_loss,
        bins=25,
        density=True,
        alpha=0.6,
        color=hist_color,
        edgecolor="black",
        label="Histogram"
    )

    # KDE (smooth density curve)
    kde = gaussian_kde(percent_loss, bw_method=0.3)
    x_vals = np.linspace(percent_loss.min(), percent_loss.max(), 600)
    y_vals = kde(x_vals)

    plt.plot(
        x_vals,
        y_vals,
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

    # Labels + Title
    plt.title("Distribution of % Loss Across Gene Sets",
              fontsize=18, fontweight="bold")
    plt.xlabel("% Loss", fontsize=16, fontweight="bold")
    plt.ylabel("Density", fontsize=16, fontweight="bold")
    plt.legend(fontsize=14, frameon=True)

    plt.grid(alpha=0.15)
    plt.tight_layout()

    #Save outputs
    base_name = os.path.join(plot_dir, "percent_loss_distribution")

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
        help="Path to gene set comparison CSV file."
    )

    args = parser.parse_args()
    make_plot(args.comparison_csv)
