import os
import tempfile
import unittest

class APITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.environ["AGENDA_DATABASE"] = os.path.join(self.temp.name, "test.sqlite3")
        os.environ["AGENDA_ALLOWED_ORIGINS"] = "http://localhost:8000"
        os.environ["AGENDA_SECURE_COOKIES"] = "0"
        import importlib
        import app
        self.api = importlib.reload(app)
        self.api.init_db()
        self.client = self.api.app.test_client()
        self.headers = {"Origin": "http://localhost:8000"}

    def tearDown(self):
        self.temp.cleanup()

    def test_auth_and_sync_conflict(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        body = {"email": "user@example.com", "password": "long-test-password"}
        r = self.client.post("/api/auth/register", json=body, headers=self.headers)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        payload = {"base_revision": 0, "data": {"id": "workout-1", "type": "workout"}}
        url = "/api/sync/records/workout-1"
        r = self.client.put(url, json=payload, headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["revision"], 1)
        self.assertEqual(self.client.put(url, json=payload, headers=self.headers).status_code, 409)
        self.assertEqual(len(self.client.get("/api/sync/records").json["items"]), 1)
        self.assertEqual(self.client.post("/api/auth/logout", json={}, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_origin_restriction(self):
        r = self.client.post("/api/auth/register", json={"email":"a@b.com","password":"long-test-password"}, headers={"Origin":"https://evil.example"})
        self.assertEqual(r.status_code, 403)

if __name__ == "__main__":
    unittest.main()
