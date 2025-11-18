import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

# Reset to default fonts (no LaTeX)
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.size": 14
})

# Load data
df = pd.read_csv("gene_set_comparison_sample_437.csv")
new_genes = df["# New"].dropna()

# Compute mean
mean_val = new_genes.mean()

# Create figure
plt.figure(figsize=(10,6))

# Histogram (pastel green)
hist_color = "#b2df8a"       # pastel green (light)
kde_color  = "#33a02c"       # darker green to match (visible)

counts, bins, patches = plt.hist(
    new_genes,
    bins=25,
    density=True,
    alpha=0.6,
    color=hist_color,
    edgecolor="black",
    label="Histogram"
)

# KDE (smooth density curve in darker green)
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

# Mean line
plt.axvline(
    mean_val,
    color="red",
    linestyle="--",
    linewidth=2,
    label=f"Mean = {mean_val:.2f}"
)

# Labels + Title (bold)
plt.title("Distribution of New Genes Added to Gene Sets", fontsize=18, fontweight="bold")
plt.xlabel("New Genes Added", fontsize=16, fontweight="bold")
plt.ylabel("Density", fontsize=16, fontweight="bold")

# Legend styling
plt.legend(fontsize=14, frameon=True)

# Grid + layout
plt.grid(alpha=0.15)
plt.tight_layout()

# Save high-resolution outputs
plt.savefig("new_genes_distribution_clean.png", dpi=400)
plt.savefig("new_genes_distribution_clean.svg")
plt.savefig("new_genes_distribution_clean.pdf")

plt.show()
