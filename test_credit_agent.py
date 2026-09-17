from app.agent.inventory_agent import ask_agent


response = ask_agent(
    "Sell 1 kg sugar to Ravi on credit"
)

print("\nKiranaAI:")
print(response)