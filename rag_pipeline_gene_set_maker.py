import time
from langgraph.graph import END
from langgraph.graph import StateGraph
from pubtator import Pubtator
from utils import GraphState, get_llm, get_llm_json_mode, clean_model_output, check_is_gene_annotated
from langchain_core.messages import HumanMessage, SystemMessage
from instructs import rag_prompt,grade_abstracts_instructions
import json 
import os
import asyncio

CHECKED_PMIDS_FILE = "checked_pmids.json"
PMIDS_FILE = "abstracts/pubtator/gene2pubtator/pmids.txt"

with open(PMIDS_FILE, "r") as f:
    # get PMIDs that are gene-annotated
    ga_pmids = list({int(line.strip()) for line in f if line.strip()} )

def retrieve_pubtator_abstracts(state: GraphState):
    phenotype = state["phenotype"]
    name = phenotype["name"].strip()
    outfile = f"abstracts/gene_annotated_abstracts/{name}.json"

    # If already downloaded, just load and return
    if os.path.exists(outfile):
        print(f"Cached abstracts found for {name}. Loading...")
        with open(outfile, "r") as f:
            return {"documents": json.load(f)}

    # Else: download abstracts as before
    print(f"Downloading abstracts for phenotype: {name}")

    if os.path.exists(CHECKED_PMIDS_FILE):
        with open(CHECKED_PMIDS_FILE, "r") as f:
            checked_pmids = json.load(f)
    else:
        checked_pmids = {}

    pmids = Pubtator.search_pubtator_ID(query=name)
    pmids = check_is_gene_annotated(pmids, ga_pmids)

    abstracts = []
    MAX_REQUESTS_PER_SECOND = 3
    DELAY = 1.0 / MAX_REQUESTS_PER_SECOND

    for pmid in pmids:
        if str(pmid) in checked_pmids and not checked_pmids[str(pmid)]["has_genes"]:
            continue

        try:
            abs_data = Pubtator.export_abstract(pmid)
            has_genes = abs_data is not None
            checked_pmids[str(pmid)] = {"has_genes": has_genes}

            if has_genes:
                abstracts.append(abs_data)

            time.sleep(DELAY)
        except Exception:
            time.sleep(DELAY)
            continue

    # write updated PMIDs file
    with open(CHECKED_PMIDS_FILE, "w") as f:
        json.dump(checked_pmids, f, indent=2)

    # Save ONLY raw abstracts
    os.makedirs("abstracts/gene_annotated_abstracts", exist_ok=True)
    with open(outfile, "w") as f:
        json.dump(abstracts, f, indent=2)

    print(f"Saved {len(abstracts)} abstracts to {outfile}")
    return {"documents": abstracts}



