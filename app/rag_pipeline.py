from app.prompts import build_qa_prompt


class RAGPipeline:
    def __init__(self, vector_store,llm_client):
        self.vector_store = vector_store
        self.llm_client = llm_client
    def prepare(self, question: str, top_k: int = 3) -> dict:
        results = self.vector_store.search(question, top_k=top_k)
        contexts = [item["chunk"] for item in results]
        prompt = build_qa_prompt(question, contexts)
        return {"question": question, "sources": results, "prompt": prompt}
    def ask(self, question: str, top_k: int = 3) -> dict:
        prepared = self.prepare(question, top_k=top_k)
        answer = self.llm_client.generate(prepared["prompt"])
        return {
            "question": question,
            "answer": answer,
            "sources": prepared["sources"],
    }