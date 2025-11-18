import time
from langgraph.graph import END
from langgraph.graph import StateGraph
from pubtator import Pubtator
from utils import GraphState, get_llm, get_llm_json_mode, clean_model_output, check_is_gene_annotated, save_to_json_list
from langchain_core.messages import HumanMessage, SystemMessage
from instructs import rag_prompt2, grade_abstracts_instructions2
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
    query = phenotype["name"].strip()
    gene = phenotype["gene"].strip()

    # Retrieve 10 abstracts directly
    pmids = Pubtator.search_pubtator_ID(relation=f"@GENE_{gene} AND {query}", limit=1)
    print(f"Fetched {len(pmids)} PMIDs for {gene} and {query}")

    abstracts = []
    for pmid in pmids:
        try:
            abs_data = Pubtator.export_abstract(pmid, check_for_genes=False)
            if abs_data:
                abstracts.append(abs_data)
        except Exception as e:
            print(f"⚠️ Error fetching PMID {pmid}: {e}")
    save_to_json_list(abstracts, f"abstracts/gene_related_abstracts/{query}_{gene}")
    return {"documents": abstracts}


def grade_abstracts(state, llm_name):
    phenotype = state["phenotype"]
    gene = phenotype["gene"]
    safe_name = f"{phenotype['name']}_{gene}"
    infile = f"abstracts/gene_related_abstracts/{safe_name}"

    if not os.path.exists(infile):
        print(f"⚠️ No abstracts found for {safe_name}")
        return {f"documents_{llm_name}": []}

    with open(infile, "r") as f:
        documents = json.load(f)

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
        except:
            continue

    outfile = f"abstracts/gene_related_abstracts/{safe_name}__filtered_{llm_name}.json"
    with open(outfile, "w") as f:
        json.dump(filtered, f, indent=2)
    print(f"✅ Saved filtered abstracts to {outfile}")
    return {f"documents_{llm_name}": filtered}


def generate(state, llm_name):
    phenotype = state["phenotype"]
    gene = phenotype["gene"]
    safe_name = f"{phenotype['name']}_{gene}"

    infile = f"abstracts/gene_related_abstracts/{safe_name}__filtered_{llm_name}.json"
    if not os.path.exists(infile):
        print(f"⚠️ No filtered abstracts for {safe_name}")
        return {f"generation_{llm_name}": []}

    with open(infile, "r") as f:
        documents = json.load(f)

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
    except:
        generation = json.loads(clean_model_output(result.content))
    generation["PMIDS"] = pmids

    outfile = f"out/phenotype_checks/{llm_name}/{phenotype['name']}/{gene}.json"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w") as f:
        json.dump(generation, f, indent=2)
    print(f"✅ Saved generation for {gene} and {phenotype['name']} to {outfile}")

    # ✅ Remove phenotype abstracts after model finished
    filtered_abstract_file = f"abstracts/gene_related_abstracts/{safe_name}__filtered_{llm_name}.json"
    if os.path.exists(filtered_abstract_file):
        os.remove(filtered_abstract_file)
        print(f"🗑️ Removed {filtered_abstract_file}")

    return {f"generation_{llm_name}": generation}




from langgraph.graph import StateGraph, END

def create_control_flow():
    workflow = StateGraph(GraphState)

    # Step 1: Retrieve abstracts
    workflow.add_node("retrieve", retrieve_pubtator_abstracts)

    # Step 2: Grade abstracts for phenotype + gene relevance using llama
    workflow.add_node("grade_ds", lambda s: grade_abstracts(s, "llama3.1:8b"))

    # Step 3: Generate inference (validate gene–phenotype association)
    workflow.add_node("gen_ds", lambda s: generate(s, "llama3.1:8b"))

    # Define workflow structure
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_ds")
    workflow.add_edge("grade_ds", "gen_ds")
    workflow.add_edge("gen_ds", END)

    return workflow.compile()
