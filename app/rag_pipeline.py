from app.prompts import build_qa_prompt
from app.llm_client import LLMClient
from app.citations import find_valid_citations
from time import perf_counter
from app.fusion import fuse_rankings
class RAGPipeline:
    def __init__(self, vector_store, llm_client=None):
        self.vector_store = vector_store
        self.llm_client = llm_client

    def retrieve(self, question: str, top_k: int = 3) -> list:
        rankings = {
            "vector": self.vector_store.search(question, top_k=10),
            "lexical": self.vector_store.search_lexical(question, top_k=10),
        }
        return fuse_rankings(rankings, top_k=top_k)
    def prepare(self, question: str, top_k: int = 3) -> dict:
        results = self.retrieve(question, top_k=top_k)
        contexts = [
            (
                f"[source: {item['source']}, "
                f"chunk_id: {item['chunk_id']}]\n"
                f"{item['chunk']}"
            )
            for item in results
        ]
        prompt = build_qa_prompt(question, contexts)
        return {"question": question, "sources": results, "prompt": prompt}

    def ask(self, question: str, top_k: int = 3) -> dict:
        started = perf_counter()
        prepared = self.prepare(question, top_k=top_k)
        prepared_at = perf_counter()
        if self.llm_client is None:
            self.llm_client = LLMClient()
        answer = self.llm_client.generate(prepared["prompt"])
        generated_at = perf_counter()
        citations = find_valid_citations(
            answer,
            prepared["sources"],
        )
        timings_ms = {
            "prepare": round((prepared_at - started) * 1000, 1),
            "generation": round((generated_at - prepared_at) * 1000, 1),
            "total": round((perf_counter() - started) * 1000, 1),
        }
        return {
            "question": question,
            "answer": answer,
            "sources": prepared["sources"],
            "citations": citations,
            "timings_ms": timings_ms,
        }
