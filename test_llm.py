import os
from openai import OpenAI
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("未找到 DEEPSEEK_API_KEY，请先在当前终端设置")

print("密钥已读取")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "用一句话解释什么是 RAG。"}
    ],
    max_tokens=100,
)
print(response.choices[0].message.content)