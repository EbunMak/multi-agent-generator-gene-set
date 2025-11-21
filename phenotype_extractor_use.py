import json
import time
import os
import requests
from utils import compare_to_phenotypes_msigdb
from phenotype_extractor import extract_phenotype_details


PHENOTYPE_FILE = "out/phenotype_to_gene_sets.txt"
HPO_DB_FILE = "geneset data/c5.hpo.v2025.1.Hs.entrez.gmt"
OUTPUT_FILE = "out/in_db_and_p2g_details.json"

#Identify phenotypes in HPO DB and in p2g

in_db_and_p2g, _, _, _ = compare_to_phenotypes_msigdb(PHENOTYPE_FILE, HPO_DB_FILE)
print(f" Identified {len(in_db_and_p2g)} phenotypes in both p2g and HPO DB")
# # Load previous results (checkpointing)
# if os.path.exists(OUTPUT_FILE):
#     with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
#         results = json.load(f)
# else:
#     results = []

# already_done = {entry["id"] for entry in results if "id" in entry}
# print(f" Already extracted {len(already_done)} phenotypes")


# # query HPO API for each phenotype

# final_output = results  # continue appending

# for idx, raw_term in enumerate(in_db_and_p2g, start=1):
#     print(f"[{idx}/{len(in_db_and_p2g)}] Extracting details for: {raw_term}")
#     extract_phenotype_details(raw_term, OUTPUT_FILE)

# print(f"Saved {len(final_output)} entries to {OUTPUT_FILE}")
