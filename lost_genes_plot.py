import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

# Reset to default font settings (no LaTeX)
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.size": 14
})

# Load data
df = pd.read_csv("gene_set_comparison_sample_437.csv")

# Compute % Loss
df["% Loss"] = (df["# Lost"] / df["# Original"]) * 100
percent_loss = df["% Loss"].dropna()

# Compute mean
mean_val = percent_loss.mean()

# Create figure
plt.figure(figsize=(10,6))

# Histogram (pastel orange)
counts, bins, patches = plt.hist(
    percent_loss,
    bins=25,
    density=True,
    alpha=0.6,
    color="#fdbf6f",      # pastel orange
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
    color="#e66101",       # darker orange
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

# Labels + title (bold)
plt.title("Distribution of % Loss Across Gene Sets", fontsize=18, fontweight="bold")
plt.xlabel("% Loss", fontsize=16, fontweight="bold")
plt.ylabel("Density", fontsize=16, fontweight="bold")

# Legend styling
plt.legend(fontsize=14, frameon=True)

# Grid + layout
plt.grid(alpha=0.15)
plt.tight_layout()

# Save high-resolution outputs
plt.savefig("percent_loss_distribution.png", dpi=400)
plt.savefig("percent_loss_distribution.svg")
plt.savefig("percent_loss_distribution.pdf")

plt.show()
