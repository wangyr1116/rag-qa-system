from app.prompts import build_qa_prompt

contexts = ["RAG retrieves relevant documents.", "An LLM uses them as context."]
prompt = build_qa_prompt("What is the capital of France?", contexts)
print(prompt)