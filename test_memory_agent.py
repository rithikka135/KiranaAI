from app.agent.inventory_agent import ask_agent


print("\n--- SAVE TEST ---")

response = ask_agent(
    "Remember that my shop opens at 8 AM"
)

print("\nKiranaAI:")
print(response)


print("\n--- SECOND SAVE TEST ---")

response = ask_agent(
    "Remember that my preferred payment method is UPI"
)

print("\nKiranaAI:")
print(response)


print("\n--- READ TEST ---")

response = ask_agent(
    "What are my saved preferences?"
)

print("\nKiranaAI:")
print(response)
