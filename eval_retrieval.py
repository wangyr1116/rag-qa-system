import json
from app.document_loader import load_text_files
from app.vector_store import VectorStore
from app.chunker import chunk_document
from app.settings import (
    CHUNKING,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SOURCE_PATHS,
)
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

documents = load_text_files(SOURCE_PATHS)

all_chunks = []
all_sources = []

for source, text in documents:
    document_chunks = chunk_document(
        text,
        strategy=args.chunking,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )

    all_chunks.extend(document_chunks)
    all_sources.extend([source] * len(document_chunks))

print("切块方式：", args.chunking)
print("文本块数量：", len(all_chunks))

store = VectorStore()
store.build_index(all_chunks, sources=all_sources)

def evaluate_cases(cases_path, dataset_name):
    hit_count = 0

    with open(cases_path, encoding="utf-8") as f:
        cases = json.load(f)

    for case in cases:
        evidence_available = any(
    case["source"] == source and case["evidence"] in chunk
    for chunk, source in zip(all_chunks, all_sources)
)

        results = store.search(case["question"], top_k=top_k)
        for item in results:
            print(
                    "检索结果：",
                    f"source={item['source']}",
                    f"chunk_id={item['chunk_id']}",
                    f"distance={item['score']:.4f}",
                    )
        hit = any(
            case["source"] == item["source"] and case["evidence"] in item["chunk"]
            for item in results
        )

        if hit:
            hit_count += 1

        print(case["id"], case["question"], "命中：", hit)
        print("完整证据存在于某个文本块：", evidence_available)

    hit_rate = hit_count / len(cases)
    print(
        f"【{dataset_name}】Top-{top_k} 证据命中率："
        f"{hit_rate:.1%}（{hit_count}/{len(cases)}）"
    )

evaluate_cases("data/eval_cases.json", "开发集")
evaluate_cases("data/test_cases.json", "独立测试集")