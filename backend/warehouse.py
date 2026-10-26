
import sqlite3
connection = sqlite3.connect('warehouse.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS warehouse_inventory (warehouse_id INTEGER PRIMARY KEY AUTOINCREMENT,
item_name TEXT NOT NULL,
quantity INTEGER NOT NULL DEFAULT 0)
''')


#cursor.execute('''INSERT INTO warehouse_inventory (item_name, quantity) VALUES
#(?, ?)''', ('Item A', 100))

connection.commit()

cursor.execute("SELECT * FROM warehouse_inventory")
items = cursor.fetchall()
for item in items:
    print("Warehouse ID: {}, Item Name: {}, Quantity: {}".format(item[0], item[1], item[2]))
    print("--------------------")
connection.close()

print('Warehouse inventory table created successfully.')