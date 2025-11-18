import os
import json
import re

def clean_repetitions(text):
    """
    Removes repeated chunks (e.g., same JSON sequence or gene entry repeated multiple times).
    """
    # Normalize spacing
    text = re.sub(r"\s+", " ", text.strip())

    # Split by closing braces assuming JSON-like chunks
    chunks = re.split(r"}\s*{", text)
    seen = set()
    cleaned = []

    for ch in chunks:
        chunk_norm = ch.strip().lower()
        if chunk_norm not in seen:
            seen.add(chunk_norm)
            cleaned.append(ch.strip())

    cleaned_text = "},\n{".join(cleaned)
    return "{" + cleaned_text + "}" if not cleaned_text.startswith("{") else cleaned_text


def repair_json_structure(raw_text):
    """
    Attempts to repair incomplete or malformed JSON text.
    """
    # Remove any invalid trailing characters
    cleaned = re.sub(r"[\x00-\x1f]+", "", raw_text)
    cleaned = cleaned.strip()

    # Ensure proper JSON array formatting
    if not cleaned.startswith("["):
        cleaned = "[" + cleaned
    if not cleaned.endswith("]"):
        cleaned = cleaned.rstrip(",") + "]"

    # Balance braces/brackets
    if cleaned.count("{") > cleaned.count("}"):
        cleaned += "}" * (cleaned.count("{") - cleaned.count("}"))
    if cleaned.count("[") > cleaned.count("]"):
        cleaned += "]" * (cleaned.count("[") - cleaned.count("]"))

    return cleaned


def process_directory(input_dir):
    """
    Processes all .txt files in the input directory and converts them to JSON.
    """
    for fname in os.listdir(input_dir):
        if not fname.endswith("_raw.txt"):
            continue

        path = os.path.join(input_dir, fname)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        print(f"Processing {fname}...")

        # Step 1: Remove repetitions
        cleaned_text = clean_repetitions(raw_text)

        # Step 2: Repair structure
        cleaned_text = repair_json_structure(cleaned_text)

        # Step 3: Try to parse as JSON
        try:
            data = json.loads(cleaned_text)
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                data = [data]
            
            # Write JSON output
            out_path = os.path.join(input_dir, fname.replace("_raw.txt", "_fixed.json"))
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved valid JSON: {out_path}")

        except Exception as e:
            # Save fallback cleaned text if still broken
            fallback = os.path.join(input_dir, fname.replace("_raw.txt", "_cleaned.txt"))
            with open(fallback, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            print(f"⚠️ Could not parse {fname} to JSON ({e}). Saved cleaned text to {fallback}")


if __name__ == "__main__":
    input_dir = "out/phenotype_generations/deepseek-r1:8b"  # e.g. "out/phenotype_generations_raw"
    process_directory(input_dir)
