import os
import json
from typing import Dict, List, Any
from datetime import datetime
from difflib import SequenceMatcher
from gene_construtor_utils import normalize_text, hybrid_similarity

# we assume your utils.py is in the same module / on PYTHONPATH
from utils import id_mapping   # your existing function

# Where the per-phenotype abstracts live (no extension, JSON list)
ABSTRACTS_DIR = "abstracts/gene_annotated_abstracts"  # <-- adjust if needed

processed_file = "processed_gene_sets.txt"
if os.path.exists(processed_file):
    with open(processed_file, "r") as f:
        processed = {line.strip() for line in f if line.strip()}
else:
    processed = set()


# ------------------------------------------------------------
# Helper: normalize & de-duplicate PMIDs
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# 0. PMID correction using phenotype abstracts       *** NEW ***
# ------------------------------------------------------------
def _load_phenotype_abstracts(phenotype: str) -> List[dict]:
    """
    Load abstracts JSON for a phenotype. File has no extension.
    Returns list of dicts with keys like 'pmid', 'abstract', 'title', etc.
    """
    if not ABSTRACTS_DIR:
        return []
    path = os.path.join(ABSTRACTS_DIR, phenotype)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        return data
    except Exception as e:
        print(f"⚠️ Could not load abstracts for {phenotype} from {path}: {e}")
        return []


def _guess_pmids_for_extract(extract: str, abstracts: list) -> list:
    """
    Improved robust matching for LLM 'Supporting Extract'
    Handles paraphrases, truncated quotes, grammatical variation.
    """

    if not extract or not abstracts:
        return []

    extract_norm = normalize_text(extract)
    if not extract_norm:
        return []

    best_scores = []
    for doc in abstracts:
        pmid = str(doc.get("pmid", "")).strip()
        text = (doc.get("title", "") + " " + doc.get("abstract", ""))

        score = hybrid_similarity(extract, text)
        best_scores.append((pmid, score))

    # Sort by best match
    best_scores.sort(key=lambda x: x[1], reverse=True)

    # Highest score
    top_pmid, top_score = best_scores[0]

    # Threshold: paraphrased quotes usually score 0.45 - 0.75
    if top_score >= 0.40:
        return [top_pmid]

    return []

def _correct_extracted_pmids_for_phenotype(
    phenotype: str,
    entries: List[dict],
    extracted_dir: str,
) -> List[dict]:
    """
    For a given phenotype:
      - Load its abstracts
      - For each extracted entry, recompute PMIDS from the abstract file
        using the Source Reference (if present)
      - Update the JSON file on disk.
    """
    abstracts = _load_phenotype_abstracts(phenotype)
    if not abstracts:
        return entries

    changed = False
    for e in entries:
        # Prefer Source Reference; fallback to Supporting Extract
        extract = e.get("Source Reference") or e.get("Supporting Extract") or ""
        new_pmids = _guess_pmids_for_extract(extract, abstracts)
        if new_pmids:
            old_pmids = _normalize_pmids(e.get("PMID") or e.get("PMIDS"))
            new_pmids = _unique_list(new_pmids + old_pmids)  # keep any old if useful
            if new_pmids != old_pmids:
                e["PMIDS"] = new_pmids
                e.pop("PMID", None)
                changed = True

    # If something changed, write back to the extracted JSON file
    if changed:
        out_path = os.path.join(extracted_dir, f"{phenotype}.json")
        try:
            with open(out_path, "w") as f:
                json.dump(entries, f, indent=2)
            print(f"🔄 Corrected PMIDs for {phenotype} and updated {out_path}")
        except Exception as e:
            print(f"⚠️ Failed to rewrite extracted JSON for {phenotype}: {e}")

    return entries


# ============================================================
# 1. LOAD EXTRACTED GENES (LLM outputs)
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

            # Tag and correct PMIDs using abstracts   *** CHANGED ***
            for d in data:
                d.setdefault("Source", "Extracted")
            # data = _correct_extracted_pmids_for_phenotype(pheno_name, data, extracted_dir)

            pheno_to_extracted[pheno_name] = data
        except Exception as e:
            print(f"⚠️ Could not read extracted file {fpath}: {e}")
    return pheno_to_extracted


