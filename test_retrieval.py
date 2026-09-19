from app.document_loader import load_text_file
from app.chunker import chunk_text
from app.vector_store import VectorStore
from app.prompts import build_qa_prompt
from app.rag_pipeline import RAGPipeline
from app.llm_client import LLMClient
from app.chunker import chunk_by_paragraph

text = load_text_file("data/sample.txt")
chunks = chunk_by_paragraph(text)

store = VectorStore()
store.build_index(chunks)
question = "What is the capital of France?"
results = store.search(question, top_k=3)
for item in results:
    print("文本块下标：", item["chunk_id"])
    print("距离：", item["score"])
    print("原文：", item["chunk"])

print("实际返回数量：", len(results))
print(results[0]["chunk"])
for item in results:
    assert item["chunk"] == chunks[item["chunk_id"]]
print("原文与下标对应检查通过")

contexts = [item["chunk"] for item in results]

prompt = build_qa_prompt(question, contexts)
print(prompt)
llm_client = LLMClient()
pipeline = RAGPipeline(store, llm_client)
result = pipeline.ask(question, top_k=3)
print("问题：", result["question"])
print("模型回答：", result["answer"])
print("来源数量：", len(result["sources"]))