import json
from statistics import median
from app.document_loader import load_text_files
from app.chunker import chunk_document
from app.vector_store import VectorStore
from app.settings import SOURCE_PATHS, CHUNKING, CHUNK_SIZE, CHUNK_OVERLAP

chunks, sources = [], []
for source, text in load_text_files(SOURCE_PATHS):
    parts = chunk_document(
        text, strategy=CHUNKING, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP
    )
    chunks.extend(parts)
    sources.extend([source] * len(parts))
store = VectorStore()
store.build_index(chunks, sources=sources)
print(f"chunking={CHUNKING}, chunks={len(chunks)}, top_k=1")
SPLIT = "test"
DATASETS = {
    "development": ("data/eval_cases.json", "data/ood_dev_cases.json"),
    "test": ("data/test_cases.json", "data/ood_test_cases.json"),
}
print(f"split={SPLIT}")
rows = []
for path in DATASETS[SPLIT]:
    with open(path, encoding="utf-8") as f:
        cases = json.load(f)
    for case in cases:
        item = store.search(case["question"], top_k=1)[0]
        rows.append({#将题目标注与检索结果合并为一条记录
            "id": case["id"], "question": case["question"],
            "category": case.get("category", "answerable"),
            "distance": item["score"],
            "source": item["source"], "chunk_id": item["chunk_id"],
            "chunk": item["chunk"],
        })

for row in sorted(rows, key=lambda row: row["distance"]):
    print(f"{row['id']} | {row['category']} | distance={row['distance']:.4f}")
    print(f"  {row['question']}")
    print(f"  {row['source']} #{row['chunk_id']} | {row['chunk']}")

for category in ("answerable", "unrelated", "related_but_missing"):
    values = [row["distance"] for row in rows if row["category"] == category]
    print(f"{category}: n={len(values)}, min={min(values):.4f}, "
          f"median={median(values):.4f}, max={max(values):.4f}")
report = {
    "split": SPLIT,
    "source_paths": SOURCE_PATHS,
    "chunking": CHUNKING,
    "chunk_size": CHUNK_SIZE,
    "overlap": CHUNK_OVERLAP,
    "chunk_count": len(chunks),
    "top_k": 1,
    "rows": rows,
}
output_path = f"docs/distances_{SPLIT}.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"saved: {output_path}")