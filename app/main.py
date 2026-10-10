from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from app.document_loader import load_text_files
from app.chunker import chunk_document
from app.vector_store import VectorStore
from app.rag_pipeline import RAGPipeline
from pathlib import Path
from fastapi.responses import FileResponse
from app.settings import (
    CHUNKING,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SOURCE_PATHS,
)
from openai import (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    documents = load_text_files(SOURCE_PATHS)
    store = VectorStore()
    def count_tokens(text: str) -> int:
        token_ids = store.model.tokenizer.encode(
            text,
            truncation=False,
        )
        return len(token_ids)
    all_chunks = []
    all_sources = []
    document_stats = []

    for source, text in documents:
        document_chunks = chunk_document(
            text,
            strategy=CHUNKING,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP,
            count_tokens=count_tokens,
            max_tokens=store.model.max_seq_length
        )

        all_chunks.extend(document_chunks)
        all_sources.extend([source] * len(document_chunks))
        document_stats.append(
            {
                "source": source,
                "chunk_count": len(document_chunks),
            }
        )


    store.build_index(all_chunks, sources=all_sources)
    app.state.document_stats = {
        "document_count": len(document_stats),
        "chunk_count": len(all_chunks),
        "documents": document_stats,
    }
    app.state.pipeline = RAGPipeline(store)
    print("RAG 初始化完成")
    yield


app = FastAPI(title="RAG QA System", lifespan=lifespan)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    return {
        "sources": SOURCE_PATHS,
        "chunking": CHUNKING,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }

@app.get("/documents")
def documents():
    return app.state.document_stats


@app.get("/")
def root():
    page = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(page)

@app.post("/search")
def search(request: QueryRequest):
    results = app.state.pipeline.retrieve(
        question=request.question,
        top_k=request.top_k,
    )

    return {
        "question": request.question,
        "results": results,
    }


@app.post("/prepare")
def prepare(request: QueryRequest):
    return app.state.pipeline.prepare(
        question=request.question,
        top_k=request.top_k,
    )


@app.post("/query")
def query(request: QueryRequest):
    try:
        return app.state.pipeline.ask(
            question=request.question,
            top_k=request.top_k,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error
    except APITimeoutError as error:
        raise HTTPException(
            status_code=504,
            detail="生成服务响应超时，请稍后重试",
        ) from error
    except APIConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail="暂时无法连接生成服务，请稍后重试",
        ) from error
    except RateLimitError as error:
        raise HTTPException(
            status_code=503,
            detail="生成服务当前受限，请稍后重试",
        ) from error
    except APIStatusError as error:
        raise HTTPException(
            status_code=502,
            detail="生成服务返回错误，请检查服务配置或稍后重试",
        ) from error
