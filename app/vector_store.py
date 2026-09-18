import faiss
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.text_chunks = []

    def build_index(self, chunks: list[str]) -> None:
        if not chunks:
            raise ValueError("chunks cannot be empty")

        self.text_chunks = chunks
        embeddings = self.model.encode(chunks, convert_to_numpy=True).astype("float32")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if self.index is None:
            raise ValueError("index has not been built")

        query_embedding = self.model.encode([query], convert_to_numpy=True).astype("float32")
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if 0<= idx < len(self.text_chunks):
                results.append(
                    {
                        "chunk_id": int(idx),
                        "chunk": self.text_chunks[idx],
                        "score": float(distances[0][i]),
                    }
                )

        return results