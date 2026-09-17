from ollama import chat

from app.agent.inventory_agent import (
    check_stock_tool,
    receive_stock_tool,
)
from app.tools.billing_tools import sell_product_tool


response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": "Sell 1 kg sugar to Ravi on credit",
        }
    ],
    tools=[
        check_stock_tool,
        receive_stock_tool,
        sell_product_tool,
    ],
)

print("\nQwen3 Tool Call:")
print("----------------")

for tool_call in response.message.tool_calls:
    print("Tool:", tool_call.function.name)
    print("Arguments:", tool_call.function.arguments)