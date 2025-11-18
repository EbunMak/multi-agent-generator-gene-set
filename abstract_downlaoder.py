from pubtator import Pubtator
import os
import time
import json
import requests
import sqlite3


PMIDS_FILE = "abstracts/pubtator/gene2pubtator/updated_pmids.txt"
OUTPUT_DIR = "abstracts/gene_annotated_abstracts"
DB_FILE = "pubtator_local.db"
PROGRESS_FILE = "processed_pmids.txt"
ERROR_LOG = "error_failed_pmids.txt"
REQUEST_DELAY = 0.3
MAX_RETRIES = 5

# ---- Initialize DB ----
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS abstracts (
            pmid TEXT PRIMARY KEY,
            title TEXT,
            journal TEXT,
            abstract TEXT,
            genes TEXT
        )
    """)
    conn.commit()
    return conn

# ---- Save one abstract ----
def save_abstract(conn, data):
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO abstracts (pmid, title, journal, abstract, genes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["pmid"],
        data.get("title"),
        data.get("journal"),
        data.get("abstract"),
        json.dumps(data.get("genes", []))
    ))
    conn.commit()

# ---- Check if PMID already exists ----
def is_downloaded(conn, pmid):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM abstracts WHERE pmid = ?", (pmid,))
    return cur.fetchone() is not None

# ---- Retrieve one abstract ----
def get_abstract(conn, pmid):
    cur = conn.cursor()
    cur.execute("SELECT * FROM abstracts WHERE pmid = ?", (pmid,))
    row = cur.fetchone()
    if row:
        return {
            "pmid": row[0],
            "title": row[1],
            "journal": row[2],
            "abstract": row[3],
            "genes": json.loads(row[4])
        }
    return None

# ---- Main download loop with resume ----
def download_abstracts():
    conn = init_db()

    if not os.path.exists(PMIDS_FILE):
        print(f"PMID list file {PMIDS_FILE} not found.")
        return

    with open(PMIDS_FILE, "r") as f:
        pmids = [line.strip() for line in f if line.strip()]

    total_pmids = len(pmids)
    print(f"Total PMIDs to process: {total_pmids}")

    for i, pmid in enumerate(pmids, start=1):
        if is_downloaded(conn, pmid):
            print(f"[{i}/{total_pmids}] PMID {pmid} already downloaded. Skipping.")
            continue

        try:
            data = Pubtator.export_abstract(pmid)
            if data:
                save_abstract(conn, data)
                print(f"[{i}/{total_pmids}] Saved PMID {pmid} with {len(data.get('genes', []))} genes")
            else:
                print(f"[{i}/{total_pmids}] PMID {pmid} has no gene annotations. Skipping.")

        except Exception as e:
            print(f"[{i}/{total_pmids}] ❌ Error for PMID {pmid}: {e}")

        # time.sleep(REQUEST_DELAY)

    conn.close()
    print("✅ All done! Downloaded abstracts are in", DB_FILE)

# ---- Example usage ----
if __name__ == "__main__":
    download_abstracts()