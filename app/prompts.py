def build_qa_prompt(question: str, contexts: list[str]) -> str:
    context_text = "\n\n".join(contexts)
    return f"""Answer the question using only the context below.
Cite the supporting source label in this format:
[source: path, chunk_id: number]
If the context does not contain the answer, say "I don't know."

Context:
{context_text}

Question:
{question}

Answer:
"""
