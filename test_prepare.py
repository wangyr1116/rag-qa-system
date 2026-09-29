from app.rag_pipeline import RAGPipeline
from app.citations import find_valid_citations

class FakeVectorStore:
    def __init__(self):
        self.received_question = None
        self.received_top_k = None

    def search(self, question: str, top_k: int) -> list[dict]:
        self.received_question = question
        self.received_top_k = top_k

        return [
            {
                "chunk_id": 6,
                "chunk": (
                    "Source metadata helps users verify "
                    "where an answer came from."
                ),
                "score": 0.53,
                "source": "data/rag_operations.txt",
            }
        ]

class FakeLLMClient:
    def __init__(self):
        self.received_prompt = None

    def generate(self, prompt: str) -> str:
        self.received_prompt = prompt
        return (
            "Source metadata helps users verify where an answer came from. "
            "[source: data/rag_operations.txt, chunk_id: 6]"
        )
store = FakeVectorStore()
llm_client = FakeLLMClient()
pipeline = RAGPipeline(store, llm_client=llm_client)

prepared = pipeline.prepare(
    question="Why should a retrieval system keep source metadata?",
    top_k=1,
)

assert store.received_question == (
    "Why should a retrieval system keep source metadata?"
)
assert store.received_top_k == 1

assert prepared["sources"][0]["source"] == "data/rag_operations.txt"
assert "Source metadata helps users verify" in prepared["prompt"]
assert "Why should a retrieval system keep source metadata?" in prepared["prompt"]
assert "[source: data/rag_operations.txt, chunk_id: 6]" in prepared["prompt"]
assert "Cite the supporting source label" in prepared["prompt"]
response = pipeline.ask(
    question="Why should a retrieval system keep source metadata?",
    top_k=1,
)

assert "[source: data/rag_operations.txt, chunk_id: 6]" in llm_client.received_prompt
assert response["answer"].startswith("Source metadata helps users verify")
assert response["sources"][0]["source"] == "data/rag_operations.txt"
assert response["citations"][0]["source"] == "data/rag_operations.txt"
assert response["citations"][0]["chunk_id"] == 6
invalid_citations = find_valid_citations(
    "[source: data/not_found.txt, chunk_id: 99]",
    response["sources"],
)

assert invalid_citations == []
print("prepare 链路检查通过")