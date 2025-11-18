import os
import json
from typing import Dict, List, Any
from datetime import datetime

# we assume your utils.py is in the same module / on PYTHONPATH
from utils import id_mapping   # your existing function

processed_file = "processed_gene_sets.txt"
if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            processed = {line.strip() for line in f if line.strip()}
else:
        processed = set()

# ============================================================
# 1. LOAD EXTRACTED GENES (LLM outputs)
#    Dir structure: extracted_dir/<phenotype>.json
#    Each file: list of dicts like:
#    [
#      {"Gene": "KAL1", "Source Reference": "...", "PMID": "35227688", "Journal": "Kidney Int"},
#      ...
#    ]
# ============================================================
def load_extracted_genes(extracted_dir: str) -> Dict[str, List[dict]]:
    pheno_to_extracted: Dict[str, List[dict]] = {}
    if not os.path.exists(extracted_dir):
        print(f"⚠️ extracted_dir '{extracted_dir}' not found, skipping extracted genes.")
        return pheno_to_extracted

    for fname in os.listdir(extracted_dir):
        if not fname.endswith(".json"):
            continue
        pheno_name = os.path.splitext(fname)[0]
        if pheno_name not in processed:
            continue
        fpath = os.path.join(extracted_dir, fname)
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            # tag the source
            for d in data:
                d.setdefault("Source", "Extracted")
            pheno_to_extracted[pheno_name] = data
        except Exception as e:
            print(f"⚠️ Could not read extracted file {fpath}: {e}")
    return pheno_to_extracted


# ============================================================
# 2. LOAD VERIFIED GENES
#    Dir-of-dirs: verified_dir/<phenotype>/<GENE>.json
#    Each file:
#    {
#      "Gene": "ABCC6",
#      "Validation": "yes",
#      "Supporting Extract": "...",
#      "PMIDS": [..]
#    }
# ============================================================
def load_verified_genes(verified_dir: str) -> Dict[str, List[dict]]:
    pheno_to_verified: Dict[str, List[dict]] = {}
    if not os.path.exists(verified_dir):
        print(f"⚠️ verified_dir '{verified_dir}' not found, skipping verified genes.")
        return pheno_to_verified

    for pheno_name in os.listdir(verified_dir):
        pheno_path = os.path.join(verified_dir, pheno_name)
        if not os.path.isdir(pheno_path):
            continue

        entries: List[dict] = []
        for gene_file in os.listdir(pheno_path):
            if not gene_file.endswith(".json"):
                continue
            gpath = os.path.join(pheno_path, gene_file)
            try:
                with open(gpath, "r") as f:
                    data = json.load(f)
                # only keep validated ones
                if str(data.get("Validation", "")).lower() == "yes":
                    data.setdefault("Source", "Verified")
                    entries.append(data)
            except Exception as e:
                print(f"⚠️ Could not read verified file {gpath}: {e}")

        if entries:
            pheno_to_verified[pheno_name] = entries

    return pheno_to_verified


# ============================================================
# 3. MERGE BOTH SOURCES
#    Rules:
#    - keyed by phenotype
#    - within phenotype, keyed by gene symbol
#    - Source: Extracted / Verified / Both
#    - PMIDs merged (unique)
# ============================================================
def merge_extracted_and_verified(
    extracted: Dict[str, List[dict]],
    verified: Dict[str, List[dict]],
) -> Dict[str, List[dict]]:
    all_phenos = set(extracted.keys()) | set(verified.keys())
    merged: Dict[str, List[dict]] = {}

    for pheno in all_phenos:
        merged_by_gene: Dict[str, dict] = {}

        # add extracted first
        extracted_count = 0
        for entry in extracted.get(pheno, []):
            gene = entry.get("Gene")
            if not gene:
                continue
            extracted_count+=1
            merged_by_gene[gene] = {
                "Gene": gene,
                "Source": "Extracted",
                "Source Reference": entry.get("Source Reference", ""),
                "Journal": entry.get("Journal", ""),
                # normalize pmids to list
                "PMIDS": _normalize_pmids(entry.get("PMID") or entry.get("PMIDS")),
            }
        

        # add verified, merging if gene already present
        for entry in verified.get(pheno, []):
            gene = entry.get("Gene")
            if not gene:
                continue

            v_pmids = _normalize_pmids(entry.get("PMIDS"))
            v_extract = entry.get("Supporting Extract", "")
            v_journal = entry.get("Journal", "")

            if gene in merged_by_gene:
                # upgrade source
                merged_by_gene[gene]["Source"] = "Both"
                # merge pmids
                merged_by_gene[gene]["PMIDS"] = _unique_list(
                    merged_by_gene[gene].get("PMIDS", []) + v_pmids
                )
                # prefer verified extract if present
                if v_extract:
                    merged_by_gene[gene]["Source Reference"] = v_extract
                # prefer verified journal if present
                if v_journal:
                    merged_by_gene[gene]["Journal"] = v_journal
            else:
                merged_by_gene[gene] = {
                    "Gene": gene,
                    "Source": "Verified",
                    "Source Reference": v_extract,
                    "Journal": v_journal,
                    "PMIDS": v_pmids,
                }

        merged[pheno] = list(merged_by_gene.values())

    return merged


