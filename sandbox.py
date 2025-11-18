# from utils import phenotype_json_reader

# def find_json_index(json_list, target_name):
#     """
#     Given a list of phenotype JSONs and a target name, 
#     return the index of the entry with that name.

#     Args:
#         json_list (list): List of JSON-like dicts.
#         target_name (str): The phenotype name to search for.

#     Returns:
#         int: Index of the matching entry, or -1 if not found.
#     """
#     for i, entry in enumerate(json_list):
#         # Match ignoring case and leading/trailing spaces
#         if entry.get("name", "").strip().lower() == target_name.strip().lower():
#             return i
#     return -1

# phenotype_json_file = "out/only_in_db_p2g_details.json"
# phenotypes = phenotype_json_reader(phenotype_json_file)
# idx = find_json_index(phenotypes, "Neonatal seizure")
# print(idx)

import os

def update_processed_phenotypes(processed_file, genes_dir):
    """
    Compare processed phenotypes (in a .txt file) with actual phenotypes
    having gene extraction JSON files in a directory, and update the file.

    Args:
        processed_file (str): Path to text file containing processed phenotype names.
        genes_dir (str): Directory containing gene extraction JSON files.
    """

    # Read processed phenotypes from file
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            processed = {line.strip() for line in f if line.strip()}
    else:
        processed = set()

    # Get phenotypes from directory (remove extensions and normalize names)
    actual = {
        os.path.splitext(fname)[0]
        for fname in os.listdir(genes_dir)
        # if fname.endswith(".json")
    }

    # if os.path.exists(genes_dir):
    #     with open(genes_dir, "r") as f:
    #         actual = {line.strip() for line in f if line.strip()}
    # else:
    #     actual = set()

    # Find differences
    missing_from_file = actual - processed
    missing_from_dir = processed - actual

    print(f"✅ Total processed in file: {len(processed)}")
    print(f"✅ Total found in directory: {len(actual)}")
    print(f"➕ To add (found in dir, not in file): {len(missing_from_file)}")
    print(f"❌ To remove (in file, not in dir): {len(missing_from_dir)}")

    # Update the processed list to reflect actual extracted ones
    updated = sorted(actual)
    for i in missing_from_file:
        print(i)
    with open(processed_file, "w") as f:
        for name in updated:
            f.write(f"{name}\n")

    print(f"✅ Updated processed list saved to {processed_file}")

    # Return differences for logging or debugging
    return {
        "added": sorted(missing_from_file),
        "removed": sorted(missing_from_dir),
        "final_count": len(updated)
    }

update_processed_phenotypes("processed_gene_sets_qwen.txt", "out/phenotype_checks/qwen3:32b")

# import csv
# from geneset_constructor import extract_genes_json
# import os
# from utils import write_gmt

# PMIDS_FILE = "abstracts/pubtator/gene2pubtator/pmids.txt"


# if not os.path.exists(PMIDS_FILE):
#     print(f"PMID list file {PMIDS_FILE} not found.")

# with open(PMIDS_FILE, "r") as f:
#     pmids = [line.strip() for line in f if line.strip()]

# total_pmids = len(pmids)
# print(f"Total PMIDs to process: {total_pmids}")

# with open("abstracts/pubtator/gene2pubtator/updated_pmids.txt", "w") as file:
#     for pmid in pmids[76231:]:
#         file.write(str(pmid) +"\n")



# out_dir = "out/phenotype_generations/llama3"

# # iterate through files in out folder and then extract genes in the phenotypes
# all_phenotypes = {}

# for filename in os.listdir(out_dir):
#     if filename.endswith(".json"):
#         file_path = os.path.join(out_dir, filename)
#         phenotype, genes = extract_genes_json(file_path)
#         if phenotype:
#             all_phenotypes[phenotype] = list(set(genes))

# write_gmt("sample_hpo_llama3.gmt", all_phenotypes)


# import sqlite3
# import json
# import time

# DB_FILE = "pubtator_local.db"
# TEST_PMID = "1000041"  # Replace with a PMID you know exists in your DB

# def get_abstract(conn, pmid):
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM abstracts WHERE pmid = ?", (pmid,))
#     row = cur.fetchone()
#     if row:
#         return {
#             "pmid": row[0],
#             "title": row[1],
#             "journal": row[2],
#             "abstract": row[3],
#             "genes": json.loads(row[4])
#         }
#     return None

