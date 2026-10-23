
import sqlite3 
connection = sqlite3.connect('rit.db')
cursor = connection.cursor()

cursor.execute(''' 
CREATE TABLE IF NOT EXISTS accounts (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
password TEXT NOT NULL,
admin INTEGER NOT NULL DEFAULT 0
)
''')
connection.commit()
connection.close()

print('Accounts table created succesfully.')