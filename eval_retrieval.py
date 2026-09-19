import json
from app.document_loader import load_text_file
from app.chunker import chunk_text
from app.vector_store import VectorStore
from app.chunker import chunk_by_paragraph
with open("data/eval_cases.json", encoding="utf-8") as f:
    cases = json.load(f)

text = load_text_file("data/sample.txt")
chunks = chunk_by_paragraph(text)
print("文本块数量：", len(chunks))
store = VectorStore()
store.build_index(chunks)
hit_count = 0
top_k = 1
for case in cases:
    evidence_available = False
    for chunk in chunks:
        if case["evidence"] in chunk:
            evidence_available = True
    results = store.search(case["question"], top_k=top_k)
    hit = False
    
    for item in results:
        if case["evidence"] in item["chunk"]:
            hit = True
    if hit:
        hit_count += 1
    print(case["id"], case["question"], "命中：", hit)
    print("完整证据存在于某个文本块：", evidence_available)

hit_rate = hit_count / len(cases)
print(f"Top-{top_k} 证据命中率：{hit_rate:.1%}（{hit_count}/{len(cases)}）")