import os
import json
from rag_pipeline_gene_checker_qwen import create_control_flow
from utils import GraphState

PROCESSED_GENES_FILE = "processed_genes_qwen.json"
PROCESSED_SETS_FILE = "processed_gene_sets_qwen.txt"

def read_gmt(file_path):
    """
    Read a GMT file and return a dictionary:
    { gene_set_name: [list_of_genes] }

    Cleans gene set names such as 'HP_11_PAIRS_OF_RIBS' → '11 pairs of ribs'
    """
    gene_sets = {}
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            raw_name = parts[0]
            cleaned_name = (
                raw_name.replace("HP_", "")
                        .replace("MP_", "")
                        .replace("_", " ")
                        .strip()
                        .capitalize()
            )
            genes = parts[2:]
            gene_sets[cleaned_name] = genes
    return gene_sets


def load_processed():
    """Load processed genes per gene set."""
    if os.path.exists(PROCESSED_GENES_FILE):
        with open(PROCESSED_GENES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_processed(processed):
    """Save processed genes dictionary."""
    with open(PROCESSED_GENES_FILE, "w") as f:
        json.dump(processed, f, indent=2)

def mark_gene_processed(gene_set, gene, processed):
    """Mark a gene as processed for a given gene set."""
    processed.setdefault(gene_set, [])
    if gene not in processed[gene_set]:
        processed[gene_set].append(gene)
        save_processed(processed)

def mark_set_complete(gene_set):
    """Append completed gene set to processed_gene_sets.txt."""
    with open(PROCESSED_SETS_FILE, "a") as f:
        f.write(f"{gene_set}\n")


def main():
    gmt_path = "geneset data/c5.hpo.v2025.1.Hs.symbols.gmt"
    gene_sets = read_gmt(gmt_path)

    print(f"📘 Loaded {len(gene_sets)} gene sets from {gmt_path}")

    # Load previously processed phenotypes (DeepSeek run)
    processed_phenotypes_file = "out/processed_phenotypes_qwen.txt"
    if os.path.exists(processed_phenotypes_file):
        with open(processed_phenotypes_file, "r") as f:
            processed_phenotypes = set(line.strip() for line in f if line.strip())
    else:
        print("⚠️ No processed phenotypes file found. Nothing will be processed.")
        return

    print(f"✅ Found {len(processed_phenotypes)} processed phenotypes to check genes for.")

    processed_genes = load_processed()
    completed_sets = set()
    if os.path.exists(PROCESSED_SETS_FILE):
        with open(PROCESSED_SETS_FILE, "r") as f:
            completed_sets = set(line.strip() for line in f if line.strip())
    # Iterate over all gene sets
    for set_name, genes in gene_sets.items():
        # 🧩 Only process gene sets that were processed previously to find genes from abstracts
        if set_name not in processed_phenotypes:
            print(f"⏭️ Skipping {set_name} (not in processed phenotypes).")
            continue

        # Skip sets fully completed already
        if set_name in completed_sets:
            print(f"⏭️ Skipping already completed gene set: {set_name}")
            continue

        print(f"\n🧬 Processing gene set: {set_name} ({len(genes)} genes)")
        processed_genes.setdefault(set_name, [])

        for gene in genes:
            if gene in processed_genes[set_name]:
                print(f"  🔁 Skipping {gene} (already processed)")
                continue

            try:
                phenotype = {
                    "name": set_name,
                    "gene": gene,
                    "definition": "",
                    "synonyms": []
                }

                print(f"➡️  Checking {gene} for {set_name}")

                # Run LangGraph pipeline
                graph = create_control_flow()
                inputs = {"phenotype": phenotype}

                for _ in graph.stream(inputs, stream_mode="values"):
                    pass

                mark_gene_processed(set_name, gene, processed_genes)
                print(f"✅ Completed {gene} for {set_name}")

            except Exception as e:
                print(f"❌ Error processing {gene} in {set_name}: {e}")

        mark_set_complete(set_name)
        print(f"🎯 Finished gene set: {set_name}")

    print("\n✅ All eligible gene sets processed successfully.")


if __name__ == "__main__":
    main()
