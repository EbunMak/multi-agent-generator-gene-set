import pandas as pd
from collections import defaultdict

# ------------ FILE PATHS ------------
file1 = "41586_2025_8623_MOESM7_ESM.xlsx"   # contains disease group, disease, gene
file2 = "41586_2025_8623_MOESM6_ESM.xlsx"   # contains disease and gene

# ------------ LOAD FILE 1 (MOESM7) ------------
df1 = pd.read_excel(file1, sheet_name="triaged_signals")

# We assume columns include:
# "Disease group", "Specific disease", "Gene"

# Create main dictionary
disease_dict = defaultdict(lambda: {"disease_group": None, "genes": set()})

for _, row in df1.iterrows():
    disease = str(row["Specific disease"]).strip()
    disease_group = str(row["Disease group"]).strip()
    disease_evidence = str(row["ClinGen final classification"]).strip()  # Optional
    gene = str(row["Gene"]).strip()

    if disease and disease_evidence == "MODERATE":  # Only include MODERATE evidence diseases
        # Set disease group (only if not already set)
        if disease_dict[disease]["disease_group"] is None:
            disease_dict[disease]["disease_group"] = disease_group
        
        # Add gene
        if gene and gene != "nan":
            disease_dict[disease]["genes"].add(gene)

# ------------ LOAD FILE 2 (MOESM6) ------------
df2 = pd.read_excel(file2, sheet_name="triage_burden_test_03_07_24")

# Columns we use:
# "Disease", "Gene"

# for _, row in df2.iterrows():
#     disease = str(row["Disease"]).strip()
#     gene = str(row["Gene"]).strip()

#     if disease:
#         # If disease not in dict, add
#         if disease not in disease_dict:
#             disease_dict[disease] = {"disease_group": None, "genes": set()}
        
#         # Add gene
#         if gene and gene != "nan":
#             disease_dict[disease]["genes"].add(gene)

# ------------ OPTIONAL: Convert sets to lists for JSON export ------------
disease_dict_json = {
    disease: {
        "disease_group": info["disease_group"],
        "genes": sorted(list(info["genes"]))
    }
    for disease, info in disease_dict.items()
}

# ------------ EXAMPLE OUTPUT ------------
print("Number of diseases found:", len(disease_dict_json))
print("Example entry:")
for d in list(disease_dict_json.keys())[:5]:
    print(d, "→", disease_dict_json[d])

# ------------ SAVE JSON TO FILE ------------
import json

with open("disease_gene_map.json", "w") as f:
    json.dump(disease_dict_json, f, indent=4)

print("Saved output to disease_gene_map.json")
