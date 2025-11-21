import os
import re
import json
import argparse


def clean_repetitions(text):
    text = re.sub(r"\s+", " ", text.strip())
    chunks = re.split(r"}\s*{", text)

    seen = set()
    cleaned = []

    for ch in chunks:
        norm = ch.strip().lower()
        if norm not in seen:
            seen.add(norm)
            cleaned.append(ch.strip())

    joined = "},\n{".join(cleaned)
    return "{" + joined + "}" if not joined.startswith("{") else joined


def repair_json_structure(raw_text):
    cleaned = re.sub(r"[\x00-\x1f]+", "", raw_text).strip()

    if not cleaned.startswith("["):
        cleaned = "[" + cleaned
    if not cleaned.endswith("]"):
        cleaned = cleaned.rstrip(",") + "]"

    if cleaned.count("{") > cleaned.count("}"):
        cleaned += "}" * (cleaned.count("{") - cleaned.count("}"))
    if cleaned.count("[") > cleaned.count("]"):
        cleaned += "]" * (cleaned.count("[") - cleaned.count("]"))

    return cleaned


def format_raw_files(input_dir):
    for fname in os.listdir(input_dir):
        if not fname.endswith("_raw.txt"):
            continue

        path = os.path.join(input_dir, fname)
        print(f"Formatting raw file: {fname}")

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        # Step 1: remove repeated chunks
        cleaned_text = clean_repetitions(raw)

        # Step 2: repair JSON structure
        cleaned_text = repair_json_structure(cleaned_text)

        # Try to parse
        try:
            data = json.loads(cleaned_text)

            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                data = [data]

            out_path = os.path.join(input_dir, fname.replace("_raw.txt", "_fixed.json"))
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"✔ Saved valid JSON: {out_path}")

        except Exception as e:
            # Save fallback cleaned text
            out_txt = os.path.join(input_dir, fname.replace("_raw.txt", "_cleaned.txt"))
            with open(out_txt, "w", encoding="utf-8") as f:
                f.write(cleaned_text)

            print(f"⚠ Could not fully repair {fname}. Saved cleaned text to {out_txt}")


def extract_json_objects(text):
    pattern = re.compile(r"\{[^{}]+\}")
    matches = pattern.findall(text)

    objs = []
    for m in matches:
        try:
            objs.append(json.loads(m))
        except Exception:
            safe = m.replace("'", '"')
            safe = re.sub(r",\s*}", "}", safe)
            try:
                objs.append(json.loads(safe))
            except:
                continue

    return objs


def repair_flat_json_files(input_dir):
    for fname in os.listdir(input_dir):
        if not fname.endswith("_cleaned.txt"):
            continue

        path = os.path.join(input_dir, fname)
        print(f"Repairing flat JSON: {fname}")

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        objs = extract_json_objects(text)

        seen = set()
        deduped = []
        for obj in objs:
            key = (obj.get("Gene"), obj.get("PMID"))
            if key not in seen:
                seen.add(key)
                deduped.append(obj)

        out_json = path.replace("_cleaned.txt", ".json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(deduped, f, indent=2, ensure_ascii=False)

        print(f"✔ Repaired {len(deduped)} entries → {out_json}")


def delete_temp_files(input_dir):
    deleted = 0
    for fname in os.listdir(input_dir):
        if fname.endswith("_raw.txt") or fname.endswith("_cleaned.txt"):
            try:
                os.remove(os.path.join(input_dir, fname))
                print(f"🗑️ Deleted: {fname}")
                deleted += 1
            except Exception as e:
                print(f"Could not delete {fname}: {e}")

    print(f"\n✔ Done. Deleted {deleted} temp files.")




def main(input_dir):
    print("\nFormat RAW LLM JSON ===")
    format_raw_files(input_dir)

    print("\nRepair Flat JSON ===")
    repair_flat_json_files(input_dir)

    print("\nDelete RAW + CLEANED Files ===")
    delete_temp_files(input_dir)

    print("\nAll LLM outputs repaired and cleaned!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix raw LLM outputs in a directory.")
    parser.add_argument(
        "--dir", type=str,
        required=True,
        help="Directory containing *_raw.txt and *_cleaned.txt files"
    )

    args = parser.parse_args()
    main(args.dir)
