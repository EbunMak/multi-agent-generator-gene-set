# A Multi-Agent Approach to Generating Context-Rich Gene Sets

This repository contains the full implementation of our pipeline for reconstructing Human Phenotype Ontology (HPO) gene sets using large language models (LLMs), including **Llama 3.1 8B**, **Qwen 3 32B**, and **DeepSeek R-1 8B**.
It includes all code for phenotype extraction, literature retrieval, gene-set generation, verification, consolidation, and evaluation.

We provide the final reconstructed 437 HPO gene sets in:
`out/genesets/consensus_gene_sets.gmt`
(All genes are represented using Entrez IDs.)

Additional data, including downloaded abstracts, MSigDB HPO data, and intermediate model-specific gene sets, are also available within the repository.



## Installation and Requirements

This project was tested on:

```
Python 3.12.5
Ollama 0.11.11
```

Install Python dependencies:

```
pip install -r requirements.txt
```

Make sure Ollama is installed and running, and that all required models
(Qwen 3 32B, Llama 3.1 8B, DeepSeek R-1 8B) are available locally.
We ran Ollama in the background using:

```
nohup ollama serve > ollama.log 2>&1 &
```

This ensures the local LLM server remains active throughout long-running jobs.

### Computing Environment (Cluster)

Our experiments were run on a research computing cluster using configurations such as:

```
salloc -N1 -n1 -c8  --mem=32GB --gres=gpu:1 -p gpu-v100
salloc -N1 -n1 -c4  --mem=32GB --gres=gpu:1 -p bigmem
```

These details are provided to give context on hardware availability; no specific time limits are included.



## Pipeline Overview

The pipeline reconstructs gene sets through the following stages:

1. **Phenotype Extraction**
2. **Literature Retrieval and Filtering**
3. **Gene Set Construction**
4. **Gene Association Verification**
5. **Consensus Gene Set Construction**
6. **Evaluation and Plot Generation**

The following sections describe how to run each stage.



## 1. Phenotype Extraction

The phenotype extraction process retrieves HPO metadata (names, IDs, definitions, and synonyms).
A small example dataset of five phenotypes is included.

Run:

```
python3 phenotype_extractor.py
```

This produces:

```
out/phenotype_details.json
```

We also include a full list of 5567 phenotypes, representing the intersection between MSigDB HPO gene sets and HPO’s official phenotype-to-gene annotations.



## 2. Main Pipeline (Literature Retrieval to Gene Maker to Gene Checker)

Run the main pipeline using:

```
python3 main.py --input_file out/phenotype_details.json
```

This performs:

* PubTator 3.0 literature retrieval
* LLM-based gene extraction (“gene maker”)
* LLM-based verification (“gene checker”)

The output consists of extracted and verified gene sets for each phenotype, stored under:

```
out/phenotype_generations/<model>/
out/phenotype_checks/<model>/
```



## 3. Constructing Gene Sets (Per LLM)

To convert extracted and verified genes into GMT files, run:

### Llama 3.1 8B

```
python3 geneset_constructor.py --model llama3.1:8b
```

### Qwen 3 32B

```
python3 geneset_constructor.py --model qwen3:32b
```

### DeepSeek R-1 8B

```
python3 geneset_constructor.py --model deepseek-r1:8b
```

Each generates Entrez- and symbol-based GMTs under:

```
out/genesets/<model>/
```



## 4. Constructing Consensus Gene Sets (Majority Voting)

To merge the three gene-set databases into a consensus:

```
python3 construct_llms_gmts.py
```

By default, this reads:

* `out/genesets/qwen/genesets_entrez_qwen.gmt`
* `out/genesets/deepseek/genesets_entrez_deepseek.gmt`
* `out/genesets/llama/genesets_entrez_llama.gmt`

You may override them using:

```
--qwen_gmt
--deepseek_gmt
--llama_gmt
```

This produces:

* `out/genesets/consensus_gene_sets.gmt` – the new consensus
* `out/genesets/phenotype_consensus_gene_sets.gmt` – the original gene sets corresponding to the same phenotypes

Consensus is based on majority vote:
a gene is included if at least two of the three LLMs identify or validate it.



## 5. Evaluation

Run evaluation:

```
python3 evaluation.py
```

Or specify custom GMTs:

```
python3 evaluation.py --original_gmt <path> --new_gmt <path>
```

This produces:

* `out/evaluation/gene_set_comparison.csv`
* `out/evaluation/gene_set_similarity.csv`
* `out/evaluation/gene_analysis.txt`
  (containing summary statistics: mean loss, mean new genes, overall similarity)



## 6. Plot Generation

The evaluation CSVs can be visualized using:

```
python3 similarity_plot.py
python3 lost_genes_plot.py
python3 new_genes_plot.py
```

Plots are saved as SVG, PNG, and PDF under:

```
out/evaluation/plots/
```



## Additional Notes

* The `geneset data/` directory contains MSigDB’s HPO gene sets (v2025.1) in both Entrez and symbol formats, as well as HPO’s official phenotype-to-gene annotations.
* The `abstracts/` directory contains the downloaded PubTator abstracts used for gene–phenotype association.
* The repository includes intermediate outputs for all LLMs under `out/geneset/<model>`.
* All scripts assume that Ollama is available and running locally.