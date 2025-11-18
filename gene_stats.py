import pandas as pd

# Load comparison table
df = pd.read_csv("gene_set_comparison_sample_437.csv")

# Ensure numerical columns exist and are of correct type
for col in ["# Common", "# New", "# Original"]:
    if col not in df.columns:
        df[col] = 0
df[["# Common", "# New", "# Original"]] = df[["# Common", "# New", "# Original"]].fillna(0).astype(int)

# Compute # of genes in original but missing in new
df["# Lost"] = df["# Original"] - df["# Common"]

print("\n=== BASIC DATA ===")
print(f"Total gene sets compared: {len(df)}")

print("\n=== OVERLAP STATISTICS (# COMMON GENES) ===")
print(df["# Common"].describe())

print("\nGene sets with NO common genes:")
print(df[df["# Common"] == 0]["Gene Set Name"].tolist())

print("\nGene sets with HIGH overlap (top 10):")
print(df.sort_values("# Common", ascending=False)[["Gene Set Name", "# Common"]].head(10))

print("\n=== NEW GENE STATISTICS (# NEW GENES) ===")
print(df["# New"].describe())

print("\nGene sets with NO new genes added (fully consistent):")
print(df[df["# New"] == 0]["Gene Set Name"].tolist())

print("\nGene sets with MANY new genes added (top 10):")
print(df.sort_values("# New", ascending=False)[["Gene Set Name", "# New"]].head(10))

print("\n=== LOSS STATISTICS (# ORIGINAL GENES NOT IN NEW) ===")
print(df["# Lost"].describe())

print("\nGene sets that lost ALL original genes:")
print(df[df["# Lost"] == df["# Original"]]["Gene Set Name"].tolist())

print("\nGene sets that retained MOST original genes (lowest loss, top 10):")
print(df.sort_values("# Lost", ascending=True)[["Gene Set Name", "# Lost"]].head(10))


# --------------------------------------------------------
# ✅ GLOBAL DATABASE-LEVEL STATISTICS (FIXED)
# --------------------------------------------------------

# Helper to parse comma-separated genes into a set
def parse_gene_list(col):
    if isinstance(col, str) and col.strip():
        return set(g.strip() for g in col.split(",") if g.strip())
    return set()

# Parse existing columns
df["Common Set"] = df["Common Genes"].apply(parse_gene_list)
df["Lost Set"] = df["Lost Genes"].apply(parse_gene_list)

# If the CSV has original genes explicitly:
if "Original Genes" in df.columns:
    df["Original Set"] = df["Original Genes"].apply(parse_gene_list)
else:
    # Build "Original Set" from:  Original = Common ∪ Lost
    df["Original Set"] = df.apply(
        lambda row: row["Common Set"].union(row["Lost Set"]),
        axis=1
    )


# New Set = Common + Newly Added
df["New Set"] = df.apply(
    lambda row: row["Common Set"].union(parse_gene_list(row["Newly Added Genes"])),
    axis=1
)

# Global database unions
global_original = set().union(*df["Original Set"].tolist())
global_new = set().union(*df["New Set"].tolist())

# Compute global losses and gains
global_lost = global_original - global_new
global_gained = global_new - global_original

print("\n=== GLOBAL DATABASE-LEVEL GENE DIFFERENCES ===")
print(f"Total unique genes in ORIGINAL DB: {len(global_original)}")
print(f"Total unique genes in NEW DB: {len(global_new)}")
print(f"Genes LOST from original DB: {len(global_lost)}")
print(f"Genes GAINED in new DB: {len(global_gained)}")

# Save lists
pd.DataFrame({"Genes Lost": list(global_lost)}).to_csv("genes_lost_globally.csv", index=False)
pd.DataFrame({"Genes Gained": list(global_gained)}).to_csv("genes_gained_globally.csv", index=False)

print("\n📁 Saved global lost/gained genes to:")
print("    • genes_lost_globally.csv")
print("    • genes_gained_globally.csv")