# def main():
#     conn = sqlite3.connect(DB_FILE)

#     start_time = time.time()
#     abstract_data = get_abstract(conn, TEST_PMID)
#     end_time = time.time()

#     if abstract_data:
#         print(f"Retrieved PMID {TEST_PMID} in {end_time - start_time:.6f} seconds")
#         print("Title:", abstract_data["title"])
#         print("Journal:", abstract_data["journal"])
#         print("Number of genes:", len(abstract_data["genes"]))
#     else:
#         print(f"PMID {TEST_PMID} not found in the database.")

#     conn.close()

# if __name__ == "__main__":
#     main()



# # Input files
# phenotype_file = "smaple_hpo.gmt"
# hpo_db_file = "geneset data/c5.hpo.v2025.1.Hs.entrez.gmt"

# # --- Load phenotype gene sets ---
# phenotype_names = set()
# # phenotype_ids = {}

# # with open(phenotype_file, "r", encoding="utf-8") as f:
# #     reader = csv.DictReader(f, delimiter="\t")
# #     for row in reader:
# #         hpo_id = row["hpo_id"].strip()
# #         hpo_name = row["hpo_name"].strip()
# #         hpo_name = "HP_" + hpo_name
# #         hpo_name = hpo_name.replace("-", "_")
# #         phenotype_names.add(hpo_name.upper().replace(" ", "_"))  # normalize
# #         phenotype_ids[hpo_id] = hpo_name

# # --- Load MSigDB HPO gene set database ---
# with open(phenotype_file, "r", encoding="utf-8") as f:
#     for line in f:
#         parts = line.strip().split("\t")
#         if not parts:
#             continue
#         gs_name = parts[0].strip()
#         # gs_name = parts[0].strip('HP_')
#         gs_name = "HP_" + gs_name
#         phenotype_names.add(gs_name.upper())
#           # keep the rest if needed



# # --- Load MSigDB HPO gene set database ---
# db_gene_sets = set()
# db_full = {}

# with open(hpo_db_file, "r", encoding="utf-8") as f:
#     for line in f:
#         parts = line.strip().split("\t")
#         if not parts:
#             continue
#         gs_name = parts[0].strip()
#         # gs_name = parts[0].strip('HP_')
#         db_gene_sets.add(gs_name)
#         db_full[gs_name] = parts[1:]  # keep the rest if needed
# print(list(phenotype_names)[:2])

# print(list(db_gene_sets)[:2])

# # --- Compare ---
# in_both = phenotype_names & db_gene_sets
# only_in_phenotypes = phenotype_names - db_gene_sets
# only_in_db = db_gene_sets - phenotype_names

# print(f"Matches found: {len(in_both)}")
# print(f"Only in phenotypes file: {len(only_in_phenotypes)}")
# print(f"Only in database file: {len(only_in_db)}")

# # --- Write results ---
# with open("new_comparison_results.txt", "w", encoding="utf-8") as out:
#     out.write("=== In Both ===\n")
#     for name in sorted(in_both):
#         out.write(name + "\n")

#     out.write("\n=== Only in Phenotypes File ===\n")
#     for name in sorted(only_in_phenotypes):
#         out.write(name + "\n")

#     out.write("\n\n")
#     for name in sorted(only_in_db):
#         out.write(name + "\n")


# import csv
# from collections import defaultdict

# # Input and output file names
# input_file = "geneset data/genes_to_phenotype.txt"
# output_file = "out/phenotype_to_genes_from_genes_to_phenotypes.txt"

# # Dictionary: phenotype -> set of gene symbols
# phenotype_genes = defaultdict(set)
# phenotype_names = {}

# # Parse the input file
# with open(input_file, "r", encoding="utf-8") as f:
#     reader = csv.DictReader(f, delimiter="\t")
#     for row in reader:
#         hpo_id = row["hpo_id"]
#         hpo_name = row["hpo_name"]
#         gene_symbol = row["gene_symbol"]

#         phenotype_names[hpo_id] = hpo_name
#         phenotype_genes[hpo_id].add(gene_symbol)

# # Count distinct phenotypes
# num_phenotypes = len(phenotype_genes)
# print(f"Number of distinct phenotypes: {num_phenotypes}")

