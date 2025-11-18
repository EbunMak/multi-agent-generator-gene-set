import json
import os

def extract_genes_json(phenotype_json):
    with open(phenotype_json, "r") as f:
            #read list of json 
            genes_info =  json.load(f)
    #if list is empty return None
    if not genes_info:
        print(f"No genes found in {phenotype_json}")
        return None, None
    #store name of phenotype
    phenotype_name = os.path.splitext(os.path.basename(phenotype_json))[0]
    genes = []
    #iterate and get the genes form the list of json
    for entry in genes_info:
        # Handle different possible formats of model output
        gene_name = entry.get("Gene") 
        # pmid = entry.get("PMID")

        if gene_name:
            genes.append(gene_name)

    # If still empty, return None
    if not genes:
        print(f"No valid gene entries found in {phenotype_json}")
        return None, None

    return phenotype_name, genes


import csv
from geneset_constructor import extract_genes_json
import os
from utils import write_gmt

PMIDS_FILE = "abstracts/pubtator/gene2pubtator/pmids.txt"


if not os.path.exists(PMIDS_FILE):
    print(f"PMID list file {PMIDS_FILE} not found.")

with open(PMIDS_FILE, "r") as f:
    pmids = [line.strip() for line in f if line.strip()]

total_pmids = len(pmids)
print(f"Total PMIDs to process: {total_pmids}")

with open("abstracts/pubtator/gene2pubtator/updated_pmids.txt", "w") as file:
    for pmid in pmids[76231:]:
        file.write(str(pmid) +"\n")



out_dir = "out/phenotype_generations/llama3"

# iterate through files in out folder and then extract genes in the phenotypes
all_phenotypes = {}

for filename in os.listdir(out_dir):
    if filename.endswith(".json"):
        file_path = os.path.join(out_dir, filename)
        phenotype, genes = extract_genes_json(file_path)
        if phenotype:
            all_phenotypes[phenotype] = list(set(genes))

write_gmt("sample_hpo_deepseek_2.gmt", all_phenotypes)
