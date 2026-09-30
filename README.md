# RAG QA System

A beginner-friendly RAG project built with FastAPI, sentence-transformers, and FAISS.

## Current Features
- Use a browser question-answering page at `/` to view answers and candidate evidence, with loading and error feedback.
- Load local text documents
- Chunk text into segments
- Build vector index
- Retrieve relevant chunks
- Return retrieved chunks with source paths, chunk IDs, and squared L2 distances
- Attach traceable source labels to model context and validate answer citations against retrieved candidates
- Generate answers from retrieved context using the DeepSeek API.
- Expose retrieval through `POST /search` without a generation-model API key.
- Expose generated answers through the FastAPI `POST /query` endpoint.
- Validate question length and limit top_k to 1–10.

## Local browser demo

Windows CMD, from the project directory (requires uv):

```bat
uv sync
set "DEEPSEEK_API_KEY=your-api-key"
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/ after startup. Ask: `Why should a RAG system keep source metadata?`
The page requests Top-1 retrieval and displays the generated answer and candidate evidence.
Each submitted question invokes the paid generation API. Keep the key in the local environment, not in source files.
The embedding model may require a download on first startup.
`GET /documents` lists the loaded documents; `/docs` provides the API interface.
Candidate evidence does not guarantee answer support, and validated citation labels do not establish semantic correctness.

## Next Steps
- Support PDF and Markdown files
- Add reranking
- Improve the minimal browser interface

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

### Completed: Traceable Retrieval API

- `POST /search` returns retrieval results without invoking DeepSeek.
- `POST /prepare` returns the retrieved candidates and final prompt without invoking DeepSeek, so prompt construction can be inspected without an API key.
- Every result includes `source`, `chunk_id`, `score`, and `chunk`.
- `POST /query` returns both `sources` (retrieved candidates) and `citations` (answer labels validated against those candidates).
- The service indexes multiple local text documents and preserves a source path for every chunk.
- The embedding index starts without `DEEPSEEK_API_KEY`; the key is only needed when `/query` generates an answer.
- Manually verified `/search` against `data/sample.txt` using a fixed 150-character chunk index.
- Verified multi-document retrieval against `data/rag_operations.txt`, including chunk-to-source mapping and mismatched-metadata rejection.
- `GET /config` exposes the active documents and chunking configuration.
- `GET /documents` lists loaded documents, the chunk count for each document, and the total indexed chunk count.
- When no generation key is configured, `POST /query` returns HTTP 503 with a clear error while retrieval remains available.

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
