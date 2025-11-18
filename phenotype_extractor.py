import json
import csv
from collections import defaultdict
from utils import compare_to_phenotypes_msigdb
import requests
import time
import os


# get 10265 phenotypes from g2p

# Input and output file names
# g2p_file = "geneset data/genes_to_phenotype.txt"
# hpo_db_file = "geneset data/c5.hpo.v2025.1.Hs.entrez.gmt"


# # Dictionary: phenotype -> set of gene symbols
# g2p_ids = set()


# # Parse the input file
# with open(g2p_file, "r", encoding="utf-8") as f:
#     reader = csv.DictReader(f, delimiter="\t")
#     for row in reader:
#         hpo_id = row["hpo_id"]
#         g2p_ids.add(hpo_id)

# # Count distinct phenotypes
# num_phenotypes = len(g2p_ids)
# print(f"Number of distinct phenotypes: {num_phenotypes}")

# get phenotypes not in g2p and not in p2g but in MSigDB_HPO
phenotype_file = "out/phenotype_to_gene_sets.txt"
hpo_db_file = "geneset data/c5.hpo.v2025.1.Hs.entrez.gmt"

# get in p2g
_, only_in_phenotypes, only_in_db_p2g, db_gene_sets =  compare_to_phenotypes_msigdb(phenotype_file, hpo_db_file)
print(len(db_gene_sets))


output_file = "out/only_in_db_p2g_details.json"

# Load JSON
with open(output_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract all HPO IDs
hpo_ids = [entry.get("id") for entry in data if "id" in entry]

# Count how many unique HPO IDs
unique_hpo_ids = set(hpo_ids)

print(f"Total records in file: {len(data)}")
print(f"Total HPO IDs found: {len(hpo_ids)}")
print(f"Unique HPO IDs: {len(unique_hpo_ids)}")
print("\nSample HPO IDs:", list(unique_hpo_ids)[:10])


# get phenotypes in HPO with no genes associated yet with them (will come back to this)

# <-for each phenotype get the ID, Name, Description, and Synonymas a JSON Dict-> #

# for g2p_ids
# base_term_url = "https://ontology.jax.org/api/hp/terms/"
# base_annotation_url = "https://ontology.jax.org/api/network/annotation/"

# g2p_ids = unique_hpo_ids
# results = []

# output_file = "out/phenotype_data_clean.json"

# # --- Load existing results if file exists (checkpointing) ---
# if os.path.exists(output_file):
#     with open(output_file, "r", encoding="utf-8") as f:
#         results = json.load(f)
# else:
#     results = []

# print(f"There are {len(results)} phenotypes extracted")

# # Track completed IDs so we don’t re-fetch
# done_ids = {r["id"] for r in results if "id" in r}

# session = requests.Session()


# for idx, hpo_id in enumerate(g2p_ids, start=1):
#     if hpo_id in done_ids:
#         continue  # skip already processed

#     encoded_id = hpo_id.replace(":", "%3A")
#     phenotype_info = {"id": hpo_id}

#     try:
#         # --- Term info ---
#         term_resp = session.get(f"{base_term_url}{encoded_id}", timeout=20)
#         term_resp.raise_for_status()
#         term_data = term_resp.json()

#         phenotype_info.update({
#             "name": term_data.get("name"),
#             "description": term_data.get("definition"),
#             "synonyms": term_data.get("synonyms", [])
#         })

#     except Exception as e:
#         print(f"Error fetching term {hpo_id}: {e}")
#         phenotype_info.update({"name": None, "description": None, "synonyms": []})

#     # Add to results
#     results.append(phenotype_info)

#     # --- Save incrementally every ID ---
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=2, ensure_ascii=False)

#     print(f"[{idx}/{len(g2p_ids)}] Saved {hpo_id}")

#     # Small pause to be polite to server
#     time.sleep(0.2)











# import json
# import os
# import time
# import requests

# def format_query(hpo_gene_set):
#     return hpo_gene_set.replace("HP_", "").replace("_", " ").title()

# # File paths
# input_file = "out/phenotype_data_clean.json"
# output_file = "out/only_in_db_p2g_details.json"

# # Load phenotype database
# with open(input_file, "r", encoding="utf-8") as f:
#     phenotype_data = json.load(f)

