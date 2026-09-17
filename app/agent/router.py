# app/agent/router.py

from app.agent.inventory_agent import ask_agent
from app.agent.customer_agent import ask_customer_agent


# ============================================================
# CUSTOMER INTENT DETECTION
# ============================================================

def is_customer_request(message: str) -> bool:
    """
    Decide whether the message should go to the
    customer management agent.

    Customer agent handles:
    - Add customer
    - Create customer
    - Register customer
    - Find/search customer
    - Customer balance
    - Khata balance
    - Customer payments
    """

    text = message.lower().strip()

    # --------------------------------------------------------
    # 1. Explicit customer creation
    # --------------------------------------------------------

    customer_creation_phrases = [
        "add customer",
        "create customer",
        "register customer",
        "new customer",
        "save customer",
    ]

    for phrase in customer_creation_phrases:
        if phrase in text:
            return True

    # --------------------------------------------------------
    # 2. Customer search
    # --------------------------------------------------------

    customer_search_phrases = [
        "find customer",
        "search customer",
        "show customer",
        "get customer",
        "customer details",
    ]

    for phrase in customer_search_phrases:
        if phrase in text:
            return True

    # --------------------------------------------------------
    # 3. Customer / Khata balance
    # --------------------------------------------------------

    customer_balance_phrases = [
        "customer balance",
        "khata balance",
        "check khata",
        "check balance",
        "how much does",
        "how much owe",
        "owes",
        "outstanding balance",
    ]

    for phrase in customer_balance_phrases:
        if phrase in text:
            return True

    # --------------------------------------------------------
    # 4. Customer payment
    # --------------------------------------------------------

    payment_phrases = [
        "paid",
        "payment from",
        "record payment",
        "received payment",
        "khata payment",
    ]

    for phrase in payment_phrases:
        if phrase in text:

            # Avoid sending normal billing/payment
            # messages to the customer agent.

            billing_words = [
                "bill",
                "invoice",
                "sale",
                "selling",
                "cash",
                "upi",
                "card",
                "payment method",
            ]

            for word in billing_words:
                if word in text:
                    return False

            return True

    return False


# ============================================================
# MAIN ROUTER
# ============================================================

def ask_kirana_agent(user_message: str) -> str:
    """
    Route the Telegram message to the correct agent.

    Customer-related requests:
        -> customer_agent.py

    Everything else:
        -> inventory_agent.py
    """

    print("\n========================================")
    print("KIRANAAI ROUTER")
    print("========================================")

    print("User message:", user_message)

    # --------------------------------------------------------
    # Customer request
    # --------------------------------------------------------

    if is_customer_request(user_message):

        print("Route: CUSTOMER AGENT")

        return ask_customer_agent(user_message)

    # --------------------------------------------------------
    # Existing inventory / billing agent
    # --------------------------------------------------------

    print("Route: INVENTORY / BILLING AGENT")

    return ask_agent(user_message)