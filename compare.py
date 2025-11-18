import csv

def parse_gmt(file_path, remove_prefix=None):
    """
    Parse a GMT file into a dictionary:
    { gene_set_name: set(genes) }
    Optionally remove a prefix from gene set names.
    """
    gene_sets = {}
    with open(file_path, 'r') as file:
        for line in file:
            columns = line.strip().split("\t")
            gene_set_name = columns[0]
            genes = columns[2:]

            # Remove prefix if specified
            if remove_prefix and gene_set_name.startswith(remove_prefix):
                gene_set_name = gene_set_name[len(remove_prefix):]

            gene_sets[gene_set_name] = set(genes)
    return gene_sets


def compare_gene_sets(original, new):
    """
    Compare original and new gene set dictionaries.
    Returns a list of:
    [Gene Set Name, Common Genes, New Genes, Lost Genes, # Common, # New, # Lost, # Original]
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


def export_to_csv(data, filename="gene_set_comparison_sample.csv"):
    """
    Export the comparison results to a CSV file.
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

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)

    print(f"✅ CSV file created: {filename}")


# === MAIN EXECUTION ===
if __name__ == "__main__":
    original_gmt_file = 'phenotype_consensus_gene_sets.gmt'  # Original
    new_gmt_file = 'consensus_gene_sets.gmt'                 # Curated

    prefix_to_remove = 'HALLMARK_'  # Adjust or remove if not needed

    # Parse GMTs
    original_gene_set = parse_gmt(original_gmt_file, remove_prefix=prefix_to_remove)
    new_gene_set = parse_gmt(new_gmt_file)

    # Compare
    comparison_result = compare_gene_sets(original_gene_set, new_gene_set)

    # Export CSV
    export_to_csv(comparison_result, filename="gene_set_comparison_sample_437.csv")
    print("📊 CSV file saved as: gene_set_comparison_sample_437.csv")