# ============================================================
# 2. LOAD VERIFIED GENES (unchanged)
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
# 3. MERGE BOTH SOURCES (now merges duplicate extracted PMIDs) *** CHANGED ***
# ============================================================
def merge_extracted_and_verified(
    extracted: Dict[str, List[dict]],
    verified: Dict[str, List[dict]],
) -> Dict[str, List[dict]]:
    all_phenos = set(extracted.keys()) & set(verified.keys())
    merged: Dict[str, List[dict]] = {}

    for pheno in all_phenos:
        merged_by_gene: Dict[str, dict] = {}

        # add extracted first (merge duplicates by gene)
        for entry in extracted.get(pheno, []):
            gene = entry.get("Gene")
            if not gene:
                continue

            e_pmids = _normalize_pmids(entry.get("PMID") or entry.get("PMIDS"))
            e_ref = entry.get("Source Reference", "")
            e_journal = entry.get("Journal", "")

            if gene in merged_by_gene:
                # already have this gene from another extracted entry
                existing = merged_by_gene[gene]
                existing["PMIDS"] = _unique_list(existing.get("PMIDS", []) + e_pmids)
                if not existing.get("Source Reference") and e_ref:
                    existing["Source Reference"] = e_ref
                if not existing.get("Journal") and e_journal:
                    existing["Journal"] = e_journal
                if existing.get("Source") == "Verified":
                    existing["Source"] = "Both"
                elif existing.get("Source") == "Extracted":
                    existing["Source"] = "Extracted"  # stays Extracted for now
            else:
                merged_by_gene[gene] = {
                    "Gene": gene,
                    "Source": "Extracted",
                    "Source Reference": e_ref,
                    "Journal": e_journal,
                    "PMIDS": e_pmids,
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
                existing = merged_by_gene[gene]
                existing["Source"] = "Both"
                existing["PMIDS"] = _unique_list(existing.get("PMIDS", []) + v_pmids)
                if v_extract:
                    existing["Source Reference"] = v_extract
                if v_journal:
                    existing["Journal"] = v_journal
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


# ============================================================
# 4. BUILD GMTs from merged data (map first, then keep only mapped)
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
            # collect unique gene symbols
            symbols = sorted({e["Gene"] for e in entries if e.get("Gene")})
            if not symbols:
                continue

            # map to entrez FIRST                   *** CHANGED ***
            mapped_ids, valid_syms, invalid_syms = id_mapping(symbols, mode="entrezgene")

            if invalid_syms:
                unmapped_per_pheno.setdefault(phenotype, []).extend(invalid_syms)

            # build symbol -> entrez map based on successful mappings
            sym_to_entrez = {sym: str(eid) for sym, eid in zip(valid_syms, mapped_ids)}

            if not sym_to_entrez:
                continue  # nothing mapped, skip this phenotype entirely

            # Only keep successfully mapped symbols in BOTH GMTs
            mapped_symbols = sorted(sym_to_entrez.keys())
            entrez_ids = [sym_to_entrez[s] for s in mapped_symbols]

            # symbols GMT line (symbols that have an Entrez ID)
            f_sym.write(
                phenotype
                + "\t"
                + "combined extracted+verified (symbols mapped to Entrez)"
                + "\t"
                + "\t".join(mapped_symbols)
                + "\n"
            )

            # entrez GMT line
            f_ent.write(
                phenotype
                + "\t"
                + "combined extracted+verified (entrez)"
                + "\t"
                + "\t".join(entrez_ids)
                + "\n"
            )

    return unmapped_per_pheno


# ============================================================
# 5. HTML SUMMARY (show full extract, keep PubMed links)
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
    /* Show full text, no ellipsis                 *** CHANGED *** */
    table.dataTable td {{
      white-space: normal;
      word-wrap: break-word;
      max-width: none;
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
    # CHANGE THESE TO YOUR REAL PATHS
    extracted_dir = "out/phenotype_generations/deepseek-r1:8b"
    verified_dir = "out/phenotype_checks/deepseek-r1:8b"
    out_dir = "out/genesets/deepseek"
    os.makedirs(out_dir, exist_ok=True)

    # 1) load both sources (extracted first, with PMID correction)
    extracted = load_extracted_genes(extracted_dir)
    verified = load_verified_genes(verified_dir)

    # 2) merge
    merged = merge_extracted_and_verified(extracted, verified)

    # 3) build GMTs (symbols + entrez, symbols only for successfully mapped genes)
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
