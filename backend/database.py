
import sqlite3 
connection = sqlite3.connect('accounts.db')
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

cursor.execute("SELECT id, name, admin FROM accounts")
accounts = cursor.fetchall()
for account in accounts:
    print("Name: {}, Admin: {}".format(account[1], account[2]))
    if account[2] == 1:
        print("Role: Admin")
    else:
        print("Role: Regular User")
    print("--------------------")

connection.close()

print('Accounts table created succesfully.')
