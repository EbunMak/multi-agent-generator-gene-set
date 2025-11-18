from langgraph.graph import END
from langgraph.graph import StateGraph
from pubtator import Pubtator
from utils import GraphState, get_llm, get_llm_json_mode, format_json_docs
from langchain_core.messages import HumanMessage, SystemMessage
from instructs import hallucination_grader_instructions, hallucination_grader_prompt, answer_grader_instructions, answer_grader_prompt, rag_prompt, abstract_grader_prompt, grade_abstracts_instructions, rag_prompt2
import json 
import os


# def retrieve_enity_IDS(state):
#     phenotype = state["phenotype"]
#     # phenotype_query = (
#     #     f"Phenotype: {phenotype['name']} "
#     #     f"Description: {phenotype['definition']} "
#     #     f"Synonyms: {', '.join(phenotype.get('synonyms', []))}"
#     # )
#     phenotype_query = f"{phenotype["name"]}"
#     entity_ids_results = Pubtator.find_entity_ID(entity_details="aspirin")
#     print(entity_ids_results)
#     # Ask the LLM to select the best entity
#     system_prompt = (
#         "You are a biomedical NER assistant. "
#         "You will be given JSON containing candidate PubTator entities. "
#         "Your job is to pick the single most relevant entity ID that matches the input phenotype. "
#         "If none are relevant, return 'None'. "
#         "Respond ONLY with a JSON object: {\"entity_id\": \"<id>\"}."
#     )

#     llm = get_llm_json_mode()  # ensures output is valid JSON
#     generation = llm.invoke([
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=str(entity_ids_results))
#     ])

#     #Parse LLM output into Python dict
#     try:
#         entity_id = generation["entity_id"]
#     except Exception:
#         import json
#         parsed = json.loads(generation.content)
#         entity_id = parsed.get("entity_id", None)

#     return {"entity_id": entity_id}

CHECKED_PMIDS_FILE = "checked_pmids.json"

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

    abstracts = []
    for pmid in pmids:
        # Skip PMIDs already known to have no gene annotations
        if str(pmid) in checked_pmids and not checked_pmids[str(pmid)]["has_genes"]:
            print(f"Skipping PMID {pmid}: previously found no genes.")
            continue

        try:
            abs_data = Pubtator.export_abstract(pmid)
            has_genes = abs_data is not None
            # Store the check result
            checked_pmids[pmid] = {"has_genes": has_genes}

            if has_genes:
                abstracts.append(abs_data)
            else:
                print(f"Skipped PMID {pmid}: No gene annotations found.")
        except Exception as e:
            print(f"Failed to fetch PMID {pmid}: {e}")

    # Save checked PMIDs back to file
    with open(CHECKED_PMIDS_FILE, "w") as f:
        json.dump(checked_pmids, f, indent=2)

    # Store results in state
    return {"documents": abstracts}


def grade_abstracts(state):
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


    llm = get_llm_json_mode()
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
            print(f"⚠️ Failed to parse LLM result for PMID {doc.get('pmid')}: {e}")
            continue

        if grade == "yes":
            print(f"✅ PMID {doc.get('pmid')} - RELEVANT")
            filtered_docs.append(doc)
        else:
            print(f"❌ PMID {doc.get('pmid')} - NOT RELEVANT")

    return {"documents": filtered_docs}

def generate(state):
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

    llm = get_llm()

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
            print("⚠️ Warning: Model returned non-JSON text, attempting to clean...")
            cleaned_output = raw_output.split("```json")[-1].split("```")[0].strip()
            generation = json.loads(cleaned_output)

        print(f"✅ Successfully extracted {len(generation)} genes with PMIDs.")

    except Exception as e:
        print(f"❌ Error during generation: {e}")


    # Save generation output to file
    out_dir = "out/phenotype_generations/llama3"
    os.makedirs(out_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in phenotype["name"])
    file_path = os.path.join(out_dir, f"{safe_name}.json")
    try:
        with open(file_path, "w") as f:
            json.dump(generation, f, indent=2)
        print(f"💾 Generation saved to {file_path}")
    except Exception as e:
        print(f"⚠️ Failed to save generation to file: {e}")

    return {"generation": generation, "loop_step": loop_step + 1}

def create_control_flow():

    workflow = StateGraph(GraphState)

    # Define the nodes
    workflow.add_node("retrieve", retrieve_pubtator_abstracts)  # retrieve
    workflow.add_node("grade_abstracts", grade_abstracts)  # grade documents
    workflow.add_node("generate", generate)  # generate


    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_abstracts")
    workflow.add_edge("grade_abstracts", "generate")
    # workflow.add_conditional_edges(
    #     "grade_abstracts",
    #     decide_to_generate,
    #     {
    #         "generate": "generate",
    #     },
    # )
    # workflow.add_conditional_edges(
    #     "generate",
    #     grade_generation_v_documents_and_question,
    #     {
    #         "not supported": "generate",
    #         "useful": END,
    #         "not useful": END,
    #         "max retries": END,
    #     },
    # )

    # Compile
    graph = workflow.compile()
    return graph