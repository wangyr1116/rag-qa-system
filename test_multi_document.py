from app.chunker import chunk_document
from app.document_loader import load_text_files
from app.settings import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SOURCE_PATHS,
    CHUNKING,
)
from app.vector_store import VectorStore


documents = load_text_files(SOURCE_PATHS)

all_chunks = []
all_sources = []

for source, text in documents:
    document_chunks = chunk_document(
        text,
        strategy=CHUNKING,
        chunk_size=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP,
    )

    all_chunks.extend(document_chunks)
    all_sources.extend([source] * len(document_chunks))

store = VectorStore()
store.build_index(all_chunks, sources=all_sources)

results = store.search(
    "Why should a retrieval system keep source metadata?",
    top_k=1,
)

assert results, "search should return at least one result"

top_result = results[0]

# 1. 检索行为：该问题应命中第二份文档
assert top_result["source"] == "data/rag_operations.txt"

# 2. 映射一致性：返回的来源必须等于同一个 chunk_id 对应的来源 result与底账是否一致
chunk_id = top_result["chunk_id"]

assert top_result["chunk"] == all_chunks[chunk_id]
assert top_result["source"] == all_sources[chunk_id]

# 3. 输入保护：每个文本块必须有一个来源
assert len(all_chunks) == len(all_sources)

try:
    store.build_index(
        chunks=["only one chunk"],
        sources=[],
    )
except ValueError as error:
    assert str(error) == "chunks and sources must have the same length"
else:
    raise AssertionError("mismatched chunks and sources should fail")

print("多文档检索与来源映射检查通过")
print("命中文档：", top_result["source"])
print("文本块下标：", chunk_id)