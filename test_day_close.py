from app.agent.inventory_agent import ask_agent

response = ask_agent(
    "Give me today's day close report"
)

print("\nKiranaAI:")
print(response)
