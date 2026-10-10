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
from pathlib import Path
from app.fusion import fuse_rankings
parser = argparse.ArgumentParser()
parser.add_argument("--top-k", type=int, default=3, help="Evaluate retrieval evidence hits")
parser.add_argument(
    "--chunking",
    choices=["fixed", "paragraph", "markdown_sections", "markdown_tokens"],
    default=CHUNKING,
)
parser.add_argument("--cases", help="Evaluate one specified development dataset")
parser.add_argument("--chunk-size", type=int, default=150)
parser.add_argument("--overlap", type=int, default=30)
args = parser.parse_args()
if args.top_k < 1:
    parser.error("--top-k must be at least 1")
top_k = args.top_k

documents = load_text_files(SOURCE_PATHS)
store = VectorStore()
def count_tokens(text: str) -> int:
    return len(store.model.tokenizer.encode(text, truncation=False))
all_chunks = []
all_sources = []

for source, text in documents:
    document_chunks = chunk_document(
        text,
        strategy=args.chunking,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        count_tokens=count_tokens,
        max_tokens=store.model.max_seq_length
    )

    all_chunks.extend(document_chunks)
    all_sources.extend([Path(source).as_posix()] * len(document_chunks))

print("切块方式：", args.chunking)
print("文本块数量：", len(all_chunks))


store.build_index(all_chunks, sources=all_sources)
def matches_evidence(case, source: str, chunk: str) -> bool:
    expected_source = Path(case["source"]).as_posix()
    actual_source = Path(source).as_posix()
    if "evidence_any" in case:
        evidences = case["evidence_any"]
    else:
        evidences = [case["evidence"]]
    return (
        expected_source == actual_source
        and any(evidence in chunk for evidence in evidences)
    )
def evaluate_cases(cases_path, dataset_name):
    hit_count = 0
    hybrid_hit_count = 0
    with open(cases_path, encoding="utf-8") as f:
        cases = json.load(f)

    for case in cases:
        case["source"] = Path(case["source"]).as_posix()
        evidence_available = any(
            matches_evidence(case, source, chunk)
            for chunk, source in zip(all_chunks, all_sources)
        )

        results = store.search(case["question"], top_k=top_k)
        lexical_results = store.search_lexical(case["question"], top_k=10)
        lexical_rank = None
        for rank, item in enumerate(lexical_results, start=1):
            if matches_evidence(case, item["source"], item["chunk"]):
                lexical_rank = rank
                break
        print(case["id"], "关键词Top-10中的证据排名：", lexical_rank)
        hybrid_results = fuse_rankings(
            {
                "vector": store.search(case["question"], top_k=10),
                "lexical": lexical_results,
            },
            top_k=top_k,
        )
        hybrid_hit = any(
            matches_evidence(case, item["source"], item["chunk"])
            for item in hybrid_results
        )
        hybrid_hit_count += int(hybrid_hit)
        print(case["id"], "融合命中：", hybrid_hit)
        for item in results:
            print(
                    "检索结果：",
                    f"source={item['source']}",
                    f"chunk_id={item['chunk_id']}",
                    f"distance={item['score']:.4f}",
                    )
        hit = any(
            matches_evidence(case, item["source"], item["chunk"])
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
    print(
        f"融合Top-{top_k}证据命中率："
        f"{hybrid_hit_count / len(cases):.1%}（{hybrid_hit_count}/{len(cases)}）"
    )

if args.cases:
    evaluate_cases(args.cases, "指定题集")
else:
    evaluate_cases("data/eval_cases.json", "开发集")
    evaluate_cases("data/test_cases.json", "独立测试集")