# phenotype_by_name = {
#     entry.get("name", "").lower(): entry
#     for entry in phenotype_data
#     if entry.get("name")
# }

# # Load your gene names
# # Replace with real variable
# only_in_db_p2g = db_gene_sets  # your list

# matched_entries = []
# missing = []

# # Step 1: Match locally
# for gene_set in only_in_db_p2g:
#     search_name = format_query(gene_set).lower()
#     if search_name in phenotype_by_name:
#         matched_entries.append(phenotype_by_name[search_name])
#     else:
#         missing.append(gene_set)

# # Step 2: Query HPO API for missing ones
# base_url = "https://ontology.jax.org/api/hp/search?q="

# for term in missing:
#     query = format_query(term)
#     search_url = f"{base_url}{query}&page=0&limit=1"
#     try:
#         r = requests.get(search_url, timeout=10)
#         r.raise_for_status()
#         data = r.json()

#         if "terms" in data and len(data["terms"]) > 0:
#             term_data = data["terms"][0]
#             matched_entries.append({
#                 "id": term_data.get("id"),
#                 "name": term_data.get("label"),
#                 "description": term_data.get("definition"),
#                 "synonyms": term_data.get("synonyms", [])
#             })
#         else:
#             print(f"❌ No HPO API match for: {term}")
#     except Exception as e:
#         print(f"⚠️ Error fetching {term} from HPO API: {e}")

#     time.sleep(0.2)  # Be kind to server

# # Step 3: Save result
# with open(output_file, "w", encoding="utf-8") as f:
#     json.dump(matched_entries, f, indent=2, ensure_ascii=False)

# print(f"\n✅ Final saved to {output_file}")
# print(f"✔️ Total matched with info: {len(matched_entries)}")
# print(f"❌ Still missing after API lookup: {len(only_in_db_p2g) - len(matched_entries)}")



# import os
# import time
# import json
# import requests

# INPUT_LIST = missing  # <- your list of phenotype names like HP_ABDOMINAL_CRAMPS
# OUTPUT_FILE = "out/p2g_missing_hpo_details.json"
# API_URL = "https://ontology.jax.org/api/hp/search"
# REQUEST_DELAY = 0.3  # seconds between requests

# def load_existing_results():
#     if os.path.exists(OUTPUT_FILE):
#         with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     return []

# def save_results(results):
#     os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
#     with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=2, ensure_ascii=False)

# def format_query(hpo_gene_set):
#     # Convert HP_ABDOMINAL_CRAMPS -> "Abdominal Cramps"
#     name = hpo_gene_set.replace("HP_", "").replace("_", " ").title()
#     return name

# def fetch_hpo_info(query):
#     params = {"q": query, "page": 0, "limit": 1}
#     try:
#         resp = requests.get(API_URL, params=params, timeout=20)
#         resp.raise_for_status()
#         results = resp.json().get("terms", [])
#         if results:
#             term = results[0]
#             return {
#                 "id": term.get("id"),
#                 "name": term.get("name"),
#                 "description": term.get("definition"),
#                 "synonyms": term.get("synonymNames", []),
#             }
#     except Exception as e:
#         print(f"⚠️ Error fetching query '{query}': {e}")
#     return None

# def main():
#     results = load_existing_results()
#     processed = {entry["query"] for entry in results}

#     print(f"🔍 {len(INPUT_LIST)} phenotypes to search from msigdb missing ones")
#     print(f"✅ {len(processed)} already processed")
#     print(f"➡️ {len(INPUT_LIST) - len(processed)} remaining\n")

#     for hpo_term in INPUT_LIST:
#         query = format_query(hpo_term)
#         if query in processed:
#             continue

#         print(f"🔎 Searching: {query} ...")
#         data = fetch_hpo_info(query)

#         entry = {"query": query, "source": hpo_term, "found": bool(data)}
#         if data:
#             entry.update(data)
#             print(f"✅ Found: {data['name']} ({data['id']})")
#         else:
#             print(f"❌ No match found in HPO for '{query}'")

#         results.append(entry)
#         save_results(results)
#         time.sleep(REQUEST_DELAY)

#     print("\n🎉 Done! Results saved to", OUTPUT_FILE)

# if __name__ == "__main__":
#     main()
