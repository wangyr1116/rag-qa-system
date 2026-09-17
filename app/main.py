from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RAG QA System")


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "ok",
            "建议访问": "/docs"}

@app.post("/query")
def query(request: QueryRequest):
    return {
        "question": request.question,
        "answer": "RAG project skeleton is running successfully.",
        "top_k": request.top_k,
    }