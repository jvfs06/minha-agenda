"""PostgreSQL integration smoke test; requires DATABASE_URL and disposable database."""
import os
import uuid
import unittest

class PostgresIntegration(unittest.TestCase):
    def test_register_sync_and_conflict(self):
        if not os.environ.get("DATABASE_URL"):
            self.skipTest("DATABASE_URL not configured")
        import app
        app.init_db()
        client = app.app.test_client()
        headers={"Origin":app.ORIGINS[0]}
        email=f"ci-{uuid.uuid4().hex}@example.com"
        r=client.post("/api/auth/register",json={"email":email,"password":"integration-test-password"},headers=headers)
        self.assertEqual(r.status_code,201,r.get_data(as_text=True))
        item_id="test-"+uuid.uuid4().hex
        url="/api/sync/records/"+item_id
        payload={"base_revision":0,"data":{"id":item_id,"type":"study"}}
        r=client.put(url,json=payload,headers=headers)
        self.assertEqual(r.status_code,200,r.get_data(as_text=True))
        self.assertEqual(client.put(url,json=payload,headers=headers).status_code,409)
        self.assertEqual(client.get("/api/sync/records").status_code,200)
        self.assertEqual(client.post("/api/auth/logout",json={},headers=headers).status_code,200)

if __name__=="__main__":
    unittest.main()
