import json
from app.document_loader import load_text_file
from app.vector_store import VectorStore
from app.chunker import chunk_by_paragraph,chunk_text
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--top-k", type=int, default=3, help="Evaluate retrieval evidence hits")
parser.add_argument(
    "--chunking",
    choices=["fixed", "paragraph"],
    default="paragraph",
)
parser.add_argument("--chunk-size", type=int, default=150)
parser.add_argument("--overlap", type=int, default=30)
args = parser.parse_args()
if args.top_k < 1:
    parser.error("--top-k must be at least 1")
top_k = args.top_k

text = load_text_file("data/sample.txt")
if args.chunking == "fixed":
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be greater than 0")
    if not 0 <= args.overlap < args.chunk_size:
        parser.error("--overlap must satisfy 0 <= overlap < chunk-size")
    chunks = chunk_text(text, chunk_size=args.chunk_size, overlap=args.overlap)
    print("切块大小：", args.chunk_size, "重叠：", args.overlap)
else:
    chunks = chunk_by_paragraph(text)

print("切块方式：", args.chunking)
print("文本块数量：", len(chunks))

store = VectorStore()
store.build_index(chunks)

hit_count = 0
with open("data/eval_cases.json", encoding="utf-8") as f:
    cases = json.load(f)

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