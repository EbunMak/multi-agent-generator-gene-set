import os
import json
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.backends.backend_pdf import PdfPages
from utils import id_mapping

def load_gmt(filepath):
    """Load a GMT file into a dict: {gene_set_name: set(genes)}"""
    gene_sets = {}
    with open(filepath) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) > 2:
                gene_sets[parts[0]] = set(parts[2:])
    return gene_sets

def compare_gmts(qwen_path, deepseek_path, llama3_path, output_pdf="gene_set_bar_summary.pdf"):
    # Load GMTs
    qwen = load_gmt(qwen_path)
    deepseek = load_gmt(deepseek_path)
    llama3 = load_gmt(llama3_path)

    # Gene set names
    q_sets = set(qwen.keys())
    d_sets = set(deepseek.keys())
    l_sets = set(llama3.keys())

    # Overlaps
    all_three = q_sets & d_sets & l_sets
    qd = (q_sets & d_sets) - all_three
    ql = (q_sets & l_sets) - all_three
    dl = (d_sets & l_sets) - all_three
    q_only = q_sets - (d_sets | l_sets)
    d_only = d_sets - (q_sets | l_sets)
    l_only = l_sets - (q_sets | d_sets)

    # ✅ New: Union of all gene sets
    union_all = q_sets | d_sets | l_sets

    # Prepare data
    categories = [
        "Qwen Only", "DeepSeek Only", "Llama3 Only",
        "Qwen & DeepSeek", "Qwen & Llama3", "DeepSeek & Llama3",
        "All Three", "Union (All Sets)"
    ]

    counts = [
        len(q_only), len(d_only), len(l_only),
        len(qd), len(ql), len(dl),
        len(all_three), len(union_all)
    ]

    # Save summary JSON
    summary = dict(zip(categories, counts))
    with open(output_pdf.replace(".pdf", "_summary.json"), "w") as f:
        json.dump(summary, f, indent=4)

    # --- Improved Bar Chart ---
    with PdfPages(output_pdf) as pdf:
        plt.figure(figsize=(11, 6))
        bars = plt.bar(categories, counts,
                       color=["#5DA5DA", "#F17CB0", "#60BD68", "#B276B2", "#FF9DA7", "#B2912F", "#4E79A7", "#7F7F7F"])

        plt.xticks(rotation=35, ha="right", fontsize=10)
        plt.ylabel("Number of Gene Sets", fontsize=12)
        plt.title("Gene Set Overlap Across Qwen, DeepSeek, and Llama3", fontsize=15)

        # Label counts above bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, height + 1,
                     str(int(height)), ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.tight_layout()
        pdf.savefig()
        plt.close()

    print(f"✅ PDF saved to: {output_pdf}")
    print(f"✅ Summary saved to: {output_pdf.replace('.pdf', '_summary.json')}")
    return summary

def make_consensus_gmt(qwen_file, deepseek_file, llama_file, out_gmt="consensus_gene_sets.gmt"):
    qwen = load_gmt(qwen_file)
    deepseek = load_gmt(deepseek_file)
    llama = load_gmt(llama_file)

    q_sets = set(qwen.keys())
    d_sets = set(deepseek.keys())
    l_sets = set(llama.keys())

    # gene sets appearing in at least 2 models
    shared_pairs = ( d_sets & q_sets ) | (l_sets & q_sets) | (l_sets & d_sets)

    with open(out_gmt, "w") as out:
        for gs in sorted(shared_pairs):
            # Collect genes present in each model for this gene set
            g_q = qwen.get(gs, set())
            g_d = deepseek.get(gs, set())
            g_l = llama.get(gs, set())

            # Count appearances of each gene across models (max 3)
            gene_counts = defaultdict(int)
            for g in g_q: gene_counts[g] += 1
            for g in g_d: gene_counts[g] += 1
            for g in g_l: gene_counts[g] += 1

            # Keep genes appearing in at least 2 models
            consensus_genes = [g for g, count in gene_counts.items() if count >= 2]

            # Only write if consensus has genes
            if consensus_genes:
                out.write(gs + "\tconsensus\t" + "\t".join(sorted(consensus_genes)) + "\n")

    print(f"✅ Consensus GMT saved to: {out_gmt}")



