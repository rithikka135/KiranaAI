from app.agent.inventory_agent import detect_payment_method

print(detect_payment_method("Sell 1 kg rice, payment by UPI"))
print(detect_payment_method("Sell 1 kg rice, pay by card"))
print(detect_payment_method("Sell 1 kg rice, cash"))
print(detect_payment_method("Sell 1 kg rice"))