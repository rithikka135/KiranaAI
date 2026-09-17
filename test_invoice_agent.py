from app.agent.inventory_agent import ask_agent

response = ask_agent(
    "Send invoice for bill 12"
)

print("\nKiranaAI:")
print(response)