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
            "/requests", json={"item_name": "Water", "quantity": 4}
        )
        self.assertEqual(response.status_code, 201)
        request_id = response.json["request_id"]

        response = self.client.get(f"/requests/{request_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["account_id"], account_id)
        self.assertEqual(response.json["status"], "pending")

        response = self.client.put(
            f"/requests/{request_id}",
            json={"item_name": "Water", "quantity": 5, "status": "approved"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/requests").json[0]["quantity"], 5)

        self.assertEqual(self.client.delete(f"/requests/{request_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/requests/{request_id}").status_code, 404)

    def test_request_rejects_invalid_values(self):
        self.create_authenticated_account()

        self.assertEqual(
            self.client.post(
                "/requests", json={"item_name": "Water", "quantity": 0}
            ).status_code,
            400,
        )
        response = self.client.post(
            "/requests", json={"item_name": "Water", "quantity": 2}
        )
        request_id = response.json["request_id"]
        self.assertEqual(
            self.client.put(
                f"/requests/{request_id}",
                json={"item_name": "Water", "quantity": 2, "status": "unknown"},
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
            {"request_id", "account_id", "item_name", "quantity", "status", "created_at"},
        )

    def test_production_requires_explicit_secret(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "FLASK_SECRET_KEY"):
                self.app_module.get_secret_key()


if __name__ == "__main__":
    unittest.main()