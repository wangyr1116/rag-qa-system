import json
from pathlib import Path
from app.prompts import build_qa_prompt
from app.llm_client import LLMClient

snapshot = Path("docs/distances_development.json")
report = json.loads(snapshot.read_text(encoding="utf-8"))
assert report["split"] == "development" and report["top_k"] == 1
selected = {"ops_dev_1": True, "ood_dev_3": False, "ood_dev_1": False}
rows = [row for row in report["rows"] if row["id"] in selected]
assert len(rows) == 3 and {row["id"] for row in rows} == set(selected)
output = Path("docs/generation_development.json")
if output.exists():
    raise FileExistsError("结果文件已存在，请先检查，避免重复调用模型。")
client = LLMClient()
results = []
for row in rows:
    context = (
        f"[source: {row['source']}, chunk_id: {row['chunk_id']}]\n"
        f"{row['chunk']}"
    )
    prompt = build_qa_prompt(row['question'], [context])  # TODO 1：传入当前题目的问题
    answer = client.generate(prompt)  # TODO 2：使用 client 生成该 prompt 的回答
    results.append({
        "id": row["id"], "question": row["question"],
        "candidate_sufficient": selected[row["id"]],
        "source": row["source"], "chunk_id": row["chunk_id"],
        "chunk": row["chunk"], "prompt": prompt, "answer": answer,
    })
    output.write_text(
        json.dumps({"snapshot": str(snapshot), "rows": results},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n{row['id']} | sufficient={selected[row['id']]}\n{answer}")