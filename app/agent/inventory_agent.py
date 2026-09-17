from ollama import chat

from app.database.connection import SessionLocal

from app.tools.khata_tools import check_customer_balance
from app.tools.khata_payment_tools import record_customer_payment
from app.tools.invoice_tools import generate_invoice_tool
from app.tools.sales_tools import get_today_sales_tool
from app.tools.day_close_tools import get_day_close_tool
from app.tools.analysis_tools import generate_weekly_analysis_deck_tool

from app.tools.multi_turn_billing_tools import (
    start_bill_tool,
    add_to_current_bill_tool,
    update_current_bill_item_tool,
    remove_from_current_bill_tool,
    get_current_bill_tool,
    set_bill_payment_tool,
    finalize_current_bill_tool,
)

from app.tools.memory_tools import (
    save_owner_preference,
    get_owner_preference,
    get_owner_preferences,
    delete_owner_preference,
)

from app.tools.inventory_tools import (
    check_stock,
    receive_stock_tool,
)

from app.tools.billing_tools import sell_product_tool


# ============================================================
# INVENTORY TOOL WRAPPER
# ============================================================

def check_stock_tool(product_name: str) -> dict:
    db = SessionLocal()

    try:
        return check_stock(
            db=db,
            product_name=product_name
        )

    finally:
        db.close()


# ============================================================
# LEGACY PAYMENT DETECTION
# Used only by the old one-shot sell_product_tool
# ============================================================

def detect_payment_method(user_message: str) -> str:
    message = user_message.lower()

    if "upi" in message:
        return "upi"

    if "card" in message:
        return "card"

    if "cash" in message:
        return "cash"

    if "credit" in message or "khata" in message:
        return "credit"

    return "cash"


def detect_customer_name(user_message: str) -> str:
    message = user_message.lower()

    if " to " in message:
        after_to = message.split(" to ", 1)[1]

        if " on credit" in after_to:
            return after_to.split(
                " on credit",
                1
            )[0].strip()

        if " on khata" in after_to:
            return after_to.split(
                " on khata",
                1
            )[0].strip()

    return ""


# ============================================================
# MAIN AGENT
# ============================================================

