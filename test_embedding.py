from app.document_loader import load_text_file
from app.chunker import chunk_text
from sentence_transformers import SentenceTransformer
import faiss

text = load_text_file("data/sample.txt")
chunks = chunk_text(text, chunk_size=150, overlap=30)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

embeddings = model.encode(chunks, convert_to_numpy=True)
embeddings = embeddings.astype("float32")
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
question =  "How does RNN process tokens?"
query_embedding = model.encode(
    [question], convert_to_numpy=True
).astype("float32")
distances, indices = index.search(query_embedding, 3)
print(query_embedding.shape)
print("距离：", distances)
print("下标：", indices)
print("当前问题：", question)
for rank, chunk_id in enumerate(indices[0], start=1):
    distance = distances[0][rank - 1]
    print(f"\n第 {rank} 名，距离：{distance:.4f}")
    print(chunks[chunk_id])