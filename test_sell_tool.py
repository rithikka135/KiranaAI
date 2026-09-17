from app.tools.billing_tools import sell_product_tool

result = sell_product_tool(
    product_name="rice",
    quantity=2,
)

print("\nKiranaAI:")
print(result)