def ask_agent(user_message: str) -> str:

    print("1. Asking Qwen3...")

    messages = [
        {
            "role": "system",
            "content": (
                "You are KiranaAI, a supermarket operations assistant.\n\n"

                "You help the supermarket owner with:\n"
                "- checking inventory\n"
                "- receiving stock\n"
                "- creating and managing bills\n"
                "- selling products\n"
                "- customer Khata\n"
                "- recording Khata payments\n"
                "- generating GST invoices\n"
                "- today's sales\n"
                "- day close reports\n"
                "- generating weekly sales analysis PowerPoint decks\n"
                "- remembering owner preferences\n\n"


                # ====================================================
                # MULTI-TURN BILLING
                # ====================================================

                "MULTI-TURN BILLING RULES:\n\n"

                "Use the multi-turn billing tools for normal "
                "customer billing conversations.\n\n"

                "When the owner says they want to start, create, "
                "open, or make a bill, use start_bill_tool.\n\n"

                "Examples:\n"
                "Start a bill\n"
                "Create a new bill\n"
                "Open a bill\n"
                "Make a bill\n\n"

                "When the owner gives a product and quantity for "
                "the current bill, use add_to_current_bill_tool.\n\n"

                "Examples:\n"
                "2 kg rice\n"
                "Add 3 packets of biscuits\n"
                "Put 1 litre oil in the bill\n"
                "Add 2 soaps\n\n"

                "When the owner asks to change or update the "
                "quantity of an existing item, use "
                "update_current_bill_item_tool.\n\n"

                "Examples:\n"
                "Change rice to 3 kg\n"
                "Make sugar quantity 5 kg\n"
                "Update oil quantity to 2 litres\n\n"

                "When the owner asks to remove an item from the "
                "current bill, use remove_from_current_bill_tool.\n\n"

                "Examples:\n"
                "Remove rice\n"
                "Take sugar out of the bill\n"
                "Remove the soap\n\n"

                "When the owner asks for the bill, total, current "
                "bill, bill summary, or amount, use "
                "get_current_bill_tool.\n\n"

                "Examples:\n"
                "Show the bill\n"
                "What's the total?\n"
                "Show current bill\n"
                "How much is the bill?\n"
                "Give me the bill summary\n\n"

                "When the owner specifies cash, UPI, or card for "
                "the current bill, use set_bill_payment_tool.\n\n"

                "Examples:\n"
                "Cash\n"
                "Payment is UPI\n"
                "Customer paid by card\n"
                "Set payment to UPI\n\n"

                "Do not assume a payment method for the current "
                "multi-turn bill unless the owner explicitly "
                "provides it.\n\n"

                "When the owner asks to finalize, complete, or "
                "finish the current bill, use "
                "finalize_current_bill_tool.\n\n"

                "Do not finalize a bill unless a payment method "
                "has been selected.\n\n"

                "Draft bills do not reduce inventory.\n"

                "Inventory is reduced only when the finalization "
                "tool succeeds.\n\n"

                "Do not use the old sell_product_tool for normal "
                "multi-turn billing conversations when the owner "
                "is building a bill across multiple messages.\n\n"


                # ====================================================
                # WEEKLY ANALYSIS
                # ====================================================

                "WEEKLY ANALYSIS RULES:\n"

                "When the owner asks for a weekly sales report, "
                "weekly sales analysis, business analysis, weekly "
                "report, sales PowerPoint, PPT, PPTX, or analysis "
                "deck, use generate_weekly_analysis_deck_tool.\n\n"

                "The analysis tool generates the actual PowerPoint "
                "file using the supermarket's sales and inventory "
                "data.\n\n"

                "Do not claim that you cannot generate PowerPoint "
                "files. Use the analysis tool.\n\n"


                # ====================================================
                # OWNER MEMORY
                # ====================================================

                "OWNER MEMORY RULES:\n"

                "When the owner says 'remember', 'save', 'store', "
                "or clearly asks you to remember a shop preference, "
                "use save_owner_preference.\n\n"

                "Examples:\n"
                "Remember that my shop opens at 8 AM.\n"
                "Remember that my shop closes at 9 PM.\n"
                "Remember that my preferred payment method is UPI.\n\n"

                "Use simple preference keys such as:\n"
                "shop_opening_time\n"
                "shop_closing_time\n"
                "preferred_payment_method\n\n"

                "When the owner asks what you remember, what "
                "preferences are saved, or asks for all saved "
                "preferences, use get_owner_preferences.\n\n"

                "When the owner asks about one specific preference, "
                "use get_owner_preference.\n\n"

                "When the owner says forget, remove, delete, or "
                "stop remembering a preference, use "
                "delete_owner_preference.\n\n"

                "Do not invent saved preferences. Use the memory "
                "tools to retrieve them."
            ),
        },

        {
            "role": "user",
            "content": user_message
        },
    ]


    # ============================================================
    # QWEN TOOL DEFINITIONS
    # ============================================================

    response = chat(
        model="qwen3:4b",

        messages=messages,

        tools=[
            # Inventory
            check_stock_tool,
            receive_stock_tool,

            # Legacy one-shot billing
            sell_product_tool,

            # Multi-turn billing
            start_bill_tool,
            add_to_current_bill_tool,
            update_current_bill_item_tool,
            remove_from_current_bill_tool,
            get_current_bill_tool,
            set_bill_payment_tool,
            finalize_current_bill_tool,

            # Khata
            check_customer_balance,
            record_customer_payment,

            # Documents
            generate_invoice_tool,

            # Reports
            get_today_sales_tool,
            get_day_close_tool,
            generate_weekly_analysis_deck_tool,

            # Memory
            save_owner_preference,
            get_owner_preference,
            get_owner_preferences,
            delete_owner_preference,
        ],
    )


    print("2. Qwen3 responded")

    print(
        "Tool calls:",
        response.message.tool_calls
    )


    messages.append(response.message)


    # ============================================================
    # TOOL EXECUTION
    # ============================================================

    if response.message.tool_calls:

        for tool_call in response.message.tool_calls:

            tool_name = tool_call.function.name

            print(
                "Selected tool:",
                tool_name
            )


            # ====================================================
            # CHECK STOCK
            # ====================================================

            if tool_name == "check_stock_tool":

                product_name = (
                    tool_call.function.arguments[
                        "product_name"
                    ]
                )

                print(
                    "3. Executing stock check tool..."
                )

                print(
                    "Product:",
                    product_name
                )

                result = check_stock_tool(
                    product_name
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"We currently have "
                        f"{result['quantity']} "
                        f"{result['unit']} of "
                        f"{result['product_name']} "
                        f"in stock."
                    )

                return result.get(
                    "message",
                    "I couldn't find that product."
                )


            # ====================================================
            # RECEIVE STOCK
            # ====================================================

            elif tool_name == "receive_stock_tool":

                product_name = (
                    tool_call.function.arguments[
                        "product_name"
                    ]
                )

                quantity = (
                    tool_call.function.arguments[
                        "quantity"
                    ]
                )

                print(
                    "3. Executing receive stock tool..."
                )

                print(
                    "Product:",
                    product_name
                )

                print(
                    "Quantity:",
                    quantity
                )

                result = receive_stock_tool(
                    product_name,
                    quantity
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"Received "
                        f"{result['quantity_received']} "
                        f"{result['unit']} of "
                        f"{result['product_name']}.\n\n"
                        f"Current stock: "
                        f"{result['current_stock']} "
                        f"{result['unit']}."
                    )

                return result.get(
                    "message",
                    "I couldn't receive that stock."
                )


            # ====================================================
            # START BILL
            # ====================================================

            elif tool_name == "start_bill_tool":

                print(
                    "3. Executing start bill tool..."
                )

                result = start_bill_tool()

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        "🧾 New bill started.\n\n"
                        f"Bill ID: #{result['bill_id']}\n\n"
                        "Tell me the products and "
                        "quantities to add."
                    )

                return result.get(
                    "message",
                    "I couldn't start the bill."
                )


            # ====================================================
            # ADD PRODUCT TO CURRENT BILL
            # ====================================================

            elif tool_name == "add_to_current_bill_tool":

                product_name = (
                    tool_call.function.arguments[
                        "product_name"
                    ]
                )

                quantity = (
                    tool_call.function.arguments[
                        "quantity"
                    ]
                )

                print(
                    "3. Executing add-to-current-bill tool..."
                )

                print(
                    "Product:",
                    product_name
                )

                print(
                    "Quantity:",
                    quantity
                )

                result = add_to_current_bill_tool(
                    product_name,
                    quantity
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"✅ Added to bill "
                        f"#{result['bill_id']}\n\n"

                        f"Product: "
                        f"{result['product_name']}\n"

                        f"Quantity: "
                        f"{result['quantity']} "
                        f"{result['unit']}\n"

                        f"Price: ₹"
                        f"{result['unit_price']}\n"

                        f"GST: "
                        f"{result['gst_rate']}%\n\n"

                        f"Current total: ₹"
                        f"{result['total']}"
                    )

                return result.get(
                    "message",
                    "I couldn't add that product."
                )


            # ====================================================
            # UPDATE CURRENT BILL ITEM
            # ====================================================

            elif tool_name == "update_current_bill_item_tool":

                product_name = (
                    tool_call.function.arguments[
                        "product_name"
                    ]
                )

                quantity = (
                    tool_call.function.arguments[
                        "quantity"
                    ]
                )

                print(
                    "3. Executing update bill item tool..."
                )

                print(
                    "Product:",
                    product_name
                )

                print(
                    "New quantity:",
                    quantity
                )

                result = update_current_bill_item_tool(
                    product_name,
                    quantity
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"✏️ Updated "
                        f"{result['product_name']} "
                        f"to {result['quantity']} "
                        f"{result['unit']}.\n\n"

                        f"Current total: ₹"
                        f"{result['total']}"
                    )

                return result.get(
                    "message",
                    "I couldn't update that item."
                )


            # ====================================================
            # REMOVE CURRENT BILL ITEM
            # ====================================================

            elif tool_name == "remove_from_current_bill_tool":

                product_name = (
                    tool_call.function.arguments[
                        "product_name"
                    ]
                )

                print(
                    "3. Executing remove bill item tool..."
                )

                print(
                    "Product:",
                    product_name
                )

                result = remove_from_current_bill_tool(
                    product_name
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"🗑️ Removed "
                        f"{result['product_name']} "
                        f"from bill "
                        f"#{result['bill_id']}.\n\n"

                        f"Current total: ₹"
                        f"{result['total']}"
                    )

                return result.get(
                    "message",
                    "I couldn't remove that item."
                )


            # ====================================================
            # CURRENT BILL SUMMARY
            # ====================================================

            elif tool_name == "get_current_bill_tool":

                print(
                    "3. Executing current bill tool..."
                )

                result = get_current_bill_tool()

                print(
                    "4. Tool result:"
                )

                print(result)

                if not result.get("success"):

                    return result.get(
                        "message",
                        "There is no active bill."
                    )

                response_text = (
                    f"🧾 Bill #{result['bill_id']}\n\n"
                )

                items = result.get(
                    "items",
                    []
                )

                if not items:

                    response_text += (
                        "No items added yet.\n"
                    )

                else:

                    for item in items:

                        response_text += (
                            f"• "
                            f"{item['quantity']} "
                            f"{item['unit']} "
                            f"{item['product_name']} "
                            f"@ ₹{item['unit_price']}\n"
                        )

                response_text += (
                    "\n"
                    f"Subtotal: ₹"
                    f"{result['subtotal']}\n"

                    f"CGST: ₹"
                    f"{result['cgst']}\n"

                    f"SGST: ₹"
                    f"{result['sgst']}\n"

                    f"Total GST: ₹"
                    f"{result['total_tax']}\n"

                    f"Total: ₹"
                    f"{result['total']}"
                )

                if result.get(
                    "payment_method"
                ):

                    response_text += (
                        "\nPayment: "
                        f"{result['payment_method']}"
                    )

                return response_text


            # ====================================================
            # SET PAYMENT
            # ====================================================

            elif tool_name == "set_bill_payment_tool":

                payment_method = (
                    tool_call.function.arguments[
                        "payment_method"
                    ]
                )

                print(
                    "3. Executing bill payment tool..."
                )

                print(
                    "Payment:",
                    payment_method
                )

                result = set_bill_payment_tool(
                    payment_method
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        "💳 Payment method set to "
                        f"{result['payment_method'].upper()}.\n\n"

                        f"Bill total: ₹"
                        f"{result['total']}\n\n"

                        "Say 'finalize bill' "
                        "to complete the sale."
                    )

                return result.get(
                    "message",
                    "I couldn't set the payment method."
                )


            # ====================================================
            # FINALIZE BILL
            # ====================================================

            elif tool_name == "finalize_current_bill_tool":

                print(
                    "3. Executing finalize current bill tool..."
                )

                result = finalize_current_bill_tool()

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"✅ Bill #{result['bill_id']} "
                        "finalized successfully!\n\n"

                        f"Subtotal: ₹"
                        f"{result['subtotal']}\n"

                        f"CGST: ₹"
                        f"{result['cgst']}\n"

                        f"SGST: ₹"
                        f"{result['sgst']}\n"

                        f"Total GST: ₹"
                        f"{result['total_tax']}\n"

                        f"Total: ₹"
                        f"{result['total']}\n"

                        f"Payment: "
                        f"{result['payment_method'].upper()}\n\n"

                        "📦 Stock has been updated."
                    )

                return result.get(
                    "message",
                    "I couldn't finalize the bill."
                )


            # ====================================================
            # CUSTOMER KHATA BALANCE
            # ====================================================

            elif tool_name == "check_customer_balance":

                customer_name = (
                    tool_call.function.arguments[
                        "customer_name"
                    ]
                )

                print(
                    "3. Executing customer balance tool..."
                )

                print(
                    "Customer:",
                    customer_name
                )

                result = check_customer_balance(
                    customer_name
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"📒 "
                        f"{result['customer_name']}'s Khata\n\n"

                        f"Outstanding balance: ₹"
                        f"{result['balance']}"
                    )

                return result.get(
                    "message",
                    "I couldn't find that customer."
                )


            # ====================================================
            # KHATA PAYMENT
            # ====================================================

            elif tool_name == "record_customer_payment":

                customer_name = (
                    tool_call.function.arguments[
                        "customer_name"
                    ]
                )

                amount = (
                    tool_call.function.arguments[
                        "amount"
                    ]
                )

                print(
                    "3. Executing Khata payment tool..."
                )

                print(
                    "Customer:",
                    customer_name
                )

                print(
                    "Amount:",
                    amount
                )

                result = record_customer_payment(
                    customer_name,
                    amount
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

                        f"Amount paid: ₹"
                        f"{result['amount']}"
                    )

                return result.get(
                    "message",
                    "I couldn't record the Khata payment."
                )


            # ====================================================
            # INVOICE
            # ====================================================

            elif tool_name == "generate_invoice_tool":

                bill_id = (
                    tool_call.function.arguments[
                        "bill_id"
                    ]
                )

                print(
                    "3. Executing invoice generation tool..."
                )

                print(
                    "Bill ID:",
                    bill_id
                )

                result = generate_invoice_tool(
                    bill_id
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"__INVOICE__:"
                        f"{result['pdf_path']}"
                    )

                return result.get(
                    "message",
                    "I couldn't generate the invoice."
                )


            # ====================================================
            # WEEKLY ANALYSIS DECK
            # ====================================================

            elif tool_name == "generate_weekly_analysis_deck_tool":

                print(
                    "3. Executing weekly analysis deck tool..."
                )

                result = (
                    generate_weekly_analysis_deck_tool()
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"__ANALYSIS_DECK__:"
                        f"{result['file_path']}"
                    )

                return result.get(
                    "message",
                    "I couldn't generate the weekly "
                    "analysis deck."
                )


            # ====================================================
            # LEGACY ONE-SHOT SALE
            # ====================================================

            elif tool_name == "sell_product_tool":

                product_name = (
                    tool_call.function.arguments[
                        "product_name"
                    ]
                )

                quantity = (
                    tool_call.function.arguments[
                        "quantity"
                    ]
                )

                payment_method = (
                    detect_payment_method(
                        user_message
                    )
                )

                customer_name = ""

                if payment_method == "credit":

                    customer_name = (
                        detect_customer_name(
                            user_message
                        )
                    )

                print(
                    "3. Executing legacy "
                    "sell product tool..."
                )

                print(
                    "Product:",
                    product_name
                )

                print(
                    "Quantity:",
                    quantity
                )

                print(
                    "Payment:",
                    payment_method
                )

                print(
                    "Customer:",
                    customer_name
                )

                result = sell_product_tool(
                    product_name,
                    quantity,
                    payment_method,
                    customer_name
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    customer_text = ""

                    if result.get(
                        "customer_name"
                    ):

                        customer_text = (
                            "\nCustomer: "
                            f"{result['customer_name']}"
                        )

                    return (
                        "🧾 Sale completed!\n\n"

                        f"Product: "
                        f"{result['product_name']}\n"

                        f"Quantity: "
                        f"{result['quantity']} "
                        f"{result['unit']}"

                        f"{customer_text}\n\n"

                        f"Subtotal: ₹"
                        f"{result['subtotal']}\n"

                        f"CGST: ₹"
                        f"{result['cgst']}\n"

                        f"SGST: ₹"
                        f"{result['sgst']}\n"

                        f"Total: ₹"
                        f"{result['total']}\n"

                        f"Payment: "
                        f"{result['payment_method']}\n\n"

                        f"Bill ID: "
                        f"{result['bill_id']}"
                    )

                return result.get(
                    "message",
                    "I couldn't complete the sale."
                )


            # ====================================================
            # TODAY'S SALES
            # ====================================================

            elif tool_name == "get_today_sales_tool":

                print(
                    "3. Executing daily sales tool..."
                )

                result = get_today_sales_tool()

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        "📊 Today's Sales\n\n"

                        f"Bills: "
                        f"{result['bill_count']}\n"

                        f"Total Sales: ₹"
                        f"{result['total_sales']}\n\n"

                        f"💵 Cash: ₹"
                        f"{result['cash_sales']}\n"

                        f"📱 UPI: ₹"
                        f"{result['upi_sales']}\n"

                        f"💳 Card: ₹"
                        f"{result['card_sales']}\n"

                        f"📒 Credit: ₹"
                        f"{result['credit_sales']}"
                    )

                return result.get(
                    "message",
                    "I couldn't calculate today's sales."
                )


            # ====================================================
            # DAY CLOSE
            # ====================================================

            elif tool_name == "get_day_close_tool":

                print(
                    "3. Executing day close tool..."
                )

                result = get_day_close_tool()

                print(
                    "4. Tool result:"
                )

                print(result)

                if not result.get("success"):

                    return result.get(
                        "message",
                        "I couldn't generate "
                        "the day close report."
                    )

                low_stock = result.get(
                    "low_stock_products",
                    []
                )

                best_selling = result.get(
                    "best_selling_product"
                )

                response_text = (
                    f"🌙 Day Close — "
                    f"{result['date']}\n\n"

                    "📊 SALES\n"

                    f"Bills: "
                    f"{result['bill_count']}\n"

                    f"Total Sales: ₹"
                    f"{result['total_sales']}\n\n"

                    "💰 PAYMENT BREAKDOWN\n"

                    f"💵 Cash: ₹"
                    f"{result['cash_sales']}\n"

                    f"📱 UPI: ₹"
                    f"{result['upi_sales']}\n"

                    f"💳 Card: ₹"
                    f"{result['card_sales']}\n"

                    f"📒 Credit: ₹"
                    f"{result['credit_sales']}\n\n"

                    "🧾 GST\n"

                    f"CGST: ₹"
                    f"{result['cgst']}\n"

                    f"SGST: ₹"
                    f"{result['sgst']}\n"

                    f"Total GST: ₹"
                    f"{result['total_gst']}\n\n"

                    "📒 KHATA\n"

                    f"Credit given today: ₹"
                    f"{result['credit_given_today']}\n"

                    f"Payments received: ₹"
                    f"{result['khata_payments_today']}\n\n"
                )

                if best_selling:

                    response_text += (
                        "🏆 BEST SELLING PRODUCT\n"

                        f"{best_selling['product_name']} — "

                        f"{best_selling['quantity']} "

                        f"{best_selling['unit']}\n\n"
                    )

                else:

                    response_text += (
                        "🏆 BEST SELLING PRODUCT\n"
                        "No sales recorded today.\n\n"
                    )

                response_text += (
                    "📦 LOW STOCK\n"
                )

                if low_stock:

                    for product in low_stock:

                        response_text += (
                            f"⚠️ "
                            f"{product['product_name']}: "

                            f"{product['quantity']} "

                            f"{product['unit']} "

                            f"(reorder at "

                            f"{product['reorder_level']})\n"
                        )

                else:

                    response_text += (
                        "✅ No products are below "
                        "their reorder level.\n"
                    )

                response_text += (
                    "\n✅ Day close report generated."
                )

                return response_text


            # ====================================================
            # SAVE OWNER PREFERENCE
            # ====================================================

            elif tool_name == "save_owner_preference":

                key = (
                    tool_call.function.arguments[
                        "key"
                    ]
                )

                value = (
                    tool_call.function.arguments[
                        "value"
                    ]
                )

                print(
                    "3. Saving owner preference..."
                )

                print(
                    "Key:",
                    key
                )

                print(
                    "Value:",
                    value
                )

                result = save_owner_preference(
                    key,
                    value
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        "🧠 Preference remembered!\n\n"

                        f"{result['key']}: "
                        f"{result['value']}"
                    )

                return result.get(
                    "message",
                    "I couldn't save that preference."
                )


            # ====================================================
            # GET ONE OWNER PREFERENCE
            # ====================================================

            elif tool_name == "get_owner_preference":

                key = (
                    tool_call.function.arguments[
                        "key"
                    ]
                )

                print(
                    "3. Getting owner preference..."
                )

                print(
                    "Key:",
                    key
                )

                result = get_owner_preference(
                    key
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"🧠 {result['key']}: "
                        f"{result['value']}"
                    )

                return result.get(
                    "message",
                    "I couldn't find that preference."
                )


            # ====================================================
            # GET ALL OWNER PREFERENCES
            # ====================================================

            elif tool_name == "get_owner_preferences":

                print(
                    "3. Getting owner preferences..."
                )

                result = get_owner_preferences()

                print(
                    "4. Tool result:"
                )

                print(result)

                if not result.get("success"):

                    return (
                        "I couldn't retrieve "
                        "your preferences."
                    )

                preferences = result.get(
                    "preferences",
                    []
                )

                if not preferences:

                    return (
                        "🧠 You don't have any "
                        "saved preferences yet."
                    )

                response_text = (
                    "🧠 Saved Preferences\n\n"
                )

                for preference in preferences:

                    response_text += (
                        f"• {preference['key']}: "
                        f"{preference['value']}\n"
                    )

                return response_text


            # ====================================================
            # DELETE OWNER PREFERENCE
            # ====================================================

            elif tool_name == "delete_owner_preference":

                key = (
                    tool_call.function.arguments[
                        "key"
                    ]
                )

                print(
                    "3. Deleting owner preference..."
                )

                print(
                    "Key:",
                    key
                )

                result = delete_owner_preference(
                    key
                )

                print(
                    "4. Tool result:"
                )

                print(result)

                if result.get("success"):

                    return (
                        f"🗑️ Preference "
                        f"'{key}' deleted."
                    )

                return result.get(
                    "message",
                    "I couldn't delete "
                    "that preference."
                )


    # ============================================================
    # FALLBACK
    # ============================================================

    return "I couldn't understand your request."
