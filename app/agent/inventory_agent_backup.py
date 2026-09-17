import json

from ollama import chat

from app.tools.khata_tools import check_customer_balance
from app.tools.khata_payment_tools import record_customer_payment
from app.tools.invoice_tools import generate_invoice_tool
from app.tools.sales_tools import get_today_sales_tool
from app.tools.day_close_tools import get_day_close_tool
from app.tools.analysis_tools import generate_weekly_analysis_deck_tool
from app.database.connection import SessionLocal

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


# ============================================================
# INVENTORY TOOL WRAPPER
# ============================================================

def check_stock_tool(product_name: str) -> dict:
    """
    Wrapper around the inventory stock-check service.

    A fresh database session is created for every tool call.
    """

    from app.database.connection import SessionLocal

    db = SessionLocal()

    try:
        return check_stock(
            db=db,
            product_name=product_name,
        )

    finally:
        db.close()


# ============================================================
# TOOL REGISTRY
#
# The LLM selects a tool by name.
# The agent looks up the corresponding Python function here.
#
# This avoids a large if/elif tool dispatcher.
# ============================================================

TOOLS = {
    # Inventory
    "check_stock_tool": check_stock_tool,
    "receive_stock_tool": receive_stock_tool,

    # Multi-turn billing
    "start_bill_tool": start_bill_tool,
    "add_to_current_bill_tool": add_to_current_bill_tool,
    "update_current_bill_item_tool": update_current_bill_item_tool,
    "remove_from_current_bill_tool": remove_from_current_bill_tool,
    "get_current_bill_tool": get_current_bill_tool,
    "set_bill_payment_tool": set_bill_payment_tool,
    "finalize_current_bill_tool": finalize_current_bill_tool,

    # Khata
    "check_customer_balance": check_customer_balance,
    "record_customer_payment": record_customer_payment,

    # Documents
    "generate_invoice_tool": generate_invoice_tool,

    # Reports
    "get_today_sales_tool": get_today_sales_tool,
    "get_day_close_tool": get_day_close_tool,
    "generate_weekly_analysis_deck_tool": (
        generate_weekly_analysis_deck_tool
    ),

    # Memory
    "save_owner_preference": save_owner_preference,
    "get_owner_preference": get_owner_preference,
    "get_owner_preferences": get_owner_preferences,
    "delete_owner_preference": delete_owner_preference,
}


# ============================================================
# OLLAMA TOOL DEFINITIONS
#
# This is the list exposed to Qwen.
# ============================================================

AVAILABLE_TOOLS = list(TOOLS.values())


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are KiranaAI, a supermarket operations assistant for an
Indian kirana/supermarket owner.

Your job is to help the owner operate the shop through Telegram.

You can:

- check inventory
- receive stock
- create and manage bills
- update bill items
- remove bill items
- set payment methods
- finalize sales
- check customer Khata balances
- record Khata payments
- generate GST invoices
- show today's sales
- generate day-close reports
- generate weekly sales analysis PowerPoint decks
- remember owner preferences

IMPORTANT AGENT BEHAVIOUR
-------------------------

You are a tool-using agent.

When a request requires an operation:

1. Understand the owner's request.
2. Select the appropriate tool.
3. Execute the tool.
4. Carefully inspect the tool result.
5. If another tool is required, call the next tool.
6. Continue until the owner's request is completely handled.
7. Only then give the final answer.

Do NOT stop after the first tool call if the task requires
additional steps.

Use the results returned by tools as the source of truth.

Do not invent database values, stock quantities, bill totals,
customer balances, GST values, or saved preferences.

If a tool reports an error, explain that error clearly to the
owner instead of pretending the operation succeeded.


MULTI-TURN BILLING
------------------

Use the multi-turn billing tools for normal billing.

When the owner wants to start, create, open, or make a bill:

Use:
start_bill_tool

Examples:

"Start a bill"
"Create a new bill"
"Open a bill"
"Make a bill"


When the owner gives a product and quantity for the current bill:

Use:
add_to_current_bill_tool

Examples:

"2 kg rice"
"Add 3 packets of biscuits"
"Put 1 litre oil in the bill"
"Add 2 soaps"


When the owner changes an existing item's quantity:

Use:
update_current_bill_item_tool

Examples:

"Change rice to 3 kg"
"Make sugar quantity 5 kg"
"Update oil quantity to 2 litres"


