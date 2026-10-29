import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch


os.environ["JOBGUARD_DATABASE_PATH"] = os.path.join(
    tempfile.gettempdir(), "jobguard-test-import.db"
)

import app
from analyzer import predict_job


class JobGuardAppTests(unittest.TestCase):
    def setUp(self):
        handle, self.database_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        app.DATABASE = self.database_path
        app.DATABASE_DIR = os.path.dirname(self.database_path)
        app.init_database()
        app.app.config.update(TESTING=True)
        self.client = app.app.test_client()

    def tearDown(self):
        if os.path.exists(self.database_path):
            os.unlink(self.database_path)

    def test_homepage_get(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_empty_submission(self):
        response = self.client.post("/", data={"job_description": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter a job description.", response.data)

    @patch(
        "app.predict_job",
        return_value={
            "prediction": "FAKE",
            "confidence": 92.5,
            "risk_score": 80,
            "risk_level": "HIGH RISK",
            "red_flags": [("Payment Request", "registration fee")],
        },
    )
    def test_valid_submission_is_saved(self, _predict):
        response = self.client.post(
            "/",
            data={"job_description": "Pay a registration fee to start."},
        )
        self.assertEqual(response.status_code, 200)
        with closing(sqlite3.connect(app.DATABASE)) as connection:
            row = connection.execute(
                "SELECT prediction, confidence, risk_score FROM scans"
            ).fetchone()
        self.assertEqual(row, ("FAKE", 92.5, 80))

    @patch("app.predict_job", side_effect=RuntimeError("model failure"))
    def test_prediction_error_is_user_safe(self, _predict):
        response = self.client.post(
            "/", data={"job_description": "A valid description"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unable to analyze this job description.", response.data)

    def test_history_filters_and_empty_state(self):
        app.save_scan("real role", "REAL", 75, 10, "LOW RISK")
        app.save_scan("fee role", "FAKE", 90, 80, "HIGH RISK")

        response = self.client.get("/history?prediction=FAKE&risk=ALL")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"fee role", response.data)
        self.assertNotIn(b"real role", response.data)

        handle, empty_database_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        os.unlink(empty_database_path)
        app.DATABASE = empty_database_path
        app.DATABASE_DIR = os.path.dirname(app.DATABASE)
        app.init_database()
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No scans found", response.data)

    def test_dashboard_and_scan_details(self):
        app.save_scan("real role", "REAL", 75, 10, "LOW RISK")
        dashboard = self.client.get("/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(b"Total Scans", dashboard.data)

        details = self.client.get("/scan/1")
        self.assertEqual(details.status_code, 200)
        self.assertIn(b"real role", details.data)
        self.assertEqual(self.client.get("/scan/999").status_code, 404)

    def test_real_prediction_schema(self):
        result = predict_job("Pay Rs 999 registration fee through WhatsApp.")
        self.assertIn(result["prediction"], {"REAL", "FAKE"})
        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 100)
        self.assertIsInstance(result["red_flags"], list)
        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)


if __name__ == "__main__":
    unittest.main()