# # Write output file
# with open(output_file, "w", encoding="utf-8") as f:
#     writer = csv.writer(f, delimiter="\t")
#     writer.writerow(["hpo_id", "hpo_name", "genes"])
#     for hpo_id, genes in phenotype_genes.items():
#         writer.writerow([hpo_id, phenotype_names[hpo_id], ",".join(sorted(genes))])



# # # Input and output file names
# # input_file = "geneset data/phenotype_to_genes.txt"
# # output_file = "out/phenotype_to_gene_sets.txt"

# # # Dictionary: phenotype -> set of gene symbols
# # phenotype_genes = defaultdict(set)
# # phenotype_names = {}

# # # Parse the input file
# # with open(input_file, "r", encoding="utf-8") as f:
# #     reader = csv.DictReader(f, delimiter="\t")
# #     for row in reader:
# #         hpo_id = row["hpo_id"]
# #         hpo_name = row["hpo_name"]
# #         gene_symbol = row["gene_symbol"]

# #         phenotype_names[hpo_id] = hpo_name
# #         phenotype_genes[hpo_id].add(gene_symbol)

# # # Count distinct phenotypes
# # num_phenotypes = len(phenotype_genes)
# # print(f"Number of distinct phenotypes with ≥1 gene: {num_phenotypes}")

# # # Write output file
# # with open(output_file, "w", encoding="utf-8") as f:
# #     writer = csv.writer(f, delimiter="\t")
# #     writer.writerow(["hpo_id", "hpo_name", "genes"])
# #     for hpo_id, genes in phenotype_genes.items():
# #         writer.writerow([hpo_id, phenotype_names[hpo_id], ",".join(sorted(genes))])

no_new_genes = ['Abdominal colic', 'Abnormal blistering of the skin', 'Abnormal caudate nucleus morphology', 'Abnormal circulating interleukin 10 concentration', 'Abnormal circulating isoleucine concentration', 'Abnormal corneal epithelium morphology', 'Abnormal lung lobation', 'Abnormal mesentery morphology', 'Abnormal periungual morphology', 'Abnormal pulse', 'Abnormal shoulder physiology', 'Abnormal spinal meningeal morphology', 'Abnormal toe morphology', 'Abnormality of peripheral nerve conduction', 'Abnormality of the dentition', 'Abnormality of the phalanges of the 3rd toe', 'Abnormality of the proximal phalanx of the 5th finger', 'Absence of the sacrum', 'Absent palmar crease', 'Antimitochondrial antibody positivity', 'Aplasia of the bladder', 'Aplasia of the ulna', 'Axillary freckling', 'Bifid distal phalanx of the thumb', 'Broad first metatarsal', 'Bronchial wall thickening', 'Cardiac rhabdomyoma', 'Cerebellar hemorrhage', 'Choroid plexus cyst', 'Complete duplication of phalanx of hand', 'Crackles', 'Crumpled ear', 'Cupped ribs', 'Decreased libido', 'Deviation of the 4th finger', 'Diffuse optic disc pallor', 'Distal symphalangism', 'Easy fatigability', 'Ectopia lentis', 'Enlarged sylvian cistern', 'Enuresis', 'Fair hair', 'Fifth finger distal phalanx clinodactyly', 'Flared iliac wing', 'Gastrointestinal desmoid tumor', 'Hemianopia', 'Hyperventilation', 'Hypotension', 'Impaired vibration sensation at ankles', 'Increased circulating gonadotropin level', 'Increased intervertebral space', 'Intercostal muscle weakness', 'Interrupted aortic arch', 'Limb muscle weakness', 'Limited hip extension', 'Lower limb hyperreflexia', 'Moon facies', 'Nocturia', 'Orofacial dyskinesia', 'Palmar pruritus', 'Parietal foramina', 'Partial duplication of the distal phalanges of the hand', 'Patchy changes of bone mineral density', 'Periauricular skin pits', 'Peripheral arterial stenosis', 'Polyembolokoilamania', 'Premature loss of teeth', 'Prominent sternum', 'Prominent umbilicus', 'Radial deviation of finger', 'Recurrent hand flapping', 'Recurrent protozoan infections', 'Short 4th toe', 'Skin dimple', 'Slow pupillary light response', 'Small hand', 'Stomatocytosis', 'Syndactyly']
print(f"Total phenotypes with NO new genes: {len(no_new_genes)}")