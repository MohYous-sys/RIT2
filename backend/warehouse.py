
try:
    from .database import get_db_connection, init_databases
except ImportError:
    from database import get_db_connection, init_databases


init_databases()
connection = get_db_connection()
items = connection.execute(
    "SELECT warehouse_id, item_name, quantity, status FROM warehouse_inventory"
).fetchall()
for item in items:
    print(
        "Warehouse ID: {}, Item Name: {}, Quantity: {}, Status: {}".format(
            item["warehouse_id"], item["item_name"], item["quantity"], item["status"]
        )
    )
    print("--------------------")
connection.close()

print('Warehouse inventory table created successfully.')