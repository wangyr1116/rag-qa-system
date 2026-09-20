# RAG QA System

A beginner-friendly RAG project built with FastAPI, sentence-transformers, and FAISS.

## Current Features
- Load local text documents
- Chunk text into segments
- Build vector index
- Retrieve relevant chunks
- Return retrieved chunks with chunk IDs and squared L2 distances
- Generate answers from retrieved context using the DeepSeek API.
- Expose the RAG pipeline through a FastAPI POST /query endpoint.
- Validate question length and limit top_k to 1–10.

## Next Steps
- Support PDF and Markdown files
- Add reranking
- Build a frontend

## Learning Progress

### Completed: Document Loading

Implemented `app/document_loader.py` to load local UTF-8 text files.

- Input: a local file path, for example `data/sample.txt`
- Output: the complete document content as a Python string
- Error handling: raises `FileNotFoundError` if the file does not exist

### Completed: Text Chunking

Implemented `app/chunker.py` to split long documents into overlapping text chunks.

- Tested with `chunk_size=150`
- Compared `overlap=0` and `overlap=30`
- Observed that overlap preserves shared context between adjacent chunks and reduces semantic loss at chunk boundaries

### Completed: Vector Retrieval

- Encoded text chunks with sentence-transformers/all-MiniLM-L6-v2.
- Built a FAISS IndexFlatL2 index for vector retrieval.
- Returned original chunks with IDs and squared L2 distances.
- Filtered invalid indices when top_k exceeds the number of chunks.
- Checked returned chunk mappings and result counts with assertions.

Current limitations:
- Fixed-size character chunking can split words and sentences.
- Retrieval can return candidates even when the document has no answer.

### Completed: End-to-End RAG API

- Initialize the embedding model and document index during application startup.
- Retrieve context, build a prompt, and generate an answer for each query.
- Return the question, answer, and retrieved sources.
- Read the API key from an environment variable.
- Manually verified an in-document question and an out-of-document question.
- Verified HTTP 422 responses for an empty question and out-of-range top_k values.

Current limitations:
- Retrieved sources are candidate evidence, not verified sentence-level citations.
- Refusal behavior has only been checked on a small number of examples.
- Fixed-size character chunking can split words and sentences.

### Retrieval Evaluation: Chunking Baselines

Evaluated five manually annotated questions on one English sample document.
A hit means at least one retrieved chunk contains the exact annotated evidence.

| Chunking strategy | Overlap (characters) | Chunks | Top K | Evidence hit rate |
|---|---:|---:|---:|---:|
| Fixed: 150 characters | 30 | 15 | 3 | 40.0% (2/5) |
| Fixed: 300 characters | 30 | 7 | 3 | 100.0% (5/5) |
| Paragraph-based | N/A | 6 | 3 | 100.0% (5/5) |
| Paragraph-based | N/A | 6 | 1 | 100.0% (5/5) |

With 150-character chunks, the complete evidence for q3–q5 did not
appear in any single chunk. Larger chunks and paragraph boundaries
preserved the annotated evidence in these examples.

Limitations:
- The dataset contains only five questions from one short document.
- Exact evidence matching does not measure semantic answerability or answer quality.
- Chunk sizes and retrieved context lengths differ across strategies.
- Paragraph chunking does not enforce a maximum input length.

Detailed commands, verification status, and experiment limitations are recorded in [docs/experiments.md](docs/experiments.md).
