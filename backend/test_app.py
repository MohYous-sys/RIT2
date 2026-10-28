import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import database


class BackendApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        database.DATABASE_DIR = Path(cls.temp_dir.name)
        cls.environment = patch.dict(
            os.environ,
            {"APP_ENV": "test", "FLASK_SECRET_KEY": "unit-test-secret"},
        )
        cls.environment.start()
        cls.app_module = importlib.import_module("app")
        cls.app = cls.app_module.app
        cls.app.config["TESTING"] = True

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()
        cls.temp_dir.cleanup()

    def setUp(self):
        connection = database.get_db_connection()
        connection.execute("DELETE FROM accounts")
        connection.commit()
        connection.close()

        connection = database.get_db_connection("requests.db")
        connection.execute("DELETE FROM requests")
        connection.commit()
        connection.close()

        connection = database.get_db_connection()
        connection.execute("DELETE FROM warehouse_inventory")
        connection.commit()
        connection.close()
        self.client = self.app.test_client()

    def create_authenticated_account(self):
        response = self.client.post(
            "/accounts", json={"name": "requester", "password": "test-password"}
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.post(
            "/login", json={"name": "requester", "password": "test-password"}
        )
        self.assertEqual(response.status_code, 200)
        return response.json["account_id"]

    def test_requests_require_login_and_support_crud(self):
        self.assertEqual(self.client.get("/requests").status_code, 401)
        account_id = self.create_authenticated_account()

        response = self.client.post(
            "/requests",
            json={
                "item_name": "Drinking Water",
                "shelter": "Downtown Emergency Shelter",
                "quantity": 4,
                "urgency": "Critical",
            },
        )
        self.assertEqual(response.status_code, 201)
        request_id = response.json["request_id"]

        response = self.client.get(f"/requests/{request_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["account_id"], account_id)
        self.assertEqual(response.json["status"], "pending")
        self.assertEqual(response.json["shelter"], "Downtown Emergency Shelter")
        self.assertEqual(response.json["urgency"], "Critical")

        response = self.client.put(
            f"/requests/{request_id}",
            json={
                "item_name": "Drinking Water",
                "shelter": "Creek Relief Center",
                "quantity": 5,
                "urgency": "High",
                "status": "pending",
            },
        )
        self.assertEqual(response.status_code, 200)
        updated_request = self.client.get("/requests").json[0]
        self.assertEqual(updated_request["quantity"], 5)
        self.assertEqual(updated_request["shelter"], "Creek Relief Center")
        self.assertEqual(updated_request["urgency"], "High")

        self.assertEqual(self.client.delete(f"/requests/{request_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/requests/{request_id}").status_code, 404)

    def test_approval_deducts_available_inventory_and_keeps_remainder_pending(self):
        self.create_authenticated_account()
        for warehouse_code, quantity in (("WH-001", 2), ("WH-002", 3)):
            response = self.client.post(
                "/warehouse",
                json={
                    "item_name": "Drinking Water",
                    "quantity": quantity,
                    "warehouse_code": warehouse_code,
                },
            )
            self.assertEqual(response.status_code, 201)

        response = self.client.post(
            "/requests",
            json={
                "item_name": "Drinking Water",
                "shelter": "Downtown Emergency Shelter",
                "quantity": 8,
            },
        )
        request_id = response.json["request_id"]

        response = self.client.put(
            f"/requests/{request_id}",
            json={"item_name": "Drinking Water", "quantity": 8, "status": "approved"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["fulfilled_quantity"], 5)
        self.assertEqual(response.json["quantity"], 3)
        self.assertEqual(response.json["status"], "pending")
        self.assertEqual(
            sum(item["quantity"] for item in self.client.get("/warehouse").json),
            0,
        )

        response = self.client.put(
            f"/requests/{request_id}",
            json={"item_name": "Drinking Water", "quantity": 3, "status": "approved"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["fulfilled_quantity"], 0)
        self.assertEqual(response.json["quantity"], 3)
        self.assertEqual(response.json["status"], "pending")

        self.client.post(
            "/warehouse",
            json={
                "item_name": "Drinking Water",
                "quantity": 3,
                "warehouse_code": "WH-003",
            },
        )
        response = self.client.put(
            f"/requests/{request_id}",
            json={"item_name": "Drinking Water", "quantity": 3, "status": "approved"},
        )
        self.assertEqual(response.json["fulfilled_quantity"], 3)
        self.assertEqual(response.json["quantity"], 0)
        self.assertEqual(response.json["status"], "approved")
        self.assertEqual(
            sum(item["quantity"] for item in self.client.get("/warehouse").json),
            0,
        )

    def test_request_rejects_invalid_values(self):
        self.create_authenticated_account()

        self.assertEqual(
            self.client.post(
                "/requests",
                json={
                    "item_name": "Drinking Water",
                    "shelter": "Downtown Emergency Shelter",
                    "quantity": 0,
                },
            ).status_code,
            400,
        )
        response = self.client.post(
            "/requests",
            json={
                "item_name": "Drinking Water",
                "shelter": "Downtown Emergency Shelter",
                "quantity": 2,
            },
        )
        request_id = response.json["request_id"]
        self.assertEqual(
            self.client.put(
                f"/requests/{request_id}",
                json={"item_name": "Drinking Water", "quantity": 2, "status": "unknown"},
            ).status_code,
            400,
        )
        for status in ("fulfilled", "rejected"):
            with self.subTest(status=status):
                self.assertEqual(
                    self.client.put(
                        f"/requests/{request_id}",
                        json={
                            "item_name": "Drinking Water",
                            "quantity": 2,
                            "status": status,
                        },
                    ).status_code,
                    400,
                )
        self.assertEqual(
            self.client.post(
                "/requests",
                json={
                    "item_name": "Drinking Water",
                    "shelter": "Downtown Emergency Shelter",
                    "quantity": 2,
                    "urgency": "Immediate",
                },
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/requests",
                json={
                    "item_name": "Blankets",
                    "shelter": "Downtown Emergency Shelter",
                    "quantity": 2,
                },
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/requests",
                json={
                    "item_name": "Drinking Water",
                    "shelter": "Unknown Shelter",
                    "quantity": 2,
                },
            ).status_code,
            400,
        )

    def test_request_schema_is_created_on_startup(self):
        connection = database.get_db_connection("requests.db")
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(requests)")
        }
        connection.close()
        self.assertEqual(
            columns,
            {
                "request_id",
                "account_id",
                "item_name",
                "shelter",
                "quantity",
                "urgency",
                "status",
                "created_at",
            },
        )
        connection = database.get_db_connection("requests.db")
        with self.assertRaises(Exception):
            connection.execute(
                "INSERT INTO requests (account_id, item_name, quantity, status) VALUES (1, 'Water', 1, 'fulfilled')"
            )
        connection.close()

    def test_request_schema_migrates_existing_rows(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            database, "DATABASE_DIR", Path(directory)
        ):
            connection = database.get_db_connection("requests.db")
            connection.execute(
                """CREATE TABLE requests (
                    request_id INTEGER PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'approved', 'fulfilled', 'rejected')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            connection.executemany(
                "INSERT INTO requests (request_id, account_id, item_name, quantity, status) VALUES (?, 3, 'Water', 2, ?)",
                [(1, "pending"), (2, "approved"), (3, "fulfilled"), (4, "rejected")],
            )
            connection.commit()
            connection.close()

            database.init_databases()
            connection = database.get_db_connection("requests.db")
            migrated = connection.execute(
                "SELECT request_id, shelter, urgency, status, quantity FROM requests ORDER BY request_id"
            ).fetchall()
            connection.close()

            self.assertEqual(
                [tuple(row) for row in migrated],
                [
                    (1, "", "Moderate", "pending", 2),
                    (2, "", "Moderate", "pending", 2),
                    (3, "", "Moderate", "approved", 0),
                    (4, "", "Moderate", "pending", 2),
                ],
            )

    def test_warehouse_only_accepts_supported_items_and_statuses(self):
        self.create_authenticated_account()

        response = self.client.post(
            "/warehouse",
            json={
                "item_name": "Drinking Water",
                "quantity": 49,
                "status": "In Stock",
                "warehouse_code": "WH-001",
            },
        )
        self.assertEqual(response.status_code, 201)

        item = self.client.get("/warehouse").json[0]
        self.assertEqual(item["item_name"], "Drinking Water")
        self.assertEqual(item["status"], "Low Stock")
        self.assertEqual(item["warehouse_code"], "WH-001")

        item_id = item["warehouse_id"]
        merged = self.client.post(
            "/warehouse",
            json={"item_name": "Drinking Water", "quantity": 1, "warehouse_code": "WH-001"},
        )
        self.assertEqual(merged.status_code, 201)
        self.assertEqual(merged.json["warehouse_id"], item_id)
        self.assertEqual(merged.json["quantity"], 50)
        self.assertEqual(merged.json["status"], "In Stock")

        separate_warehouse = self.client.post(
            "/warehouse",
            json={"item_name": "Drinking Water", "quantity": 5, "warehouse_code": "WH-002"},
        )
        self.assertEqual(separate_warehouse.status_code, 201)
        self.assertNotEqual(separate_warehouse.json["warehouse_id"], item_id)

        for quantity, expected_status, submitted_status in (
            (0, "Out Of Stock", "In Stock"),
            (49, "Low Stock", "Out Of Stock"),
            (50, "In Stock", "Low Stock"),
            (51, "In Stock", "Out Of Stock"),
        ):
            with self.subTest(quantity=quantity):
                response = self.client.put(
                    f"/warehouse/{item_id}",
                    json={
                        "item_name": "Drinking Water",
                        "quantity": quantity,
                        "status": submitted_status,
                        "warehouse_code": "WH-001",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["status"], expected_status)
                self.assertEqual(self.client.get("/warehouse").json[0]["status"], expected_status)

        invalid_warehouse = self.client.post(
            "/warehouse",
            json={"item_name": "Food Packs", "quantity": 1, "warehouse_code": "WH-006"},
        )
        self.assertEqual(invalid_warehouse.status_code, 400)

        for item_name in ("Blankets", "Laptop", "drinking water"):
            with self.subTest(item_name=item_name):
                self.assertEqual(
                    self.client.post(
                        "/warehouse",
                        json={"item_name": item_name, "quantity": 1},
                    ).status_code,
                    400,
                )

    def test_warehouse_schema_constrains_status(self):
        connection = database.get_db_connection()
        columns = {
            row["name"]: row for row in connection.execute("PRAGMA table_info(warehouse_inventory)")
        }
        self.assertIn("status", columns)
        with self.assertRaises(Exception):
            connection.execute(
                "INSERT INTO warehouse_inventory (item_name, quantity, status) VALUES (?, ?, ?)",
                ("Drinking Water", 1, "pending"),
            )
        connection.execute(
            "INSERT INTO warehouse_inventory (item_name, quantity, status) VALUES (?, ?, ?)",
            ("Drinking Water", 49, "In Stock"),
        )
        item_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.assertEqual(
            connection.execute(
                "SELECT status FROM warehouse_inventory WHERE warehouse_id = ?", (item_id,)
            ).fetchone()[0],
            "Low Stock",
        )
        connection.execute(
            "UPDATE warehouse_inventory SET quantity = 50, status = 'Low Stock' WHERE warehouse_id = ?",
            (item_id,),
        )
        self.assertEqual(
            connection.execute(
                "SELECT status FROM warehouse_inventory WHERE warehouse_id = ?", (item_id,)
            ).fetchone()[0],
            "In Stock",
        )
        connection.close()

    def test_split_databases_migrate_into_rit_db_once(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            database, "DATABASE_DIR", Path(directory)
        ):
            account_connection = database.get_db_connection("accounts.db")
            account_connection.execute(
                "CREATE TABLE accounts (id INTEGER PRIMARY KEY, name TEXT, password TEXT)"
            )
            account_connection.execute(
                "INSERT INTO accounts VALUES (1, 'Rand', 'existing-hash')"
            )
            account_connection.commit()
            account_connection.close()

            warehouse_connection = database.get_db_connection("warehouse.db")
            warehouse_connection.execute(
                """CREATE TABLE warehouse_inventory (
                    warehouse_id INTEGER PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0
                )"""
            )
            warehouse_connection.executemany(
                "INSERT INTO warehouse_inventory VALUES (?, ?, ?)",
                [
                    (1, "Drinking Water", 49),
                    (2, "Food Packs", 50),
                    (3, "First Aid Kits", 51),
                    (4, "Medical Supplies", 0),
                    (5, "Laptop", 4),
                ],
            )
            warehouse_connection.commit()
            warehouse_connection.close()

            database.init_databases()
            database.init_databases()
            connection = database.get_db_connection()
            accounts = connection.execute("SELECT name, password FROM accounts").fetchall()
            items = connection.execute(
                "SELECT item_name, quantity, status, warehouse_code FROM warehouse_inventory ORDER BY warehouse_id"
            ).fetchall()
            connection.close()

            self.assertEqual([tuple(account) for account in accounts], [("Rand", "existing-hash")])
            self.assertEqual(
                [tuple(item) for item in items],
                [
                    ("Drinking Water", 49, "Low Stock", "WH-001"),
                    ("Food Packs", 50, "In Stock", "WH-001"),
                    ("First Aid Kits", 51, "In Stock", "WH-001"),
                    ("Medical Supplies", 0, "Out Of Stock", "WH-001"),
                ],
            )

    def test_warehouse_migration_archives_unsupported_items(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            database, "DATABASE_DIR", Path(directory)
        ):
            connection = database.get_db_connection()
            connection.execute(
                """CREATE TABLE warehouse_inventory (
                    warehouse_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0
                )"""
            )
            connection.executemany(
                "INSERT INTO warehouse_inventory (item_name, quantity) VALUES (?, ?)",
                [("Drinking Water", 8), ("Laptop", 3), ("Medical Supplies", 0)],
            )
            connection.commit()
            connection.close()

            database.init_databases()
            connection = database.get_db_connection()
            active_items = connection.execute(
                "SELECT item_name, quantity, status, warehouse_code FROM warehouse_inventory ORDER BY warehouse_id"
            ).fetchall()
            archived_items = connection.execute(
                "SELECT item_name FROM warehouse_inventory_legacy ORDER BY warehouse_id"
            ).fetchall()
            connection.close()
            self.assertEqual(
                [tuple(item) for item in active_items],
                [
                    ("Drinking Water", 8, "Low Stock", "WH-001"),
                    ("Medical Supplies", 0, "Out Of Stock", "WH-001"),
                ],
            )
            self.assertEqual([item["item_name"] for item in archived_items], ["Drinking Water", "Laptop", "Medical Supplies"])

    def test_production_requires_explicit_secret(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "FLASK_SECRET_KEY"):
                self.app_module.get_secret_key()


if __name__ == "__main__":
    unittest.main()