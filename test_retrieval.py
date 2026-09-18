from app.document_loader import load_text_file
from app.chunker import chunk_text
from app.vector_store import VectorStore

text = load_text_file("data/sample.txt")
chunks = chunk_text(text, chunk_size=150, overlap=30)

store = VectorStore()
store.build_index(chunks)
results = store.search("What is the capital of France?", top_k=3)

for item in results:
    print("文本块下标：", item["chunk_id"])
    print("距离：", item["score"])
    print("原文：", item["chunk"])

print("实际返回数量：", len(results))

for item in results:
    assert item["chunk"] == chunks[item["chunk_id"]]
print("原文与下标对应检查通过")

assert len(results) == 3
print("返回数量检查通过")