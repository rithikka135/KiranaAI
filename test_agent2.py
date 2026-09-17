from app.agent.inventory_agent import ask_agent


result = ask_agent(
    "How much rice do we have in stock?"
)

print("\nKiranaAI:")
print(result)