import os

def delete_raw_and_clean_txt(directory):
    """
    Deletes all *_raw.txt and *_cleaned.txt files in the specified directory.
    """
    deleted = 0
    for fname in os.listdir(directory):
        if fname.endswith("_raw.txt") or fname.endswith("_cleaned.txt"):
            path = os.path.join(directory, fname)
            try:
                os.remove(path)
                print(f"🗑️ Deleted: {fname}")
                deleted += 1
            except Exception as e:
                print(f"⚠️ Could not delete {fname}: {e}")
    print(f"\n✅ Done. Deleted {deleted} files from {directory}")

if __name__ == "__main__":
    dir_path = "out/phenotype_generations/qwen3:32b"  # e.g. "out/phenotype_generations_raw"
    delete_raw_and_clean_txt(dir_path)
