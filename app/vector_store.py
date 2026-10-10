import faiss
from sentence_transformers import SentenceTransformer
import re
from rank_bm25 import BM25Okapi

class VectorStore:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.text_chunks = []
        self.sources = []
        self.lexical_index = None
    def validate_chunk_lengths(self, chunks: list[str]) -> None:
        encoded = self.model.tokenizer(
            chunks,
            padding=False,
            truncation=False,
        )
        limit = self.model.max_seq_length
        oversized = []

        for index, token_ids in enumerate(encoded["input_ids"]):
            token_count = len(token_ids)
            if token_count > limit:
                oversized.append((index, token_count))

        if oversized:
            examples = oversized[:5]
            raise ValueError(
                f"有 {len(oversized)} 个文本块超过 {limit} token；"
                f"前5个块的编号与长度：{examples}。请先调整切块。"
            )
    def build_index(self, chunks: list[str], sources: list[str]) -> None:
        if not chunks:
            raise ValueError("chunks cannot be empty")
        if len(chunks) != len(sources):
            raise ValueError("chunks and sources must have the same length")
        self.validate_chunk_lengths(chunks)
        self.text_chunks = chunks
        self.sources = sources
        embeddings = self.model.encode(chunks, convert_to_numpy=True).astype("float32")
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        tokenized = [re.findall(r"\w+", chunk.lower()) for chunk in chunks]
        self.lexical_index = BM25Okapi(tokenized)

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
                        "source": self.sources[idx],

                    }
                )

        return results
    def search_lexical(self, query: str, top_k: int = 10) -> list[dict]:
        if self.lexical_index is None:
            raise ValueError("lexical index has not been built")
        query_tokens = re.findall(r"\w+", query.lower())
        if not query_tokens:
            return []
        scores = self.lexical_index.get_scores(query_tokens)
        indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )[:top_k]
        return [
            {
                "chunk_id": index,
                "chunk": self.text_chunks[index],
                "source": self.sources[index],
                "lexical_score": float(scores[index]),
            }
            for index in indices
        ]