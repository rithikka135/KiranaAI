from ollama import chat

response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": "Say hello to KiranaAI in one sentence."
        }
    ],
)

print(response.message.content)