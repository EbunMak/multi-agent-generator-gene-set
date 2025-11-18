from utils import phenotype_json_reader
from rag_pipeline_consolidated import create_control_flow
from concurrent.futures import ThreadPoolExecutor
import threading
import os

# Thread-safe print
thread_print_lock = threading.Lock()

PROCESSED_FILE = "out/processed_phenotypes.txt"
MAX_WORKERS = 1  # number of phenotypes to run in parallel


def load_processed():
    """Load processed phenotypes from file."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def mark_processed(phenotype_name):
    """Append phenotype name to processed file."""
    with open(PROCESSED_FILE, "a") as f:
        f.write(f"{phenotype_name}\n")


def process_phenotype(phenotype):
    name = phenotype["name"]

    with thread_print_lock:
        print(f"\nStarting phenotype: {name}")

    try:
        graph = create_control_flow()
        inputs = {"phenotype": phenotype}

        # Run the pipeline but ignore intermediate stream events
        for _ in graph.stream(inputs, stream_mode="values"):
            pass

        # Mark as processed
        mark_processed(name)

        with thread_print_lock:
            print(f"✅ Finished phenotype: {name}")

    except Exception as e:
        with thread_print_lock:
            print(f"❌ Error processing {name}: {str(e)}")


def main():
    phenotype_json_file = "out/phenotype_data_clean.json"
    phenotypes = phenotype_json_reader(phenotype_json_file)

    # Load list of completed phenotypes
    processed = load_processed()
    to_process = [p for p in phenotypes if p["name"] not in processed]

    print(f"Total phenotypes: {len(phenotypes)}")
    print(f"Already processed: {len(processed)}")
    print(f"Remaining to process: {len(to_process)}")

    if not to_process:
        print("All phenotypes already processed. Nothing to do.")
        return

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(process_phenotype, to_process)

    print("\nDone! Progress saved in processed_phenotypes.txt")


if __name__ == "__main__":
    main()
