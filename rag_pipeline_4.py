import time
from langgraph.graph import END
from langgraph.graph import StateGraph
from pubtator import Pubtator
from utils import GraphState, get_llm, get_llm_json_mode, clean_model_output, check_is_gene_annotated, save_to_json_list
from langchain_core.messages import HumanMessage, SystemMessage
from instructs import rag_prompt,grade_abstracts_instructions
import json 
import os
from typing import Dict, Any
import asyncio

CHECKED_PMIDS_FILE = "checked_pmids.json"
PMIDS_FILE = "abstracts/pubtator/gene2pubtator/pmids.txt"

with open(PMIDS_FILE, "r") as f:
    ga_pmids = list({int(line.strip()) for line in f if line.strip()} ) # set

def retrieve_pubtator_abstracts(state: GraphState):
    phenotype = state["phenotype"]

    # Build free-text query from phenotype details
    query = phenotype["name"].strip()

    # Load previously checked PMIDs
    if os.path.exists(CHECKED_PMIDS_FILE):
        with open(CHECKED_PMIDS_FILE, "r") as f:
            checked_pmids = json.load(f)
    else:
        checked_pmids = {}

    # Search PubTator (returns PMIDs)
    pmids = Pubtator.search_pubtator_ID(query=query)

    print(f"Initially {len(pmids)} abstracts .... ")
    pmids = check_is_gene_annotated(pmids, ga_pmids)

    print(f"Attempting to extract {len(pmids)} abstracts .... ")

    abstracts = []
    MAX_REQUESTS_PER_SECOND = 3
    DELAY = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.333... seconds
    for pmid in pmids:
        # Skip PMIDs already known to have no gene annotations
        if str(pmid) in checked_pmids and not checked_pmids[str(pmid)]["has_genes"]:
            print(f"Skipping PMID {pmid}: previously found no genes.")
            continue

        try:
            abs_data = Pubtator.export_abstract(pmid)
            has_genes = abs_data is not None

            # Store the check result
            checked_pmids[str(pmid)] = {"has_genes": has_genes}

            if has_genes:
                abstracts.append(abs_data)
            else:
                print(f"Skipped PMID {pmid}: No gene annotations found.")

            # 🕒 Rate limit — wait a bit before the next request
            time.sleep(DELAY)

        except Exception as e:
            print(f"⚠️ Failed to fetch PMID {pmid}: {e}")
            # still wait a bit even on failure to be polite to the API
            time.sleep(DELAY)

    # Save checked PMIDs back to file
    with open(CHECKED_PMIDS_FILE, "w") as f:
        json.dump(checked_pmids, f, indent=2)

    # Store results in state
    save_to_json_list(abstracts, "abstracts/gene_annotated_abstracts/"+query)
    return {"documents": abstracts}


def grade_abstracts(state, llm_name):
    print("---CHECK ABSTRACT RELEVANCE---")

    phenotype = state["phenotype"]
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in phenotype["name"])
    infile = f"abstracts/gene_annotated_abstracts/{safe_name}.json"

    if not os.path.exists(infile):
        print(f"⚠️ No abstracts file found for {safe_name}")
        return {f"documents_{llm_name}": []}

    with open(infile, "r") as f:
        documents = json.load(f)

    question = (
        f"Is this abstract relevant to the phenotype '{phenotype['name']}', defined as "
        f"'{phenotype.get('definition', 'N/A')}', or its synonyms: "
        f"{', '.join(phenotype.get('synonyms', [])) if phenotype.get('synonyms') else 'None'}?"
    )

    llm = get_llm_json_mode(llm_name)
    filtered = []

    for doc in documents:
        abstract_text = (
            f"Title: {doc.get('title','')}\n"
            f"Journal: {doc.get('journal','')}\n"
            f"Abstract: {doc.get('abstract','')}"
        )

        result = llm.invoke([
            SystemMessage(content=grade_abstracts_instructions),
            HumanMessage(content=f"Question: {question}\n\nAbstract:\n{abstract_text}")
        ])

        try:
            grade = json.loads(result.content)["binary_score"].strip().lower()
        except:
            continue

        if grade == "yes":
            filtered.append(doc)

    outfile = f"abstracts/gene_annotated_abstracts/{safe_name}__filtered_{llm_name}.json"
    with open(outfile, "w") as f:
        json.dump(filtered, f, indent=2)

    print(f"✅ Saved filtered abstracts to {outfile}")
    return {f"documents_{llm_name}": filtered}

