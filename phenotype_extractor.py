import json
import os
import time
import requests


API_SEARCH_URL = "https://ontology.jax.org/api/hp/search?q="
API_TERM_URL = "https://ontology.jax.org/api/hp/terms/"

session = requests.Session()

# format hpo db name into a readable name
def format_query(term: str):
    return term.replace("HP_", "").replace("_", " ").strip().title()

# fetch HPO term details
def fetch_hpo_term(hpo_id):
    encoded = hpo_id.replace(":", "%3A")
    try:
        resp = session.get(f"{API_TERM_URL}{encoded}", timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": hpo_id,
            "name": data.get("name"),
            "description": data.get("definition"),
            "synonyms": data.get("synonyms", [])
        }
    except Exception as e:
        print(f"Error fetching full term for {hpo_id}: {e}")
        return None


def extract_phenotype_details(phenotype_name: str, output_file: str):
    # Load existing results
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = []

    existing_by_name = {entry.get("name", "").lower(): entry for entry in results}

    formatted_query = format_query(phenotype_name)

    # Check if already extracted
    if formatted_query.lower() in existing_by_name:
        return existing_by_name[formatted_query.lower()]

    # Search API
    try:
        search_resp = session.get(f"{API_SEARCH_URL}{formatted_query}&page=0&limit=1", timeout=20)
        search_resp.raise_for_status()
        search_data = search_resp.json()

        if "terms" in search_data and search_data["terms"]:
            term_info = search_data["terms"][0]
            term_id = term_info.get("id")

            # Fetch full term details
            full_details = fetch_hpo_term(term_id)
            if full_details:
                results.append(full_details)
                print(f"Found: {full_details['name']} ({full_details['id']})")
        else:
            print(f"No match for {phenotype_name}")

    except Exception as e:
        print(f"API error: {e}")

    # Save after each entry
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Politeness delay
    time.sleep(0.25)


# Example usage:
phenotype_list = []
for phenotype in phenotype_list:
    extract_phenotype_details(phenotype, "out/phenotype_details.json")