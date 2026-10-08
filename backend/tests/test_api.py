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

    def test_password_hash_and_invalid_credentials(self):
        password = "another-long-password"
        hashed = self.api.hash_password(password)
        self.assertNotIn(password, hashed)
        self.assertTrue(self.api.verify_password(password, hashed))
        self.assertFalse(self.api.verify_password("wrong-password", hashed))
        headers = self.headers
        self.assertEqual(self.client.post("/api/auth/register", json={"email":"bad","password":"short"}, headers=headers).status_code, 400)
        self.assertEqual(self.client.post("/api/auth/login", json={"email":"nobody@example.com","password":password}, headers=headers).status_code, 401)

    def test_users_cannot_read_or_write_each_others_items(self):
        first = self.api.app.test_client()
        second = self.api.app.test_client()
        self.assertEqual(first.post("/api/auth/register", json={"email":"first@example.com","password":"first-long-password"}, headers=self.headers).status_code, 201)
        self.assertEqual(second.post("/api/auth/register", json={"email":"second@example.com","password":"second-long-password"}, headers=self.headers).status_code, 201)
        url = "/api/sync/records/private-1"
        data = {"base_revision":0,"data":{"id":"private-1","type":"study","notes":"private"}}
        self.assertEqual(first.put(url, json=data, headers=self.headers).status_code, 200)
        self.assertEqual(second.get("/api/sync/records").json["items"], [])
        self.assertEqual(second.put(url, json={"base_revision":0,"data":{"id":"private-1","type":"study","notes":"other"}}, headers=self.headers).status_code, 200)
        self.assertEqual(first.get("/api/sync/records").json["items"][0]["data"]["notes"], "private")

    def test_mutations_require_json_and_valid_origin(self):
        r = self.client.post("/api/auth/register", data="email=a", headers=self.headers)
        self.assertEqual(r.status_code, 415)
        r = self.client.post("/api/auth/register", json={"email":"a@b.com","password":"long-test-password"})
        self.assertEqual(r.status_code, 403)

    def test_invalid_sync_payloads_and_missing_session(self):
        url = "/api/sync/records/entry-1"
        self.assertEqual(self.client.put(url, json={"base_revision":0,"data":{"id":"entry-1"}}, headers=self.headers).status_code, 401)
        self.client.post("/api/auth/register", json={"email":"valid@example.com","password":"long-test-password"}, headers=self.headers)
        self.assertEqual(self.client.put(url, json={"base_revision":0,"data":{"id":"wrong"}}, headers=self.headers).status_code, 400)
        self.assertEqual(self.client.put(url, json={"base_revision":-1,"data":{"id":"entry-1"}}, headers=self.headers).status_code, 400)
        self.assertEqual(self.client.get("/api/sync/not-real").status_code, 404)

if __name__ == "__main__":
    unittest.main()
