
import sqlite3

conn = sqlite3.connect('backend/requests.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY
        CHECK(id IN ('request-001', 'request-002', 'request-003', 'request-004', 'request-005')),

    amount INTEGER NOT NULL
        CHECK(amount >= 0),
    items TEXT NOT NULL CHECK(items IN ('Drinking water', 'Food Pack', 'First Aid Kit', 'Medical Supplies', )),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'approved', 'rejected'))
    need TEXT NOT NULL CHECK(need IN ('urgent', 'normal', 'low'))
    )
    ''')
    conn.commit()
    conn.close()

    print("Table 'requests' created successfully.")

