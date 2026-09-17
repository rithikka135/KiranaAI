from app.database.connection import SessionLocal
from app.tools.inventory_tools import check_stock


db = SessionLocal()

try:
    result = check_stock(
        db=db,
        product_name="rice",
    )

    print(result)

finally:
    db.close()