import csv
import argparse
import os
import pandas as pd


def parse_gmt(file_path, remove_prefix=None):
    """
    Parse a GMT file into a dictionary:
    { gene_set_name: set(genes) }
    """
    gene_sets = {}
    with open(file_path, 'r') as file:
        for line in file:
            columns = line.strip().split("\t")
            gene_set_name = columns[0]
            genes = columns[2:]

            if remove_prefix and gene_set_name.startswith(remove_prefix):
                gene_set_name = gene_set_name[len(remove_prefix):]

            gene_sets[gene_set_name] = set(genes)
    return gene_sets


def compare_gene_sets(original, new):
    """
    Compare original and new gene set dictionaries.
    """
    result = []
    for gene_set_name in new:
        if gene_set_name in original:
            original_genes = original[gene_set_name]
            new_genes = new[gene_set_name]

            common_genes = original_genes.intersection(new_genes)
            new_added_genes = new_genes - original_genes
            lost_genes = original_genes - new_genes

            result.append([
                gene_set_name,
                ", ".join(sorted(common_genes)),
                ", ".join(sorted(new_added_genes)),
                ", ".join(sorted(lost_genes)),
                len(common_genes),
                len(new_added_genes),
                len(lost_genes),
                len(original_genes)
            ])
    return result


def export_to_csv(data, filename):
    """
    Export gene set comparison results to CSV.
    """
    header = [
        "Gene Set Name",
        "Common Genes",
        "Newly Added Genes",
        "Lost Genes",
        "# Common",
        "# New",
        "# Lost",
        "# Original"
    ]

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)


def compare_similarity(db1, db2, output_csv="gene_set_similarity.csv"):
    """
    Compute per-set and database-level similarity (Jaccard).
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
            similarity = (intersection / union) * 100 if union else 0

            results.append([name, len(genes1), len(genes2), intersection, union, round(similarity, 2)])

            if union > 0:
                per_set_similarities.append(intersection / union)
                total_intersections += intersection
                total_unions += union

    # Mean similarities
    unweighted_mean = (sum(per_set_similarities) / len(per_set_similarities) * 100
                       if per_set_similarities else 0)
    weighted_mean = ((total_intersections / total_unions) * 100
                     if total_unions > 0 else 0)

    # Database-level similarity
    total_intersection = len(all_genes_db1 & all_genes_db2)
    total_union = len(all_genes_db1 | all_genes_db2)
    total_similarity = (total_intersection / total_union) * 100 if total_union else 0

    # Write similarity CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Gene Set Name", "# Genes DB1", "# Genes DB2",
                         "# Common", "Union Size", "% Similarity"])
        writer.writerows(results)

    return {
        "total_similarity": total_similarity,
        "unweighted_mean": unweighted_mean,
        "weighted_mean": weighted_mean,
        "total_genes_original": len(all_genes_db1),
        "total_genes_new": len(all_genes_db2)
    }


def write_text_report(path, comparison_stats, similarity_stats):
    """
    Write all statistics to a .txt file.
    """
    with open(path, "w") as f:
        f.write("=== SUMMARY REPORT ===\n\n")

        f.write("=== SIMILARITY METRICS ===\n")
        f.write(f"Overall Database Similarity (% Jaccard): {similarity_stats['total_similarity']:.2f}%\n")
        f.write(f"Unweighted Mean Similarity: {similarity_stats['unweighted_mean']:.2f}%\n")
        f.write(f"Weighted Mean Similarity: {similarity_stats['weighted_mean']:.2f}%\n\n")

        f.write("=== GENE COUNTS ===\n")
        f.write(f"Unique genes in ORIGINAL DB: {similarity_stats['total_genes_original']}\n")
        f.write(f"Unique genes in NEW DB: {similarity_stats['total_genes_new']}\n\n")

        f.write("=== COMPARISON TABLE SUMMARY ===\n")
        f.write(f"Gene sets compared: {len(comparison_stats)}\n")



# main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two GMT files and generate comparison outputs.")
    parser.add_argument("--original_gmt", type=str, required=False,
                        default="out/genesets/phenotype_consensus_gene_sets.gmt")
    parser.add_argument("--new_gmt", type=str, required=False,
                        default="out/genesets/consensus_gene_sets.gmt")

    args = parser.parse_args()

    original_gmt_file = args.original_gmt
    new_gmt_file = args.new_gmt

    # Output directory = same directory as new GMT
    out_dir = os.path.join(os.path.dirname(new_gmt_file), "evaluation")
    os.makedirs(out_dir, exist_ok=True)

    # Output paths
    comparison_csv = os.path.join(out_dir, "gene_set_comparison.csv")
    similarity_csv = os.path.join(out_dir, "gene_set_similarity.csv")
    text_report = os.path.join(out_dir, "gene_analysis.txt")

    # Load GMTs
    original_gene_set = parse_gmt(original_gmt_file)
    new_gene_set = parse_gmt(new_gmt_file)

    # Compare gene sets
    comparison_result = compare_gene_sets(original_gene_set, new_gene_set)
    export_to_csv(comparison_result, filename=comparison_csv)

    # Calculate similarity
    similarity_stats = compare_similarity(original_gene_set, new_gene_set, output_csv=similarity_csv)

    # Write final text analysis
    write_text_report(text_report, comparison_result, similarity_stats)

    print(f"\nSaved outputs to: {out_dir}")
    print(f"- {comparison_csv}")
    print(f"- {similarity_csv}")
    print(f"- {text_report}")
