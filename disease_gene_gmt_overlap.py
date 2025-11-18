import pandas as pd
import json
import mygene
import matplotlib.pyplot as plt
from collections import defaultdict


# --------------------------------------------------
#    ID MAPPING FUNCTION
# --------------------------------------------------
def id_mapping(genes, mode='entrezgene'):
    mg = mygene.MyGeneInfo()
    
    if mode == 'entrezgene':
        out = mg.querymany(
            genes,
            scopes='symbol,reporter,accession,entrezgene',
            fields='entrezgene',
            species='human'
        )
    else:  # symbol mapping
        out = mg.querymany(
            genes,
            scopes='symbol,reporter,accession,entrezgene',
            fields='symbol',
            species='human'
        )

    mapped_genes = []
    valid_genes = []
    invalid_genes = []

    for gene_info in out:
        if "notfound" in gene_info:
            invalid_genes.append(gene_info["query"])
        else:
            valid_genes.append(gene_info["query"])
            if mode in gene_info:
                mapped_genes.append(gene_info[mode])

    return mapped_genes, valid_genes, invalid_genes



# --------------------------------------------------
#    GMT PARSER
# --------------------------------------------------
def parse_gmt(gmt_path):
    gmt_dict = {}
    with open(gmt_path, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            gs_name = parts[0]
            genes = set(parts[2:])
            gmt_dict[gs_name] = genes
    return gmt_dict



# --------------------------------------------------
#    LOAD INPUTS
# --------------------------------------------------
with open("disease_gene_map.json", "r") as f:
    disease_dict = json.load(f)

gmt_a_path = "consensus_gene_sets.gmt"
gmt_b_path = "phenotype_consensus_gene_sets_400.gmt"

gmt_A = parse_gmt(gmt_a_path)
gmt_B = parse_gmt(gmt_b_path)

print("Loaded gene sets:", len(gmt_A), "gene sets.")



# --------------------------------------------------
#   CONVERT DISEASE GENES → ENTREZ
# --------------------------------------------------
print("\nConverting disease genes to Entrez IDs...")

for disease, info in disease_dict.items():
    gene_symbols = list(info["genes"])

    entrez, valid, invalid = id_mapping(gene_symbols, mode='entrezgene')

    disease_dict[disease]["genes_entrez"] = set(str(x) for x in entrez)
    disease_dict[disease]["genes_invalid"] = invalid

    # use entrez as main gene set
    disease_dict[disease]["genes"] = disease_dict[disease]["genes_entrez"]

print("✓ Entrez conversion complete.")



# --------------------------------------------------
#   MATCH AGAINST BOTH GMTs
# --------------------------------------------------
records = []

for disease, info in disease_dict.items():
    disease_group = info["disease_group"]
    disease_genes = set(info["genes"])

    for gs_name in gmt_A.keys():  # same keys in both GMTs
        genes_A = gmt_A[gs_name]
        genes_B = gmt_B[gs_name]

        overlap_A = disease_genes.intersection(genes_A)
        overlap_B = disease_genes.intersection(genes_B)

        records.append({
            "Disease": disease,
            "DiseaseGroup": disease_group,
            "GeneSet": gs_name,
            "NumGenes_GMT_A": len(overlap_A),
            "NumGenes_GMT_B": len(overlap_B),
            "Genes_GMT_A": ",".join(sorted(overlap_A)),
            "Genes_GMT_B": ",".join(sorted(overlap_B)),
        })


results_df = pd.DataFrame(records)
results_df.to_csv("disease_gene_gmt_overlap_entrez.csv", index=False)

print("Saved: disease_gene_gmt_overlap_entrez.csv")



# --------------------------------------------------
#   SINGLE VISUALIZATION (ALL DISEASES)
# --------------------------------------------------

print("\nGenerating single comparison visualization...")

# Sum total genes matched across ALL gene sets + ALL diseases
total_A = results_df["NumGenes_GMT_A"].sum()
total_B = results_df["NumGenes_GMT_B"].sum()

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["GMT A", "GMT B"], [total_A, total_B])

ax.set_title("Total Disease Gene Representation in GMT A vs GMT B (Entrez IDs)")
ax.set_ylabel("Total Matched Disease Genes")
ax.set_xlabel("GMT Source")

plt.tight_layout()
plt.savefig("TOTAL_GMT_REPRESENTATION.png")
plt.close()

print("✓ Saved: TOTAL_GMT_REPRESENTATION.png")
