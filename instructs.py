### LLM
from langchain_ollama import ChatOllama

local_llm = "llama3.1:8b"
llm = ChatOllama(model=local_llm, temperature=0)
llm_json_mode = ChatOllama(model=local_llm, temperature=0, format="json")


grade_abstracts_instructions = """You are a scientific grader assessing the relevance of retrieved scientific abstracts to a biological or disease-related question.

If the abstract contains keywords or semantic meaning related to the question (such as the phenotype or functionally associated genes), grade it as relevant.
Otherwise, mark it as not relevant.

Respond ONLY with a valid JSON object in the form:
{"binary_score": "yes"} or {"binary_score": "no"}.
"""

grade_abstracts_instructions2 = """You are a biomedical research assistant.

Your task is to determine if a given abstract discusses BOTH:
1. The specified phenotype (disease, biological process, or abnormality).
2. The specified gene mentioned in the question.

If BOTH are mentioned in a relevant context (same pathway, mechanism, or association), mark as "yes".
If only one or neither is relevant, mark as "no".

Return ONLY valid JSON with this format:
{"binary_score": "yes" or "no"}.

Do not explain, just return JSON.
"""


# Grader prompt
abstract_grader_prompt = """Here is the retrieved scienitific abstract document: \n\n {document} \n\n Here is the question: \n\n {question}. 

Think carefully and objectively assess whether the document contains at least some information that is relevant to the question.

Return JSON with single key, binary_score, that is 'yes' or 'no' score to indicate whether the document contains at least some information that is relevant to the question."""




# Generate
# Prompt
rag_prompt = """You are an assistant for a gene set curation task.  

Task Overview:
Your role is to identify genes that may be related to or responsible for a given biological process or disease from the 
question:
{question}  
using this as the context:
{context}  

Each context may contain multiple abstracts retrieved from PubTator.  
For each abstract, you must carefully review the title and abstract text to identify any functionally relevant genes.

Respond ONLY with a list of JSON objects only, do not add any other commentary, markdown, or text. Each object must have exactly these three keys:
1. "Gene": Identified gene mentioned in the abstract.
2. "Source Reference": Direct quote from the abstract that supports the gene’s relevance.
3. "PMID": The PubMed ID of the abstract where the gene was found.
4. "Journal": The journal where the abstract was published

Make sure:
- There are no duplicate genes.
- Every "Source Reference" is tied to the specific PMID where it appears.
- The output is **valid JSON only** — no extra commentary, markdown, or text.

"""

rag_prompt2 = """You are an assistant for a gene set validation task.  
Here is the context to use to answer the question:
{context}

Task Overview:  
Your role is to determine whether a gene provided in the question is supported by the provided context in relation to a given biological process or disease also in the question.  
Here is the question containing the gene and the biological process or disease:
{question}

Then return JSON with exactly these keys:
1. Gene: gene name  
2. Validation: "yes" or "no" score to indicate whether the gene is validated with the context  
3. Supporting Extract: "Direct quote(s) from the context that validates the gene." and short reasoning (≤5 lines) if more than one abstract is used  
4. PMIDS: list of pmids of the abstract(s) where the inference was made. If the answer for validation is yes then at least one PMID must be provided.  

Do not return any explanation or extra text—only JSON.
"""


# Hallucination Grader
# Hallucination grader instructions
hallucination_grader_instructions = """

You are a teacher grading a quiz. 

You will be given FACTS and a STUDENT ANSWER. 

Here is the grade criteria to follow:

(1) Ensure the STUDENT ANSWER is grounded in the FACTS. 

(2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

Score:

A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 

A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""

# Grader prompt
hallucination_grader_prompt = """FACTS: \n\n {documents} \n\n STUDENT ANSWER: {generation}. 

Return JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER is grounded in the FACTS. And a key, explanation, that contains an explanation of the score."""


# Answer Grader
# Answer grader instructions
answer_grader_instructions = """You are a teacher grading a quiz. 

You will be given a QUESTION and a STUDENT ANSWER. 

Here is the grade criteria to follow:

(1) The STUDENT ANSWER helps to answer the QUESTION

Score:

A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 

The student can receive a score of yes if the answer contains extra information that is not explicitly asked for in the question.

A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""

# Grader prompt
answer_grader_prompt = """QUESTION: \n\n {question} \n\n STUDENT ANSWER: {generation}. 

Return JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER meets the criteria. And a key, explanation, that contains an explanation of the score."""
