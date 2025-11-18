import json
from collections import defaultdict
from utils import id_mapping

def txt_to_gmt(input_file, output_file):
    gene_sets = defaultdict(set)

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                gene_set, json_data = line.strip().split('\t', 1)
                gene_info = json.loads(json_data)
                if gene_info.get("Validation", "").lower() == "yes":
                    gene = gene_info.get("Gene")
                    if gene:
                        normalized_set = gene_set.strip().upper().replace(" ", "_")
                        gene_sets[normalized_set].add(gene)
            except Exception as e:
                print(f"Skipping line due to error: {e}\n{line}")

    with open(output_file, 'w', encoding='utf-8') as f:
        for gene_set, genes in gene_sets.items():
            entrez_genes, _, _ = id_mapping(genes)
            f.write(f"{gene_set}\tNA\t" + "\t".join(sorted(entrez_genes)) + "\n")

txt_to_gmt("kegg_2.txt", "new_verified_kegg_2.gmt")
