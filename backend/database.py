
import os
import sqlite3
from contextlib import closing
from pathlib import Path


DATABASE_DIR = Path(os.environ.get("DATABASE_DIR", Path(__file__).resolve().parent)).resolve()


def get_db_connection(database_name="accounts.db"):
    connection = sqlite3.connect(DATABASE_DIR / database_name)
    connection.row_factory = sqlite3.Row
    return connection


def init_databases():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    with closing(get_db_connection()) as connection:
        columns = connection.execute("PRAGMA table_info(accounts)").fetchall()
        if columns and "admin" in {column["name"] for column in columns}:
            connection.execute("BEGIN")
            connection.execute("ALTER TABLE accounts RENAME TO accounts_with_roles")
            connection.execute(
                """CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL
                )"""
            )
            connection.execute(
                """INSERT INTO accounts (id, name, password)
                   SELECT id, name, password FROM accounts_with_roles"""
            )
            connection.execute("DROP TABLE accounts_with_roles")
        else:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL
                )"""
            )
        connection.commit()

    with closing(get_db_connection("places.db")) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS places (
                place_id INTEGER PRIMARY KEY AUTOINCREMENT,
                value_per_item REAL NOT NULL
            )"""
        )
        connection.commit()

    with closing(get_db_connection("warehouse.db")) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS warehouse_inventory (
                warehouse_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0
            )"""
        )
        connection.commit()

    with closing(get_db_connection("requests.db")) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'fulfilled', 'rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_requests_account_id ON requests(account_id)"
        )
        connection.commit()


if __name__ == "__main__":
    init_databases()
    print("Database schemas are ready.")
