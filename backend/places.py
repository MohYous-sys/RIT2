
import sqlite3
connection = sqlite3.connect('places.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS places (
place_id INTEGER PRIMARY KEY AUTOINCREMENT,
value_per_item REAL NOT NULL
)
''')



connection.commit()

cursor.execute("SELECT * FROM places")
places = cursor.fetchall()
for place in places:
    print("Place ID: {}, Value per Item: {}".format(place[0], place[1]))
    print("--------------------")

connection.close()

print('Places table created successfully.')