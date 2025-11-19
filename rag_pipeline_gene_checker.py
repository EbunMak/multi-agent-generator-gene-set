import time
from langgraph.graph import END
from langgraph.graph import StateGraph
from pubtator import Pubtator
from utils import GraphState, get_llm, get_llm_json_mode, clean_model_output, save_to_json_list
from langchain_core.messages import HumanMessage, SystemMessage
from instructs import rag_prompt2, grade_abstracts_instructions2
import json
import os

CHECKED_PMIDS_FILE = "checked_pmids_gene_checker.json"  # optional cache if you want

def retrieve_pubtator_abstracts(state: GraphState):
    """
    Retrieve abstracts for a given phenotype + gene.
    - If cached abstracts exist, load them from disk.
    - Otherwise, query PubTator, save the raw abstracts once, and return them.
    """
    phenotype = state["phenotype"]
    query = phenotype["name"].strip()
    gene = phenotype["gene"].strip()

    base_dir = "abstracts/gene_related_abstracts"
    os.makedirs(base_dir, exist_ok=True)
    cache_file = os.path.join(base_dir, f"{query}_{gene}.json")

    # If cached, just load and return
    if os.path.exists(cache_file):
        print(f"Loading cached abstracts for {query} / {gene}")
        with open(cache_file, "r") as f:
            abstracts = json.load(f)
        return {"documents": abstracts}

    # Else: query PubTator directly
    pmids = Pubtator.search_pubtator_ID(relation=f"@GENE_{gene} AND {query}", limit=1)
    print(f"Fetched {len(pmids)} PMIDs for {gene} and {query}")

    abstracts = []
    for pmid in pmids:
        try:
            abs_data = Pubtator.export_abstract(pmid, check_for_genes=False)
            if abs_data:
                abstracts.append(abs_data)
        except Exception as e:
            print(f"Error fetching PMID {pmid}: {e}")

    # Save raw abstracts once
    save_to_json_list(abstracts, cache_file)
    print(f"Saved {len(abstracts)} abstracts to {cache_file}")

    return {"documents": abstracts}


def grade_abstracts(state, llm_name):
    """
    Grade abstracts for phenotype+gene relevance using ONLY abstracts passed in state["documents"].
    No file I/O for abstracts here.
    """
    phenotype = state["phenotype"]
    gene = phenotype["gene"]

    documents = state.get("documents", [])
    if not documents:
        print(f"No abstracts to grade for {phenotype['name']} / {gene}")
        return {f"documents_{llm_name}": []}

    question = (
        f"Does this abstract discuss BOTH the gene '{gene}' "
        f"and the phenotype '{phenotype['name']}' ({phenotype.get('definition', 'N/A')})?"
    )

    llm = get_llm_json_mode(llm_name)
    filtered = []

    for doc in documents:
        abstract_text = (
            f"Title: {doc.get('title', '')}\n"
            f"Abstract: {doc.get('abstract', '')}"
        )
        result = llm.invoke([
            SystemMessage(content=grade_abstracts_instructions2),
            HumanMessage(content=f"Question: {question}\n\nAbstract:\n{abstract_text}")
        ])

        try:
            grade = json.loads(result.content)["binary_score"].strip().lower()
            if grade == "yes":
                filtered.append(doc)
        except Exception as e:
            print(f"Skipping abstract due to parse error: {e}")
            continue

    print(f"Kept {len(filtered)} abstracts after grading for {phenotype['name']} / {gene}")
    return {f"documents_{llm_name}": filtered}


def generate(state, llm_name):
    """
    Use only the filtered abstracts from the grader (state[f"documents_{llm_name}"])
    to decide whether the gene is supported for the phenotype.
    """
    phenotype = state["phenotype"]
    gene = phenotype["gene"]
    safe_name = phenotype["name"]

    documents = state.get(f"documents_{llm_name}", [])
    if not documents:
        print(f"No filtered abstracts for {safe_name} / {gene}")
        return {f"generation_{llm_name}": []}

    pmids = [d.get("pmid") for d in documents]
    formatted_docs = [
        f"PMID: {d.get('pmid')}\nTitle: {d.get('title')}\nJournal: {d.get('journal')}\nAbstract: {d.get('abstract')}"
        for d in documents
    ]
    context = "\n\n".join(formatted_docs)

    question = f"Is gene '{gene}' supported as being associated with phenotype '{phenotype['name']}'?"

    llm = get_llm_json_mode(llm_name)
    result = llm.invoke([
        SystemMessage(content="You are a precise biomedical reasoning model. Respond only in JSON."),
        HumanMessage(content=rag_prompt2.format(context=context, question=question))
    ])

    try:
        generation = json.loads(result.content)
    except Exception:
        generation = json.loads(clean_model_output(result.content))

    generation["PMIDS"] = pmids

    outfile = f"out/phenotype_checks/{llm_name}/{safe_name}/{gene}.json"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w") as f:
        json.dump(generation, f, indent=2)
    print(f"Saved generation for {gene} and {safe_name} to {outfile}")

    return {f"generation_{llm_name}": generation}


def create_control_flow():
    workflow = StateGraph(GraphState)

    # Step 1: Retrieve abstracts
    workflow.add_node("retrieve", retrieve_pubtator_abstracts)

    # Step 2: Grade abstracts for phenotype + gene relevance using llama
    workflow.add_node("grade_llama", lambda s: grade_abstracts(s, "llama3.1:8b"))

    # Step 3: Generate inference (validate gene–phenotype association)
    workflow.add_node("gen_llama", lambda s: generate(s, "llama3.1:8b"))

    # Define workflow structure
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_llama")
    workflow.add_edge("grade_llama", "gen_llama")
    workflow.add_edge("gen_llama", END)

    return workflow.compile()
