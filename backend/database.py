
import os
import sqlite3
from contextlib import closing
from pathlib import Path


DATABASE_DIR = Path(os.environ.get("DATABASE_DIR", Path(__file__).resolve().parent)).resolve()
MAIN_DATABASE = "rit.db"
INVENTORY_ITEMS = ("Drinking Water", "Food Packs", "First Aid Kits", "Medical Supplies")
INVENTORY_STATUSES = ("In Stock", "Low Stock", "Out Of Stock")
INVENTORY_WAREHOUSES = tuple(f"WH-{number:03d}" for number in range(1, 6))


def get_db_connection(database_name=MAIN_DATABASE):
    connection = sqlite3.connect(DATABASE_DIR / database_name)
    connection.row_factory = sqlite3.Row
    return connection


def init_databases():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    with closing(get_db_connection()) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT NOT NULL
            )"""
        )
        connection.commit()

    legacy_accounts_path = DATABASE_DIR / "accounts.db"
    if legacy_accounts_path.exists() and legacy_accounts_path != DATABASE_DIR / MAIN_DATABASE:
        legacy_connection = sqlite3.connect(legacy_accounts_path)
        legacy_accounts = legacy_connection.execute(
            "SELECT name, password FROM accounts"
        ).fetchall()
        legacy_connection.close()
        with closing(get_db_connection()) as connection:
            for name, password in legacy_accounts:
                if not connection.execute(
                    "SELECT 1 FROM accounts WHERE name = ?", (name,)
                ).fetchone():
                    connection.execute(
                        "INSERT INTO accounts (name, password) VALUES (?, ?)",
                        (name, password),
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

    with closing(get_db_connection()) as connection:
        table = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'warehouse_inventory'"
        ).fetchone()
        has_item_constraint = table and (
            "item_name IN ('Drinking Water', 'Food Packs', 'First Aid Kits', 'Medical Supplies')"
            in table["sql"]
        )
        if table and not has_item_constraint:
            legacy_columns = {
                column["name"]
                for column in connection.execute("PRAGMA table_info(warehouse_inventory)")
            }
            status_expression = """CASE
                WHEN quantity = 0 THEN 'Out Of Stock'
                WHEN quantity < 50 THEN 'Low Stock'
                ELSE 'In Stock' END"""
            connection.execute(
                "ALTER TABLE warehouse_inventory RENAME TO warehouse_inventory_legacy"
            )

        connection.execute(
            """CREATE TABLE IF NOT EXISTS warehouse_inventory (
                warehouse_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL CHECK (
                    item_name IN ('Drinking Water', 'Food Packs', 'First Aid Kits', 'Medical Supplies')
                ),
                quantity INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'In Stock'
                    CHECK (status IN ('In Stock', 'Low Stock', 'Out Of Stock')),
                warehouse_code TEXT NOT NULL DEFAULT 'WH-001' CHECK (
                    warehouse_code IN ('WH-001', 'WH-002', 'WH-003', 'WH-004', 'WH-005')
                )
            )"""
        )
        if table and not has_item_constraint:
            connection.execute(
                f"""INSERT INTO warehouse_inventory
                    (warehouse_id, item_name, quantity, status, warehouse_code)
                    SELECT warehouse_id, item_name, quantity, {status_expression}, 'WH-001'
                    FROM warehouse_inventory_legacy
                    WHERE item_name IN ({', '.join('?' for _ in INVENTORY_ITEMS)})""",
                INVENTORY_ITEMS,
            )

        columns = {
            column["name"]
            for column in connection.execute("PRAGMA table_info(warehouse_inventory)")
        }
        if "warehouse_code" not in columns:
            connection.execute(
                """ALTER TABLE warehouse_inventory ADD COLUMN warehouse_code TEXT NOT NULL
                   DEFAULT 'WH-001'
                   CHECK (warehouse_code IN ('WH-001', 'WH-002', 'WH-003', 'WH-004', 'WH-005'))"""
            )

        index_names = {
            index["name"] for index in connection.execute("PRAGMA index_list(warehouse_inventory)")
        }
        if "idx_warehouse_inventory_item_location" not in index_names:
            connection.executescript(
                """DROP TRIGGER IF EXISTS inventory_status_after_insert;
                   DROP TRIGGER IF EXISTS inventory_status_after_quantity_update;
                   DROP TRIGGER IF EXISTS inventory_status_after_status_update;

                   CREATE TEMP TABLE warehouse_inventory_rollup AS
                   SELECT MIN(warehouse_id) AS warehouse_id,
                          item_name,
                          SUM(quantity) AS quantity,
                          CASE
                              WHEN SUM(quantity) = 0 THEN 'Out Of Stock'
                              WHEN SUM(quantity) < 50 THEN 'Low Stock'
                              ELSE 'In Stock' END AS status,
                          warehouse_code
                   FROM warehouse_inventory
                   GROUP BY item_name, warehouse_code;

                   DELETE FROM warehouse_inventory;

                   INSERT INTO warehouse_inventory
                       (warehouse_id, item_name, quantity, status, warehouse_code)
                   SELECT warehouse_id, item_name, quantity, status, warehouse_code
                   FROM warehouse_inventory_rollup;

                   DROP TABLE warehouse_inventory_rollup;
                   """
            )
            connection.execute(
                """CREATE UNIQUE INDEX idx_warehouse_inventory_item_location
                   ON warehouse_inventory (item_name, warehouse_code)"""
            )
        connection.commit()

    legacy_warehouse_path = DATABASE_DIR / "warehouse.db"
    if legacy_warehouse_path.exists() and legacy_warehouse_path != DATABASE_DIR / MAIN_DATABASE:
        legacy_connection = sqlite3.connect(legacy_warehouse_path)
        legacy_columns = {
            column[1]
            for column in legacy_connection.execute("PRAGMA table_info(warehouse_inventory)")
        }
        if legacy_columns:
            status_expression = """CASE
                WHEN quantity = 0 THEN 'Out Of Stock'
                WHEN quantity < 50 THEN 'Low Stock'
                ELSE 'In Stock' END"""
            legacy_items = legacy_connection.execute(
                f"SELECT item_name, quantity, {status_expression} FROM warehouse_inventory"
            ).fetchall()
        else:
            legacy_items = []
        legacy_connection.close()
        with closing(get_db_connection()) as connection:
            if not connection.execute("SELECT 1 FROM warehouse_inventory LIMIT 1").fetchone():
                for item_name, quantity, status in legacy_items:
                    if item_name not in INVENTORY_ITEMS or type(quantity) is not int or quantity < 0:
                        continue
                    if status == "Out of Stock":
                        status = "Out Of Stock"
                    if status not in INVENTORY_STATUSES:
                        status = "Out Of Stock" if quantity == 0 else "In Stock"
                    connection.execute(
                        """INSERT INTO warehouse_inventory (item_name, quantity, status)
                           VALUES (?, ?, ?)""",
                        (item_name, quantity, status),
                    )
            connection.commit()

    with closing(get_db_connection()) as connection:
        connection.executescript(
            """CREATE TRIGGER IF NOT EXISTS inventory_status_after_insert
               AFTER INSERT ON warehouse_inventory
               BEGIN
                   UPDATE warehouse_inventory
                   SET status = CASE
                       WHEN NEW.quantity = 0 THEN 'Out Of Stock'
                       WHEN NEW.quantity < 50 THEN 'Low Stock'
                       ELSE 'In Stock' END
                   WHERE warehouse_id = NEW.warehouse_id;
               END;

               CREATE TRIGGER IF NOT EXISTS inventory_status_after_quantity_update
               AFTER UPDATE OF quantity ON warehouse_inventory
               BEGIN
                   UPDATE warehouse_inventory
                   SET status = CASE
                       WHEN NEW.quantity = 0 THEN 'Out Of Stock'
                       WHEN NEW.quantity < 50 THEN 'Low Stock'
                       ELSE 'In Stock' END
                   WHERE warehouse_id = NEW.warehouse_id;
               END;

               CREATE TRIGGER IF NOT EXISTS inventory_status_after_status_update
               AFTER UPDATE OF status ON warehouse_inventory
               WHEN NEW.status != CASE
                   WHEN NEW.quantity = 0 THEN 'Out Of Stock'
                   WHEN NEW.quantity < 50 THEN 'Low Stock'
                   ELSE 'In Stock' END
               BEGIN
                   UPDATE warehouse_inventory
                   SET status = CASE
                       WHEN NEW.quantity = 0 THEN 'Out Of Stock'
                       WHEN NEW.quantity < 50 THEN 'Low Stock'
                       ELSE 'In Stock' END
                   WHERE warehouse_id = NEW.warehouse_id;
               END;

               UPDATE warehouse_inventory
               SET status = CASE
                   WHEN quantity = 0 THEN 'Out Of Stock'
                   WHEN quantity < 50 THEN 'Low Stock'
                   ELSE 'In Stock' END;
               """
        )

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


import sqlite3('requests.db')
def create_requests_database():
    conn = sqlite3.connect
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY
       CHECK(id IN ('req-001', 'req-002', 'req-003', 'req-004', 'req-005')),
    item TEXT NOT NULL
       CHECK(item IN ('Drinking water', 'Food pack', 'First aid kits', 'Medical supplies'
       )),
    amount INTEGER NOT NULL CHECK(amount > 0),
    status TEXT NOT NULL DEFAULT 'Pending'
       CHECK(status IN ('Done', 'Pending')),
    need TEXT NOT NULL 
       CHECK(need IN ('Critical', 'Meduim', 'Low'))

    )
    """)

    conn.commit()
    conn.close()

create_requests_database()


       
       
       
       
       