When the owner removes an item:

Use:
remove_from_current_bill_tool

Examples:

"Remove rice"
"Take sugar out"
"Remove the soap"


When the owner asks to see the current bill or total:

Use:
get_current_bill_tool

Examples:

"Show the bill"
"What's the total?"
"Show current bill"
"How much is the bill?"
"Give me the bill summary"


When the owner explicitly gives a payment method for the
current bill:

Use:
set_bill_payment_tool

Supported payment methods include:

- cash
- UPI
- card
- credit

Do not assume a payment method unless the owner explicitly
provides one.

When the owner asks to finalize, complete, or finish the bill:

Use:
finalize_current_bill_tool

Do not finalize unless the payment method has been selected.

Draft bills do not reduce inventory.

Inventory is reduced only when finalization succeeds.

If finalization fails because of insufficient stock or another
business rule, report the tool result honestly.


INVENTORY
---------

For stock questions use:

check_stock_tool

For receiving stock use:

receive_stock_tool

Do not invent stock quantities.

The database result is authoritative.


KHATA
------

For checking a customer's outstanding balance use:

check_customer_balance

For recording a customer's Khata payment use:

record_customer_payment

Do not invent customer balances.

Do not claim a payment succeeded unless the tool reports success.


GST INVOICES
------------

When the owner asks for an invoice for a finalized bill:

Use:
generate_invoice_tool

The tool generates the actual GST invoice PDF.

Do not claim that an invoice was generated unless the tool
reports success.


SALES REPORTS
-------------

When the owner asks for today's sales:

Use:
get_today_sales_tool

When the owner asks for day close:

Use:
get_day_close_tool


WEEKLY ANALYSIS
---------------

When the owner asks for:

- weekly sales report
- weekly sales analysis
- business analysis
- weekly report
- sales PowerPoint
- PPT
- PPTX
- analysis deck

Use:
generate_weekly_analysis_deck_tool

The tool generates the actual PowerPoint file.

Do not claim that a PowerPoint was generated unless the tool
reports success.


OWNER MEMORY
------------

When the owner says:

- remember
- save
- store
- remember this

and is clearly asking you to remember a shop preference:

Use:
save_owner_preference

Use simple preference keys such as:

shop_opening_time
shop_closing_time
preferred_payment_method

When the owner asks what you remember or asks for all saved
preferences:

Use:
get_owner_preferences

When the owner asks about one specific preference:

Use:
get_owner_preference

When the owner says forget, remove, delete, or stop remembering
a preference:

Use:
delete_owner_preference

Never invent saved preferences.


FINAL RESPONSE
--------------

After completing the required tool operations, give the owner a
short, clear response.

For simple operations, include the important result.

For example:

"Rice stock is 32 kg."

or:

"Bill #12 was finalized successfully. Total: ₹525. Payment:
UPI. Stock has been updated."

