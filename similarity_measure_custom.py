import csv

def parse_gmt(file_path):
    """
    Parse a GMT file into a dictionary: { gene_set_name: set(genes) }
    """
    gene_sets = {}
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            name = parts[0]
            genes = set(parts[2:])
            gene_sets[name] = genes
    return gene_sets


def compare_similarity(db1, db2, output_csv="gene_set_similarity.csv"):
    """
    Compare two gene set databases (same structure) and compute:
    - % similarity per gene set (Jaccard index)
    - weighted & unweighted mean similarity across sets
    - total database-level similarity
    """
    results = []
    all_genes_db1 = set()
    all_genes_db2 = set()

    per_set_similarities = []
    total_intersections = 0
    total_unions = 0

    for name in db1:
        if name in db2:
            genes1, genes2 = db1[name], db2[name]
            all_genes_db1.update(genes1)
            all_genes_db2.update(genes2)

            intersection = len(genes1 & genes2)
            union = len(genes1 | genes2)

            similarity = (intersection / union) * 100 if union > 0 else 0
            results.append([name, len(genes1), len(genes2), intersection, union, round(similarity, 2)])

            # Accumulate for weighted/unweighted averages
            if union > 0:
                per_set_similarities.append(intersection / union)
                total_intersections += intersection
                total_unions += union

    # --- Compute mean similarities ---
    unweighted_mean = sum(per_set_similarities) / len(per_set_similarities) * 100 if per_set_similarities else 0
    weighted_mean = (total_intersections / total_unions) * 100 if total_unions > 0 else 0

    # --- Compute total similarity across entire database ---
    total_intersection = len(all_genes_db1 & all_genes_db2)
    total_union = len(all_genes_db1 | all_genes_db2)
    total_similarity = (total_intersection / total_union) * 100 if total_union > 0 else 0

    # --- Save per-gene-set results ---
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Gene Set Name", "# Genes DB1", "# Genes DB2", "# Common", "Union Size", "% Similarity"])
        writer.writerows(results)

    print(f"✅ Saved similarity report to {output_csv}")

    # --- Print summary statistics ---
    print("\n=== DATABASE-LEVEL SIMILARITY ===")
    print(f"Total unique genes in DB1: {len(all_genes_db1)}")
    print(f"Total unique genes in DB2: {len(all_genes_db2)}")
    print(f"Shared genes across databases: {total_intersection}")
    print(f"Union of all genes: {total_union}")
    print(f"🔹 Overall Database Similarity: {round(total_similarity, 2)}%")

    print("\n=== MEAN SIMILARITY ACROSS SETS ===")
    print(f"Unweighted Mean (simple average): {round(unweighted_mean, 2)}%")
    print(f"Weighted Mean (by union size): {round(weighted_mean, 2)}%")

    return {
        "total_similarity": total_similarity,
        "unweighted_mean": unweighted_mean,
        "weighted_mean": weighted_mean
    }


# Example usage
if __name__ == "__main__":
    db1 = parse_gmt("phenotype_consensus_gene_sets.gmt")   # Original
    db2 = parse_gmt("consensus_gene_sets.gmt")             # New

    stats = compare_similarity(db1, db2)