async def grade_abstracts(state, llm_name):
    print("---CHECK ABSTRACT RELEVANCE---")

    phenotype = state["phenotype"]
    documents = state["documents"]  # ← use only state, not disk

    if not documents:
        return {f"documents_{llm_name}": []}

    question = (
        f"Is this abstract relevant to the phenotype '{phenotype['name']}', "
        f"defined as '{phenotype.get('definition', 'N/A')}', or its synonyms: "
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
            if grade == "yes":
                filtered.append(doc)
        except:
            continue

    return {f"documents_{llm_name}": filtered}

def safe_json_loads(raw_output):
    """
    Safely parse LLM output into JSON, attempting to repair common truncation issues.
    """
    import json
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as e:
        print(f"JSON decode failed: {e}")
        partial = raw_output[:e.pos]
        # Try to balance braces/brackets
        if partial.count("{") > partial.count("}"):
            partial += "}"
        if partial.count("[") > partial.count("]"):
            partial += "]"
        try:
            return json.loads(partial)
        except Exception:
            print("Could not recover JSON, returning empty list.")
            return []


async def generate(state, llm_name):
    """
    Generate gene extraction results using only the in-memory filtered abstracts.
    Save:
      - Parsed JSON to out/...
      - Raw model output to *_raw.txt when JSON fails to parse
    """
    print("---GENERATE---")

    phenotype = state["phenotype"]
    safe_name = phenotype["name"]

    # Load filtered abstracts from the graph state
    documents = state.get(f"documents_{llm_name}", [])
    if not documents:
        print(f"No filtered abstracts for {llm_name}")
        return {f"generation_{llm_name}": []}

    # Build question and context
    question = (
        f"Identify genes associated with phenotype '{phenotype['name']}', "
        f"definition: '{phenotype.get('definition','N/A')}'."
    )

    context_text = "\n\n".join([
        f"PMID: {d.get('pmid')}\nTitle: {d.get('title')}\nJournal: {d.get('journal')}\nAbstract: {d.get('abstract')}"
        for d in documents
    ])

    llm = get_llm(llm_name)

    messages = [
        SystemMessage(content="You are a precise biomedical text mining assistant. Respond only in valid JSON."),
        HumanMessage(content=rag_prompt.format(context=context_text, question=question))
    ]

    # Prepare output paths
    out_dir = f"out/phenotype_generations/{llm_name}"
    os.makedirs(out_dir, exist_ok=True)

    json_outfile = f"{out_dir}/{safe_name}.json"
    raw_outfile = f"{out_dir}/{safe_name}_raw.txt"

    # Call LLM and parse JSON
    try:
        result = llm.invoke(messages)
        raw_output = result.content.strip()

        # Try parsing normally
        generation = safe_json_loads(raw_output)

        # If JSON parsing failed
        if not generation:
            print("Invalid or empty JSON. Saving raw model output...")
            with open(raw_outfile, "w") as f:
                f.write(raw_output)

            # Attempt cleanup of brackets
            generation = safe_json_loads(clean_model_output(raw_output))

            if not generation:
                print("Could not parse JSON after cleanup.")

    except Exception as e:
        # Log exception and continue with empty generation
        print(f"LLM invocation error: {e}")
        with open(raw_outfile, "w") as f:
            f.write(str(e))
        generation = []

    # Save parsed JSON (even if it's empty)
    try:
        with open(json_outfile, "w") as f:
            json.dump(generation, f, indent=2)
        print(f"Saved generation JSON to {json_outfile}")
    except Exception as e:
        print(f" Failed writing JSON file for {safe_name}: {e}")
        # As a fallback, store raw output instead
        with open(raw_outfile, "w") as f:
            f.write(raw_output)
        print(f"Wrote raw generation to {raw_outfile}")

    return {f"generation_{llm_name}": generation}


def create_control_flow():

    workflow = StateGraph(GraphState)

    # Helper to run async coroutines synchronously
    def run_async(coro):
        return asyncio.run(coro)

    # Define the nodes
    workflow.add_node("retrieve", retrieve_pubtator_abstracts)  # retrieve
    
    # grade documents wrapped with run_async
    workflow.add_node("grade_qwen", lambda state: run_async(grade_abstracts(state, llm_name="qwen3:32b")))
    workflow.add_node("grade_deepseek", lambda state: run_async(grade_abstracts(state, llm_name="deepseek-r1:8b")))
    workflow.add_node("grade_llama3", lambda state: run_async(grade_abstracts(state, llm_name="llama3.1:8b")))

    # generate nodes wrapped with run_async
    workflow.add_node("generate_qwen", lambda state: run_async(generate(state, llm_name="qwen3:32b")))
    workflow.add_node("generate_deepseek", lambda state: run_async(generate(state, llm_name="deepseek-r1:8b")))
    workflow.add_node("generate_llama3", lambda state: run_async(generate(state, llm_name="llama3.1:8b")))

    # Build graph
    workflow.set_entry_point("retrieve")

    # Run LLMs in parallel AFTER retrieval
    workflow.add_edge("retrieve", "grade_qwen")
    workflow.add_edge("retrieve", "grade_deepseek")
    workflow.add_edge("retrieve", "grade_llama3")

    workflow.add_edge("grade_qwen", "generate_qwen")
    workflow.add_edge("grade_deepseek", "generate_deepseek")
    workflow.add_edge("grade_llama3", "generate_llama3")

    # End after all generations
    workflow.add_edge("generate_qwen", END)
    workflow.add_edge("generate_deepseek", END)
    workflow.add_edge("generate_llama3", END)

    # Compile
    graph = workflow.compile()
    return graph
