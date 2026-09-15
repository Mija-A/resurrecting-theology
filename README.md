# Resurrecting Theology: Cross-Model RAG Pipeline

Code for the working paper *Resurrecting Theology: When Historical Scholars
Confront the Modern World Through AI* (Caliskan, Aleksandraviciute, Fang).

The study examines whether language models with different architectures and
training corpora produce systematically different behavior when conditioned on
identical inputs. Each model is prompted to answer a fixed set of survey
questions while role-playing an assigned historical scholar, grounded in that
scholar's own writings through retrieval-augmented generation. Holding the
corpus and the questions constant while varying only the model isolates
architecture and pretraining as the source of any behavioral difference.

## What's in this repository

This repository contains the data-collection pipelines and the text-cleaning
code for the study. It covers the retrieval-augmented generation (RAG) system used to
query each model and the preprocessing scripts that prepare the source texts
for retrieval. The scholar source texts themselves are not included in the
repository.

### Data-collection pipelines

Each model has its own retrieval-augmented generation pipeline, covering both
commercial API-based systems and open-weight models served locally. For a given
scholar, the pipeline loads a prebuilt FAISS index of that scholar's embedded
writings, and for each survey question it embeds the query, retrieves the most
relevant text chunks, and prompts the model to answer as that scholar grounded
in the retrieved passages. Responses are collected over multiple shuffled rounds
and written to CSV, with placeholder expansion for questions that vary by
country or nationality. The models are pretrained and queried at inference time;
no model weights are modified.

- `upload_docs.py`: chunks and embeds a scholar's texts into a FAISS vector store
- `ask.py`: retrieves passages and queries the model for each survey item
- `run_all.py`: runs the full question set across scholars and saves responses
- helper scripts: (`create_store.py`, `check_empty.py`) where needed

Retrieval uses semantic search over document embeddings (`all-MiniLM-L6-v2`)
with a fixed eight-chunk context for locally served models; the OpenAI pipeline
uses its hosted vector store.

### Text-cleaning scripts

Per-text preprocessing scripts that convert raw scholar source material into
clean plain text for retrieval. These handle the specific artifacts of each
document- OCR noise, running headers and footers, page numbers, footnote blocks,
drop-cap artifacts, hyphenated line breaks, and non-English (Devanagari, CJK)
segments mixed into the English text.

### Visualizations

Scripts for the figures in the paper (scholar timeline and geographic
distribution).

## Setup

API-based pipelines read credentials from a `.env` file and expect the relevant
key (e.g. `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`). Locally served models
(Falcon3, Krutrim-2, GLM) are run through `llama-server`. No keys are stored in
the code.

## Note

This is research code from a working paper, organized by scholar and by model
rather than as a packaged library. It is shared to document the retrieval and
text-processing methodology behind the study.
