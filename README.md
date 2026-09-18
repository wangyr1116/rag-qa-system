# RAG QA System

A beginner-friendly RAG project built with FastAPI, sentence-transformers, and FAISS.

## Current Features
- Load local text documents
- Chunk text into segments
- Build vector index
- Retrieve relevant chunks
- Return retrieved chunks with chunk IDs and squared L2 distances

## Next Steps
- Connect a real LLM API
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
- Retrieval is not yet connected to the FastAPI query endpoint or an LLM.