# compare_gmts("out/genesets/qwen/genesets_entrez_qwen.gmt", "out/genesets/deepseek/genesets_entrez_deepseek.gmt", "out/genesets/llama/genesets_entrez_llama.gmt", output_pdf="gene_set_barplots_400.pdf")

make_consensus_gmt(
    "out/genesets/qwen/genesets_entrez_qwen.gmt", "out/genesets/deepseek/genesets_entrez_deepseek.gmt", "out/genesets/llama/genesets_entrez_llama.gmt",
    out_gmt="consensus_gene_sets.gmt"
)

import re
import mygene

def normalize_name(name):
    name = name.lower()
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z0-9\s]", "", name)
    return name.strip()


def build_shared_gmt(consensus_gmt, phenotype_gene_file, output_gmt="phenotype_consensus_gene_sets.gmt"):
    
    # --- Load consensus gene sets ---
    def load_gmt(file_path):
        gene_sets = {}
        with open(file_path, "r") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) > 2:
                    gene_sets[parts[0]] = set(parts[2:])
        return gene_sets
    
    consensus_sets = load_gmt(consensus_gmt)
    consensus_lookup = {normalize_name(name): name for name in consensus_sets.keys()}

    # --- Load phenotype → gene symbol sets ---
    pheno_sets = {}
    with open(phenotype_gene_file, "r") as f:
        next(f)
        for line in f:
            cols = line.strip().split("\t")
            if len(cols) < 3:
                continue
            _, pheno_name, genes_str = cols[:3]
            genes = set(g.strip() for g in genes_str.split(",") if g.strip())
            pheno_sets[pheno_name] = genes

    pheno_lookup = {normalize_name(name): (name, genes) for name, genes in pheno_sets.items()}

    matched = {}

    # Match normalized names
    for norm in pheno_lookup:
        if norm in consensus_lookup:
            consensus_name = consensus_lookup[norm]
            original_name, gene_syms = pheno_lookup[norm]

            # # ✅ Convert SYMBOLS → ENTREZ
            mapped_genes, valid, invalid = id_mapping(list(gene_syms), mode="entrezgene")

            if invalid:
                print(f"⚠️ Warning: {len(invalid)} genes unmapped in {original_name}: {invalid[:8]}...")

            if mapped_genes:  # keep only if mapping yields genes
                matched[consensus_name] = set(mapped_genes)

    # --- Identify consensus gene sets with no phenotype match ---
    norm_pheno_names = set(pheno_lookup.keys())
    norm_consensus_names = set(consensus_lookup.keys())

    consensus_not_matched = norm_consensus_names - norm_pheno_names

    if consensus_not_matched:
        print("\n⚠️ Consensus gene sets with NO phenotype name mapping:")
        for nm in sorted(consensus_not_matched):
            print("   -", consensus_lookup[nm])
    else:
        print("\n✅ All consensus gene sets matched a phenotype name.")

    # --- Write final GMT with ENTIRELY ENTREZ IDs ---
    with open(output_gmt, "w") as out:
        for gs, genes in sorted(matched.items()):
            out.write(gs + "\tphenotype_gene_source_entrez\t" + "\t".join(sorted(genes)) + "\n")

    print(f"\n✅ Saved GMT: {output_gmt}")
    print(f"✅ Gene sets included: {len(matched)}")



build_shared_gmt(
    consensus_gmt="consensus_gene_sets.gmt",
    phenotype_gene_file="out/phenotype_to_gene_sets.txt",
    output_gmt="phenotype_consensus_gene_sets.gmt"
)
