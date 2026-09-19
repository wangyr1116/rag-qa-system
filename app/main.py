from fastapi import FastAPI
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from app.document_loader import load_text_file
from app.chunker import chunk_text
from app.vector_store import VectorStore
from app.llm_client import LLMClient
from app.rag_pipeline import RAGPipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    text = load_text_file("data/sample.txt")
    chunks = chunk_text(text, chunk_size=150, overlap=30)
    store = VectorStore()
    store.build_index(chunks)
    llm_client = LLMClient()
    app.state.pipeline = RAGPipeline(store, llm_client)
    print("RAG 初始化完成")
    yield
app = FastAPI(title="RAG QA System", lifespan=lifespan)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "ok",
            "建议访问": "/docs"}

@app.post("/query")
def query(request: QueryRequest):
    return app.state.pipeline.ask(
        question=request.question,
        top_k=request.top_k,
    )