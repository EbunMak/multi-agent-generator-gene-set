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


async def grade_abstracts(state, llm_name):
    """
    Grades and filters a list of abstracts based on relevance to a phenotype question.

    Args:
        state (dict): The current LangGraph state. Must contain:
            - "phenotype": dict with keys like 'name' and 'definition'
            - "documents": list of dicts with keys ['pmid', 'title', 'journal', 'abstract']

    Returns:
        dict: Updated state with filtered relevant abstracts under "documents".
    """
    print("---CHECK ABSTRACT RELEVANCE TO PHENOTYPE---")

    phenotype = state["phenotype"]
    documents = state["documents"]

    question = (
        f"Is this abstract relevant to the phenotype '{phenotype['name']}', "
        f"which is defined as '{phenotype.get('definition', 'N/A')}', "
        f"or any of its synonyms: {', '.join(phenotype.get('synonyms', [])) if phenotype.get('synonyms') else 'None'}? "
        f"Please consider abstracts discussing genes, biological processes, or mechanisms related to this phenotype."
    )


    llm = get_llm_json_mode(llm_name)
    filtered_docs = []

    for doc in documents:
        # Build content for grading
        abstract_text = (
            f"Title: {doc.get('title', '')}\n"
            f"Journal: {doc.get('journal', '')}\n"
            f"Abstract: {doc.get('abstract', '')}"
        )

        # Prompt the model
        grader_prompt = f"Question: {question}\n\nAbstract:\n{abstract_text}"
        result = llm.invoke([
            SystemMessage(content=grade_abstracts_instructions),
            HumanMessage(content=grader_prompt)
        ])

        try:
            grade = json.loads(result.content)["binary_score"].strip().lower()
        except Exception as e:
            print(f"Failed to parse LLM result for PMID {doc.get('pmid')}: {e}")
            print(json.loads(result.content))
            continue

        if grade == "yes":
            print(f"✅ PMID {doc.get('pmid')} - RELEVANT")
            filtered_docs.append(doc)
        else:
            print(f"❌ PMID {doc.get('pmid')} - NOT RELEVANT")

    return {"documents_"+llm_name: filtered_docs}

async def generate(state, llm_name):
    """
    Generate gene extraction results using RAG on retrieved PubTator abstracts,
    and store the output to a file.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Updated state with 'generation' key containing parsed LLM output
    """
    print("---GENERATE---")

    phenotype = state["phenotype"]
    documents = state["documents"]
    loop_step = state.get("loop_step", 0)

    # Build the question dynamically from phenotype info
    question = (
        f"Identify genes that may be related to the phenotype '{phenotype['name']}', "
        f"which is defined as '{phenotype.get('definition', 'N/A')}', "
        f"or any of its synonyms: {', '.join(phenotype.get('synonyms', [])) if phenotype.get('synonyms') else 'None'}. "
        f"Focus on genes or biological mechanisms mentioned in connection with this phenotype."
    )

    # Combine all documents (abstracts) into a single context
    formatted_docs = []
    for d in documents:
        pmid = d.get("pmid", "Unknown PMID")
        title = d.get("title", "")
        abstract = d.get("abstract", "")
        journal = d.get("journal", "")
        formatted_docs.append(f"PMID: {pmid}\nTitle: {title}\nJournal: {journal}\nAbstract: {abstract}")

    context_text = "\n\n".join(formatted_docs)
    rag_prompt_formatted = rag_prompt.format(context=context_text, question=question)

    llm = get_llm(llm_name)

    generation = []
    faux_generation = []
    try:
        messages = [
            SystemMessage(content="You are a precise biomedical text mining assistant. Respond only in valid JSON."),
            HumanMessage(content=rag_prompt_formatted)
        ]

        result = llm.invoke(messages)
        raw_output = result.content.strip()
        print(raw_output)

        # Try parsing model output into JSON
        try:
            generation = json.loads(raw_output)
        except json.JSONDecodeError:
            print("Warning: Model returned non-JSON text, attempting to clean...")
            cleaned_output = clean_model_output(raw_output)
            generation = json.loads(cleaned_output)

        print(f"✅ Successfully extracted {len(generation)} genes with PMIDs.")

    except Exception as e:
        print(f"❌ Error during generation: {e}")


    # Save generation output to file
    out_dir = "out/phenotype_generations/"+llm_name
    os.makedirs(out_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in phenotype["name"])
    file_path = os.path.join(out_dir, f"{safe_name}.json")
    try:
        with open(file_path, "w") as f:
            json.dump(generation, f, indent=2)
        print(f"Generation saved to {file_path}")
    except Exception as e:
        print(f"Failed to save generation to file: {e}")

    return {"generation_"+llm_name: generation, "loop_step": loop_step + 1}

import asyncio

def create_control_flow():

    workflow = StateGraph(GraphState)

    # Helper to run async coroutines synchronously
    def run_async(coro):
        return asyncio.run(coro)

    # Define the nodes
    workflow.add_node("retrieve", retrieve_pubtator_abstracts)  # retrieve
    
    # grade documents wrapped with run_async
    workflow.add_node("grade_qwen", lambda state: run_async(grade_abstracts(state, llm_name="qwen2.5:7b")))
    workflow.add_node("grade_deepseek", lambda state: run_async(grade_abstracts(state, llm_name="deepseek-r1:7b")))
    workflow.add_node("grade_llama3", lambda state: run_async(grade_abstracts(state, llm_name="llama3.1:8b")))

    # generate nodes wrapped with run_async
    workflow.add_node("generate_qwen", lambda state: run_async(generate(state, llm_name="qwen2.5:7b")))
    workflow.add_node("generate_deepseek", lambda state: run_async(generate(state, llm_name="deepseek-r1:7b")))
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
