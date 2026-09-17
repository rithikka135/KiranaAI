from ollama import chat
from app.database.connection import SessionLocal
from app.tools.inventory_tools import check_stock


def check_stock_tool(product_name: str) -> dict:
    db = SessionLocal()

    try:
        return check_stock(
            db=db,
            product_name=product_name,
        )
    finally:
        db.close()


messages = [
    {
        "role": "user",
        "content": "How much rice do we have in stock?",
    }
]

# 1. Ask Qwen3
response = chat(
    model="qwen3:4b",
    messages=messages,
    tools=[check_stock_tool],
)

# 2. Add Qwen3's tool request to the conversation
messages.append(response.message)

# 3. Execute the requested tool
if response.message.tool_calls:

    for tool_call in response.message.tool_calls:

        if tool_call.function.name == "check_stock_tool":

            product_name = tool_call.function.arguments["product_name"]

            result = check_stock_tool(product_name)

            print("Tool result:")
            print(result)

            # 4. Give the tool result back to Qwen3
            messages.append(
                {
                    "role": "tool",
                    "tool_name": "check_stock_tool",
                    "content": str(result),
                }
            )

# 5. Ask Qwen3 for the final human-friendly answer
final_response = chat(
    model="qwen3:4b",
    messages=messages,
)

print("\nKiranaAI:")
print(final_response.message.content)