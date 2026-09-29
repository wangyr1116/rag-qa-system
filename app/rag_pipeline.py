from app.prompts import build_qa_prompt
from app.llm_client import LLMClient
from app.citations import find_valid_citations


class RAGPipeline:
    def __init__(self, vector_store, llm_client=None):
        self.vector_store = vector_store
        self.llm_client = llm_client

    def retrieve(self, question: str, top_k: int = 3) -> list:
        results = self.vector_store.search(question, top_k=top_k)
        return results

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
        prepared = self.prepare(question, top_k=top_k)
        if self.llm_client is None:
            self.llm_client = LLMClient()
        answer = self.llm_client.generate(prepared["prompt"])
        citations = find_valid_citations(
            answer,
            prepared["sources"],
        )
        return {
            "question": question,
            "answer": answer,
            "sources": prepared["sources"],
            "citations": citations,
        }