Do not expose internal tool names or implementation details
unless the owner specifically asks about them.
"""


# ============================================================
# TOOL RESULT SERIALIZATION
# ============================================================

def serialize_tool_result(result) -> str:
    """
    Convert a Python tool result into text that Qwen can inspect.
    """

    if isinstance(result, str):
        return result

    try:
        return json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )

    except Exception:
        return str(result)


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(tool_name: str, arguments: dict):
    """
    Execute a selected tool from the registry.

    This is the generic tool executor used by the agent loop.
    """

    tool = TOOLS.get(tool_name)

    if tool is None:

        return {
            "success": False,
            "error": (
                f"Unknown tool requested: {tool_name}"
            ),
        }

    if arguments is None:
        arguments = {}

    try:

        print(
            f"Executing tool: {tool_name}"
        )

        print(
            f"Arguments: {arguments}"
        )

        result = tool(**arguments)

        print(
            f"Tool result: {result}"
        )

        return result

    except Exception as e:

        print(
            f"Tool execution error in "
            f"{tool_name}: {e}"
        )

        return {
            "success": False,
            "error": str(e),
            "tool": tool_name,
        }


# ============================================================
# SPECIAL DOCUMENT RESPONSES
# ============================================================

def get_special_response(
    tool_name: str,
    result,
):
    """
    Some tools generate actual files.

    Telegram bot.py already knows how to handle these markers.

    Returns:
        special response string, or None
    """

    if not isinstance(result, dict):
        return None

    if not result.get("success"):
        return None

    # --------------------------------------------------------
    # GST INVOICE
    # --------------------------------------------------------

    if tool_name == "generate_invoice_tool":

        pdf_path = result.get("pdf_path")

        if pdf_path:

            return (
                "__INVOICE__:"
                f"{pdf_path}"
            )

    # --------------------------------------------------------
    # WEEKLY ANALYSIS DECK
    # --------------------------------------------------------

    if tool_name == "generate_weekly_analysis_deck_tool":

        file_path = result.get("file_path")

        if file_path:

            return (
                "__ANALYSIS_DECK__:"
                f"{file_path}"
            )

    return None


# ============================================================
# MAIN AGENT
# ============================================================

def ask_agent(user_message: str) -> str:

    print()
    print("=" * 60)
    print("KiranaAI Agent")
    print("=" * 60)
    print(
        "User:",
        user_message
    )

    # --------------------------------------------------------
    # INITIAL CONVERSATION
    # --------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    # --------------------------------------------------------
    # AGENT CONTROL LOOP
    #
    # Observe
    #   ↓
    # Reason
    #   ↓
    # Act
    #   ↓
    # Observe tool result
    #   ↓
    # Reason again
    #   ↓
    # Continue or finish
    # --------------------------------------------------------

    max_iterations = 10

    for iteration in range(1, max_iterations + 1):

        print()
        print(
            f"Agent iteration: {iteration}"
        )

        # ----------------------------------------------------
        # ASK QWEN
        # ----------------------------------------------------

        print(
            "Asking Qwen3..."
        )

        response = chat(
            model="qwen3:4b",
            messages=messages,
            tools=AVAILABLE_TOOLS,
        )

        print(
            "Qwen3 responded."
        )

        # ----------------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # ----------------------------------------------------

        messages.append(
            response.message
        )

        tool_calls = (
            response.message.tool_calls
            or []
        )

        print(
            "Tool calls:",
            tool_calls
        )

        # ----------------------------------------------------
        # NO TOOL CALL
        #
        # Qwen has completed the task and produced its
        # final natural-language response.
        # ----------------------------------------------------

        if not tool_calls:

            final_response = (
                response.message.content
                or "Done."
            )

            print()
            print(
                "Final response:",
                final_response
            )

            print(
                "=" * 60
            )

            return final_response

        # ----------------------------------------------------
        # EXECUTE ALL REQUESTED TOOLS
        # ----------------------------------------------------

        stop_after_tool = None

        for tool_call in tool_calls:

            tool_name = (
                tool_call.function.name
            )

            arguments = (
                tool_call.function.arguments
                or {}
            )

            print()
            print(
                "Selected tool:",
                tool_name
            )

            print(
                "Arguments:",
                arguments
            )

            # ------------------------------------------------
            # EXECUTE TOOL
            # ------------------------------------------------

            result = execute_tool(
                tool_name=tool_name,
                arguments=arguments,
            )

            # ------------------------------------------------
            # CHECK FOR SPECIAL FILE RESPONSE
            # ------------------------------------------------

            special_response = (
                get_special_response(
                    tool_name=tool_name,
                    result=result,
                )
            )

            if special_response:

                stop_after_tool = (
                    special_response
                )

            # ------------------------------------------------
            # FEED TOOL RESULT BACK TO QWEN
            # ------------------------------------------------

            tool_result_text = (
                serialize_tool_result(
                    result
                )
            )

            messages.append(
                {
                    "role": "tool",
                    "content": tool_result_text,
                }
            )

            print(
                "Tool result sent back to Qwen."
            )

            # ------------------------------------------------
            # If a generated document was created, Telegram
            # needs the special marker instead of asking Qwen
            # to describe the file.
            # ------------------------------------------------

            if stop_after_tool:

                print(
                    "Generated file detected:"
                )

                print(
                    stop_after_tool
                )

                print(
                    "=" * 60
                )

                return stop_after_tool

    # --------------------------------------------------------
    # SAFETY FALLBACK
    #
    # Prevent an accidental infinite agent loop.
    # --------------------------------------------------------

    print(
        "Maximum agent iterations reached."
    )

    print(
        "=" * 60
    )

    return (
        "I couldn't complete the request within "
        "the allowed number of steps. "
        "Please try again."
    )