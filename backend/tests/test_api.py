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

    def test_rate_limit_and_revision_type(self):
        self.client.post("/api/auth/register", json={"email":"rate@example.com","password":"long-test-password"}, headers=self.headers)
        url = "/api/sync/records/entry-1"
        self.assertEqual(self.client.put(url, json={"base_revision":True,"data":{"id":"entry-1"}}, headers=self.headers).status_code, 400)
        results = [self.client.post("/api/auth/login", json={"email":"absent@example.com","password":"long-test-password"}, headers=self.headers).status_code for _ in range(self.api.RATE_LIMIT)]
        self.assertIn(429, results)
        self.assertEqual(self.client.post("/api/auth/login", json={"email":"absent@example.com","password":"long-test-password"}, headers=self.headers).status_code, 429)

    def test_duplicate_email_and_sync_settings(self):
        body={"email":"duplicate@example.com","password":"long-test-password"}
        self.assertEqual(self.client.post("/api/auth/register", json=body, headers=self.headers).status_code, 201)
        self.assertEqual(self.client.post("/api/auth/register", json=body, headers=self.headers).status_code, 409)
        url="/api/sync/settings/goals"
        self.assertEqual(self.client.put(url,json={"base_revision":0,"data":{"key":"goals","value":{"workouts":5}}},headers=self.headers).json["revision"],1)
        self.assertEqual(self.client.put(url,json={"base_revision":1,"data":{"key":"goals","value":{"workouts":4}}},headers=self.headers).json["revision"],2)
        self.assertEqual(self.client.get("/api/sync/settings").json["items"][0]["data"]["value"]["workouts"],4)

    def test_bearer_token_without_cookies(self):
        creator=self.api.app.test_client()
        r=creator.post("/api/auth/register",json={"email":"bearer@example.com","password":"long-test-password"},headers=self.headers)
        self.assertEqual(r.status_code,201)
        token=r.json["access_token"]
        self.assertTrue(token)
        other=self.api.app.test_client()
        self.assertEqual(other.get("/api/auth/me").status_code,401)
        bearer={"Authorization":"Bearer "+token}
        self.assertEqual(other.get("/api/auth/me",headers=bearer).status_code,200)
        h={**self.headers,**bearer}
        self.assertEqual(other.put("/api/sync/records/bearer-1",json={"base_revision":0,"data":{"id":"bearer-1"}},headers=h).status_code,200)
        self.assertEqual(other.post("/api/auth/logout",json={},headers=h).status_code,200)
        self.assertEqual(other.get("/api/auth/me",headers=bearer).status_code,401)

    def test_password_recovery_revokes_sessions_and_tokens(self):
        from unittest.mock import patch
        body={"email":"reset@example.com","password":"original-long-password"}
        self.assertEqual(self.client.post("/api/auth/register",json=body,headers=self.headers).status_code,201)
        token_holder=[]
        with patch.object(self.api,"send_reset_email",side_effect=lambda email,token:token_holder.append(token)):
            r=self.client.post("/api/auth/forgot-password",json={"email":body["email"]},headers=self.headers)
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(token_holder),1)
        r=self.client.post("/api/auth/reset-password",json={"token":token_holder[0],"password":"replacement-long-password"},headers=self.headers)
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.client.get("/api/auth/me").status_code,401)
        self.assertEqual(self.client.post("/api/auth/reset-password",json={"token":token_holder[0],"password":"replacement-long-password"},headers=self.headers).status_code,400)
        self.assertEqual(self.client.post("/api/auth/login",json={"email":body["email"],"password":"replacement-long-password"},headers=self.headers).status_code,200)

if __name__ == "__main__":
    unittest.main()
