from utils import phenotype_json_reader
from rag_pipeline_consolidated import create_control_flow
import os

PROCESSED_FILE = "out/processed_phenotypes_qwen.txt"

def load_processed():
    """Load processed phenotype names from file."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def mark_processed(phenotype_name):
    """Append a processed phenotype to the file."""
    with open(PROCESSED_FILE, "a") as f:
        f.write(f"{phenotype_name}\n")

def main():
    phenotype_json_file = "out/only_in_db_p2g_details.json"
    phenotypes = phenotype_json_reader(phenotype_json_file)

    # Load already processed phenotypes
    processed = load_processed()
    to_process = [p for p in phenotypes if p["name"] not in processed]

    print(f"Total phenotypes: {len(phenotypes)}")
    print(f"Already processed: {len(processed)}")
    print(f"Remaining to process: {len(to_process)}")

    if not to_process:
        print("All phenotypes already processed. Nothing to do.")
        return

    # Sequential processing
    for phenotype in to_process:
        name = phenotype["name"]
        print(f"\nProcessing phenotype: {name}")

        try:
            graph = create_control_flow()
            inputs = {"phenotype": phenotype}

            # Stream through events but we ignore them
            for _ in graph.stream(inputs, stream_mode="values"):
                pass

            # Mark phenotype as processed
            mark_processed(name)
            print(f"✅ Finished phenotype: {name}")

        except Exception as e:
            print(f"❌ Error processing {name}: {e}")

    print("\n✅ All phenotypes processed. Progress saved in processed_phenotypes.txt")


if __name__ == "__main__":
    main()
