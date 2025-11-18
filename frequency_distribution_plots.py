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
df = pd.read_csv("gene_set_similarity.csv")
similarity = df["% Similarity"].dropna()

# Compute mean
mean_val = similarity.mean()

# Create figure
plt.figure(figsize=(10,6))

# Histogram (pastel blue)
counts, bins, patches = plt.hist(
    similarity,
    bins=20,
    density=True,
    alpha=0.6,
    color="#aec7e8",          # light pastel blue
    edgecolor="black",
    label="Histogram"
)

# KDE curve
kde = gaussian_kde(similarity)
x_vals = np.linspace(similarity.min(), similarity.max(), 500)
y_vals = kde(x_vals)
plt.plot(
    x_vals, y_vals,
    linewidth=2.5,
    color="#1f77b4",
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

# Labels (bold)
plt.title("Distribution of % Similarity Across Gene Sets", fontsize=18, fontweight="bold")
plt.xlabel("% Similarity", fontsize=16, fontweight="bold")
plt.ylabel("Density", fontsize=16, fontweight="bold")

# X-axis increments by 10
xmin, xmax = similarity.min(), similarity.max()
plt.xticks(np.arange(int(xmin), int(xmax)+1, 10))

# Legend styling
plt.legend(fontsize=14, frameon=True)

plt.tight_layout()

# Save high-quality versions
plt.savefig("similarity_distribution.png", dpi=400)
plt.savefig("similarity_distribution.svg")
plt.savefig("similarity_distribution.pdf")

plt.show()