def generate(state, llm_name):
    print("---GENERATE---")

    phenotype = state["phenotype"]
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in phenotype["name"])

    infile = f"abstracts/gene_annotated_abstracts/{safe_name}__filtered_{llm_name}.json"
    if not os.path.exists(infile):
        print(f"⚠️ No filtered abstracts for {llm_name}, skipping.")
        return {f"generation_{llm_name}": []}

    with open(infile, "r") as f:
        documents = json.load(f)

    question = (
        f"Identify genes associated with phenotype '{phenotype['name']}', "
        f"definition: '{phenotype.get('definition','N/A')}'."
    )

    formatted_docs = [
        f"PMID: {d.get('pmid')}\nTitle: {d.get('title')}\nJournal: {d.get('journal')}\nAbstract: {d.get('abstract')}"
        for d in documents
    ]
    context_text = "\n\n".join(formatted_docs)

    llm = get_llm(llm_name)

    messages = [
        SystemMessage(content="You are a precise biomedical text mining assistant. Respond only in JSON."),
        HumanMessage(content=rag_prompt.format(context=context_text, question=question))
    ]
    result = llm.invoke(messages)
    raw_output = result.content.strip()

    try:
        generation = json.loads(raw_output)
    except:
        generation = json.loads(clean_model_output(raw_output))

    out_dir = f"out/phenotype_generations/{llm_name}"
    os.makedirs(out_dir, exist_ok=True)
    outfile = f"{out_dir}/{safe_name}.json"
    with open(outfile, "w") as f:
        json.dump(generation, f, indent=2)
    print(f"✅ Saved generation to {outfile}")

    # ✅ Remove phenotype abstracts after model finished
    original_abstract_file = f"abstracts/gene_annotated_abstracts/{safe_name}.json"
    if os.path.exists(original_abstract_file):
        os.remove(original_abstract_file)
        print(f"🗑️ Removed {original_abstract_file}")

    return {f"generation_{llm_name}": generation}



def create_control_flow():
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve_pubtator_abstracts)

    # workflow.add_node("grade_qwen",   lambda s: grade_abstracts(s, "qwen2.5:7b"))
    # workflow.add_node("grade_ds",     lambda s: grade_abstracts(s, "deepseek-r1:7b"))
    # workflow.add_node("grade_llama",  lambda s: grade_abstracts(s, "llama3.1:8b"))

    # workflow.add_node("gen_qwen",   lambda s: generate(s, "qwen2.5:7b"))
    # workflow.add_node("gen_ds",     lambda s: generate(s, "deepseek-r1:7b"))
    # workflow.add_node("gen_llama",  lambda s: generate(s, "llama3.1:8b"))

    workflow.set_entry_point("retrieve")

    # workflow.add_edge("retrieve", "grade_qwen")
    # workflow.add_edge("retrieve", "grade_ds")
    # workflow.add_edge("retrieve", "grade_llama")

    # workflow.add_edge("grade_qwen", "gen_qwen")
    # workflow.add_edge("grade_ds", "gen_ds")
    # workflow.add_edge("grade_llama", "gen_llama")

    # workflow.add_edge("gen_qwen", END)
    # workflow.add_edge("gen_ds", END)
    # workflow.add_edge("gen_llama", END)
    workflow.add_edge("retrieve", END)

    return workflow.compile()
