from app.agent.inventory_agent import ask_agent

response = ask_agent(
    "Sell 1 kg rice, payment by UPI"
)

print("\nKiranaAI:")
print(response)