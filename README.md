# RAG QA System

A beginner-friendly RAG project built with FastAPI, sentence-transformers, and FAISS.

## Current Features
- Use a browser question-answering page at `/` to view answers and candidate evidence, with loading and error feedback.
- Load local text documents
- Chunk text into segments
- Build vector index
- Retrieve relevant chunks
- Return hybrid retrieval candidates with source paths, chunk IDs, RRF scores, and per-channel ranks
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
The page requests Top-3 retrieval and displays the generated answer and candidate evidence.
Each submitted question invokes the paid generation API. Keep the key in the local environment, not in source files.
The embedding model may require a download on first startup.
`GET /documents` lists the loaded documents; `/docs` provides the API interface.
Candidate evidence does not guarantee answer support, and validated citation labels do not establish semantic correctness.

### Use a custom document directory

Before starting the server, run `set "RAG_DOCUMENT_DIR=knowledge"` in Windows CMD.
The directory's immediate UTF-8 `.txt` and `.md` files are loaded in sorted order; The default paragraph strategy reads Markdown as plain text; the markdown_tokens strategy preserves heading context and handles fenced code blocks within the model token budget.
The included fictional handbook supports the question `Who maintains the Cedar project handbook?`.
Restart the server after changing documents to rebuild the in-memory index.
Run `set "RAG_DOCUMENT_DIR="` before restarting to restore the original two sample documents.
Clear this variable before running the original retrieval evaluations, which share the same source configuration.

## FastAPI corpus demo（真实资料演示）

The repository includes six official English FastAPI tutorials pinned to commit `f5c6e9b4f9cadc1bf0f9a1fd672e621206b63007`. Raw files, provenance manifests, and the upstream license are preserved under `knowledge/fastapi`; expanded code examples are under `knowledge/fastapi_expanded`.

Windows CMD:

```bat
uv sync
set "RAG_DOCUMENT_DIR=knowledge\fastapi_expanded"
set "RAG_CHUNKING=markdown_tokens"
uv run uvicorn app.main:app --reload
```

`GET /documents` should report 6 documents and 127 chunks. `POST /search` works without a generation API key. Use `/docs` to search for `Should I raise or return HTTPException?` with `top_k=3`.

The current MiniLM configuration accepts 256 tokens. Chunking counts heading text and special tokens, then splits oversized units. Code excerpts retain fences and indentation but may not be independently executable. Unsupported Markdown forms and individual oversized lines remain limitations; this is a corpus-specific parser, not a complete Markdown implementation.

`ingest_fastapi_docs.py` and `expand_fastapi_docs.py` reproduce the corpus from the pinned revision. They intentionally stop if their output directory already exists. Existing checked-in snapshots require no download; do not rerun these scripts to start the service.

### Retrieval comparison（检索对照）

```bat
set "RAG_DOCUMENT_DIR=knowledge\fastapi_expanded"
set "RAG_CHUNKING=markdown_tokens"
uv run python eval_retrieval.py --cases data/fastapi_dev_cases.json --top-k 3
uv run python eval_retrieval.py --cases data/fastapi_test_cases.json --top-k 3
```

The evaluator compares vector Top-3 with RRF Top-3, using 10 candidates per channel (vector and BM25) and RRF constant 60. BM25 preprocessing lowercases text and preserves underscores in word tokens. RRF combines ranks, not raw BM25 scores and squared L2 distances.

| Dataset | Questions | Vector Top-3 | RRF Top-3 |
|---|---:|---:|---:|
| Development | 6 | 5/6 (83.3%) | 6/6 (100.0%) |
| Held-out | 6 | 3/6 (50.0%) | 4/6 (66.7%) |

These are user-run source-and-evidence-string hit rates, not answer accuracy. The development annotations include manually checked equivalent evidence alternatives; earlier annotation versions and results remain in `docs/experiments.md`. The held-out dataset was frozen before retrieval changes and was not used to tune parameters. Six same-corpus held-out questions do not establish stable improvements or cross-domain generalization.

The browser and `/search`, `/prepare`, `/query` now share hybrid RRF retrieval. Each channel retrieves 10 candidates with RRF constant 60; requests default to 3 final results. Service results include `rrf_score` (higher ranks first) and `ranks` (one-based positions in each channel's candidate list), rather than vector `score` or BM25 `lexical_score`. A missing channel in `ranks` means the chunk was absent from that channel's Top-10. RRF scores are ranking signals, not answer confidence. `GET /config` exposes the retrieval settings.

Clear both settings before running the original sample evaluations or restoring the default demo:

```bat
set "RAG_DOCUMENT_DIR="
set "RAG_CHUNKING="
```

Restart the service after configuration changes. Evaluation overrides such as `--chunking` may differ from service configuration.

## Next Steps
- Verify a generated answer and its citations on the real corpus through the browser
- Verify a reproducible deployment and representative document coverage
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
- Every service retrieval result includes `source`, `chunk_id`, `chunk`, `rrf_score`, and `ranks`.
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
