from ollama import chat

from app.tools.customer_tools import (
    create_customer_tool,
    find_customer_tool,
    customer_balance_tool,
    record_customer_payment_tool,
)


# ============================================================
# CUSTOMER AGENT
# ============================================================

def ask_customer_agent(user_message: str) -> str:

    print("1. Asking Qwen3 Customer Agent...")

    messages = [
        {
            "role": "system",
            "content": (
                "You are KiranaAI's customer management assistant.\n\n"

                "You help the supermarket owner manage customers "
                "and Khata balances.\n\n"

                "CUSTOMER CREATION:\n"
                "When the owner wants to add, create, register, "
                "or save a new customer, use create_customer_tool.\n\n"

                "Examples:\n"
                "Add customer Ravi\n"
                "Create customer Ravi\n"
                "Register Ravi\n"
                "Add Ravi with phone 9876543210\n\n"

                "CUSTOMER SEARCH:\n"
                "When the owner wants to find or search for a customer, "
                "use find_customer_tool.\n\n"

                "Examples:\n"
                "Find Ravi\n"
                "Search for Ravi\n"
                "Show customer Ravi\n\n"

                "CUSTOMER BALANCE:\n"
                "When the owner asks how much a customer owes or asks "
                "for a customer's Khata balance, use customer_balance_tool.\n\n"

                "Examples:\n"
                "What is Ravi's balance?\n"
                "How much does Ravi owe?\n"
                "Check Ravi's Khata\n\n"

                "KHATA PAYMENT:\n"
                "When the owner says that a customer has paid money "
                "towards their Khata, use record_customer_payment_tool.\n\n"

                "Examples:\n"
                "Ravi paid 500\n"
                "Ravi paid 500 rupees\n"
                "Record 500 payment from Ravi\n\n"

                "IMPORTANT:\n"
                "Do not invent customer information.\n"
                "Use the tools to create, find, or check customers.\n"
                "If the owner only gives a customer name, do not invent "
                "a phone number.\n"
            ),
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]


    # ============================================================
    # QWEN TOOL DEFINITIONS
    # ============================================================

    response = chat(
        model="qwen3:4b",
        messages=messages,
        tools=[
            create_customer_tool,
            find_customer_tool,
            customer_balance_tool,
            record_customer_payment_tool,
        ],
    )


    print("2. Qwen3 Customer Agent responded")

    print(
        "Tool calls:",
        response.message.tool_calls
    )


    # ============================================================
    # TOOL EXECUTION
    # ============================================================

    if response.message.tool_calls:

        for tool_call in response.message.tool_calls:

            tool_name = tool_call.function.name

            print(
                "Selected customer tool:",
                tool_name
            )


            # ====================================================
            # CREATE CUSTOMER
            # ====================================================

            if tool_name == "create_customer_tool":

                name = tool_call.function.arguments.get(
                    "name"
                )

                phone = tool_call.function.arguments.get(
                    "phone"
                )

                print(
                    "3. Executing create customer tool..."
                )

                print(
                    "Name:",
                    name
                )

                print(
                    "Phone:",
                    phone
                )

                result = create_customer_tool(
                    name=name,
                    phone=phone,
                )

                print(
                    "4. Tool result:"
                )

                print(result)


                if result.get("success"):

                    response_text = (
                        "👤 Customer added successfully!\n\n"
                        f"Name: {result['name']}\n"
                    )

                    if result.get("phone"):
                        response_text += (
                            f"Phone: {result['phone']}\n"
                        )

                    response_text += (
                        f"Customer ID: "
                        f"{result['customer_id']}"
                    )

                    return response_text


                return result.get(
                    "message",
                    "I couldn't create that customer."
                )


            # ====================================================
            # FIND CUSTOMER
            # ====================================================

            elif tool_name == "find_customer_tool":

                name = tool_call.function.arguments.get(
                    "name"
                )

                print(
                    "3. Executing find customer tool..."
                )

                print(
                    "Name:",
                    name
                )

                result = find_customer_tool(
                    name=name
                )

                print(
                    "4. Tool result:"
                )

                print(result)


                if result.get("success"):

                    phone = result.get(
                        "phone"
                    )

                    if not phone:
                        phone = "Not provided"

                    return (
                        "👤 Customer found\n\n"
                        f"Name: {result['name']}\n"
                        f"Phone: {phone}\n"
                        f"Khata balance: "
                        f"₹{result['balance']}"
                    )


                return result.get(
                    "message",
                    "I couldn't find that customer."
                )


            # ====================================================
            # CUSTOMER BALANCE
            # ====================================================

            elif tool_name == "customer_balance_tool":

                name = tool_call.function.arguments.get(
                    "name"
                )

                print(
                    "3. Executing customer balance tool..."
                )

                print(
                    "Name:",
                    name
                )

                result = customer_balance_tool(
                    name=name
                )

                print(
                    "4. Tool result:"
                )

                print(result)


                if result.get("success"):

                    return (
                        "📒 Khata Balance\n\n"
                        f"Customer: "
                        f"{result['customer_name']}\n"
                        f"Outstanding balance: "
                        f"₹{result['balance']}"
                    )


                return result.get(
                    "message",
                    "I couldn't find that customer's balance."
                )


            # ====================================================
            # RECORD CUSTOMER PAYMENT
            # ====================================================

            elif tool_name == "record_customer_payment_tool":

                name = tool_call.function.arguments.get(
                    "name"
                )

                amount = tool_call.function.arguments.get(
                    "amount"
                )

                note = tool_call.function.arguments.get(
                    "note"
                )

                print(
                    "3. Executing customer payment tool..."
                )

                print(
                    "Name:",
                    name
                )

                print(
                    "Amount:",
                    amount
                )

                print(
                    "Note:",
                    note
                )

                result = record_customer_payment_tool(
                    name=name,
                    amount=amount,
                    note=note,
                )

                print(
                    "4. Tool result:"
                )

                print(result)


                if result.get("success"):

                    return (
                        "💰 Khata payment recorded!\n\n"
                        f"Customer: "
                        f"{result['customer_name']}\n"
                        f"Amount paid: "
                        f"₹{result['payment']}\n"
                        f"Remaining balance: "
                        f"₹{result['balance']}"
                    )


                return result.get(
                    "message",
                    "I couldn't record the Khata payment."
                )


    # ============================================================
    # FALLBACK
    # ============================================================

    return "I couldn't understand the customer request."