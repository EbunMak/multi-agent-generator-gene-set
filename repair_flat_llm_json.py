import os
import re
import json

def extract_json_objects(text):
    """
    Extract JSON-like dicts from messy LLM output text.
    """
    pattern = re.compile(r"\{[^{}]+\}")
    matches = pattern.findall(text)
    objects = []
    for m in matches:
        try:
            obj = json.loads(m)
            objects.append(obj)
        except:
            # Try soft fix for single quotes or missing commas
            safe = m.replace("'", '"')
            safe = re.sub(r",\s*}", "}", safe)
            try:
                obj = json.loads(safe)
                objects.append(obj)
            except:
                continue
    return objects


def repair_file(file_path):
    """
    Repair a single raw .txt file -> valid JSON array.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    objs = extract_json_objects(text)

    # Deduplicate by Gene + PMID if available
    seen = set()
    deduped = []
    for obj in objs:
        key = (obj.get("Gene"), obj.get("PMID"))
        if key not in seen:
            seen.add(key)
            deduped.append(obj)

    out_json = file_path.replace("_cleaned.txt", ".json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"✅ Repaired {len(deduped)} entries saved to {out_json}")


def process_directory(input_dir):
    for fname in os.listdir(input_dir):
        if fname.endswith("_cleaned.txt"):
            repair_file(os.path.join(input_dir, fname))


if __name__ == "__main__":
    input_dir = "out/phenotype_generations/deepseek-r1:8b"  # e.g. "out/phenotype_generations_raw"
    process_directory(input_dir)
