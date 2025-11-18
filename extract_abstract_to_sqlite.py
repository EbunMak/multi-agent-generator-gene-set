import os
import sqlite3
import xml.etree.ElementTree as ET

# Load PMIDs with gene annotations
pmid_set = set()
with open('abstracts/pubtator/gene2pubtator/pmids.txt') as pidf:
    for line in pidf:
        pmid_set.add(line.strip())

# SQLite DB setup
db = 'pubtator_gene_abstracts.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS abstracts (
        pmid TEXT PRIMARY KEY,
        title TEXT,
        journal TEXT,
        abstract TEXT,
        genes TEXT
    )
''')

input_dir = 'biocxml_extracted/output/BioCXML'  # Path to extracted XML files

for fname in os.listdir(input_dir):
    if not fname.endswith('.XML'):
        continue

    tree = ET.parse(os.path.join(input_dir, fname))
    root = tree.getroot()
    
    # Iterate over each document in the collection
    for doc in root.findall('document'):
        pmid = doc.findtext('id')
        if pmid not in pmid_set:
            continue

        title, abstract, journal, genes = "", "", "", set()
        
        # Parse passages inside the document
        for passage in doc.findall('passage'):
            ptype = passage.findtext("infon[@key='type']")
            if ptype == 'title':
                title = passage.findtext("text") or ''
            elif ptype == 'abstract':
                abstract = passage.findtext("text") or ''
                # Journal info sometimes in infons
                for infon in passage.findall("infon"):
                    if infon.attrib.get("key") == "journal":
                        journal = infon.text or ''
            for annotation in passage.findall("annotation"):
                for infon in annotation.findall("infon"):
                    if infon.attrib.get("key") == "type" and infon.text == "Gene":
                        genes.add(annotation.findtext("text"))
        
        genes_str = "|".join(genes)
        
        cur.execute(
            "INSERT OR IGNORE INTO abstracts VALUES (?, ?, ?, ?, ?)",
            (pmid, title, journal, abstract, genes_str)
        )
        
        print(f"Inserted PMID: {pmid}")
        print(f"  Title: {title[:100]}")  # print first 100 chars of title
        print(f"  Journal: {journal}")
        print(f"  Genes: {genes_str}")
        print("---")

conn.commit()
conn.close()