def _normalize_pmids(pmids_field: Any) -> List[str]:
    """
    Accepts:
      - "12345"
      - 12345
      - ["12345", "67890"]
      - [12345, 67890]
    Returns list of strings
    """
    if pmids_field is None:
        return []
    if isinstance(pmids_field, (int, str)):
        return [str(pmids_field)]
    if isinstance(pmids_field, list):
        return [str(x) for x in pmids_field if x]
    return []


def _unique_list(seq: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ============================================================
# 4. BUILD GMTs from merged data
# ============================================================
def build_gmts_from_merged(
    pheno_to_entries: Dict[str, List[dict]],
    out_symbols: str,
    out_entrez: str,
):
    os.makedirs(os.path.dirname(out_symbols), exist_ok=True)
    os.makedirs(os.path.dirname(out_entrez), exist_ok=True)

    unmapped_per_pheno: Dict[str, List[str]] = {}

    with open(out_symbols, "w") as f_sym, open(out_entrez, "w") as f_ent:
        for phenotype, entries in pheno_to_entries.items():
            # collect all gene symbols for that phenotype
            symbols = [e["Gene"] for e in entries if e.get("Gene")]
            # write symbols GMT row
            if symbols:
                f_sym.write(
                    phenotype + "\t" + "combined extracted+verified" + "\t" + "\t".join(symbols) + "\n"
                )

            # map to entrez
            if symbols:
                mapped, valid, invalid = id_mapping(symbols, mode="entrezgene")
                if invalid:
                    unmapped_per_pheno.setdefault(phenotype, []).extend(invalid)
                if mapped:
                    f_ent.write(
                        phenotype
                        + "\t"
                        + "combined extracted+verified (entrez)"
                        + "\t"
                        + "\t".join(str(m) for m in mapped)
                        + "\n"
                    )

    return unmapped_per_pheno


# ============================================================
# 5. HTML SUMMARY (with Source column + PubMed links)
# ============================================================
def save_html_summary(
    pheno_to_entries: Dict[str, List[dict]],
    html_out: str,
    title: str = "Phenotype → Genes (Extracted + Verified)",
):
    os.makedirs(os.path.dirname(html_out), exist_ok=True)

    rows = []
    for phenotype, entries in pheno_to_entries.items():
        for e in entries:
            gene = e.get("Gene", "")
            source = e.get("Source", "")
            journal = e.get("Journal", "")
            ref = e.get("Source Reference", "")
            pmids = e.get("PMIDS", [])

            pmid_links = ", ".join(
                f'<a href="https://pubmed.ncbi.nlm.nih.gov/{p}/" target="_blank">{p}</a>'
                for p in pmids
            )

            rows.append(
                f"<tr>"
                f"<td>{phenotype}</td>"
                f"<td>{gene}</td>"
                f"<td>{source}</td>"
                f"<td>{journal}</td>"
                f"<td>{pmid_links}</td>"
                f"<td>{ref}</td>"
                f"</tr>"
            )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" type="text/css"
        href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css"/>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 20px;
    }}
    table.dataTable td {{
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
      max-width: 400px;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>Generated: {datetime.utcnow().isoformat()} UTC</p>
  <table id="phenoGenes" class="display" style="width:100%">
    <thead>
      <tr>
        <th>Phenotype</th>
        <th>Gene</th>
        <th>Source</th>
        <th>Journal</th>
        <th>PMIDs</th>
        <th>Supporting / Source Extract</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>

  <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
  <script>
    $(document).ready(function() {{
        $('#phenoGenes').DataTable({{
            pageLength: 25
        }});
    }});
  </script>
</body>
</html>
"""
    with open(html_out, "w") as f:
        f.write(html)
    print(f"✅ HTML summary written to {html_out}")


# ============================================================
# 6. SAVE UNMAPPED
# ============================================================
def save_unmapped(unmapped: Dict[str, List[str]], out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(unmapped, f, indent=2)
    print(f"✅ Unmapped genes written to {out_path}")


# ============================================================
# 7. MAIN
# ============================================================
def main():
    #CHANGE THESE TO YOUR REAL PATHS
    extracted_dir = "out/phenotype_generations/deepseek-r1:8b"     # e.g. "out/phenotype_generations"
    verified_dir = "out/phenotype_checks/deepseek-r1:8b"       # e.g. "out/verified_genes"
    out_dir = "out/genesets/deepseek"
    os.makedirs(out_dir, exist_ok=True)

    # 1) load both sources
    extracted = load_extracted_genes(extracted_dir)
    verified = load_verified_genes(verified_dir)

    # 2) merge
    merged = merge_extracted_and_verified(extracted, verified)

    # 3) build GMTs
    symbols_gmt = os.path.join(out_dir, "genesets_symbols_deepseek.gmt")
    entrez_gmt = os.path.join(out_dir, "genesets_entrez_deepseek.gmt")
    unmapped = build_gmts_from_merged(merged, symbols_gmt, entrez_gmt)

    # 4) HTML
    html_out = os.path.join(out_dir, "phenotype_gene_summary_deepseek.html")
    save_html_summary(merged, html_out)

    # 5) unmapped
    unmapped_out = os.path.join(out_dir, "unmapped_genes_deepseek.json")
    save_unmapped(unmapped, unmapped_out)


if __name__ == "__main__":
    main()
