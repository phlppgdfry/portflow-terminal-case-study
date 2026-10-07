"""HTTP contract tests against a real server on a free port (see integrations/openapi.yaml)."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from portflow.config import Settings
from portflow.server import App, make_handler

from helpers import manifest_json, sample


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        cls.app = App(Settings(db_path=str(base / "api.db"), spool_dir=str(base / "spool"), pool_size=2))
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.app))
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.app.pool.close()
        cls.tmp.cleanup()

    def call(self, method, path, body=None, content_type="application/json"):
        data = body.encode() if isinstance(body, str) else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode()

    def test_health(self):
        status, body = self.call("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["database"], "UP")

    def test_manifest_lifecycle(self):
        status, body = self.call("POST", "/api/v1/vehicle-manifests", manifest_json(messageRef="API-1", shipmentId="API-S1"))
        self.assertEqual(status, 201, body)

        status, _ = self.call("POST", "/api/v1/gate-events", json.dumps({"vin": "KNAB2512AST123456"}))
        self.assertEqual(status, 201)

        _, body = self.call("GET", "/api/v1/shipments")
        shipment = next(s for s in json.loads(body) if s["shipment_ref"] == "API-S1")
        self.assertEqual((shipment["arrived"], shipment["vehicles"]), (1, 3))

    def test_at10_operations_can_see_why_a_message_was_rejected(self):
        status, body = self.call("POST", "/api/v1/edi-messages", sample("sample-edi-invalid.edi"), "text/plain")
        self.assertEqual(status, 422)
        message_id = json.loads(body)["messageId"]

        _, body = self.call("GET", "/api/v1/messages?status=REJECTED")
        self.assertIn(message_id, [m["message_id"] for m in json.loads(body)])

        _, body = self.call("GET", f"/api/v1/messages/{message_id}")
        detail = json.loads(body)
        self.assertEqual({e["error_code"] for e in detail["errors"]}, {"V-ARRIVAL-DATE", "V-VIN-FORMAT"})
        self.assertIn("UNB+UNOC:3+HRN", detail["raw_payload"])

    def test_syntax_error_is_http_400(self):
        status, _ = self.call("POST", "/api/v1/vehicle-manifests", "{not json")
        self.assertEqual(status, 400)

    def test_unknown_vin_at_gate_is_404(self):
        status, _ = self.call("POST", "/api/v1/gate-events", json.dumps({"vin": "WVWZZZE1ZPP099999"}))
        self.assertEqual(status, 404)

    def test_kpis_and_ops_page(self):
        status, body = self.call("GET", "/api/v1/reports/kpis")
        self.assertEqual(status, 200)
        self.assertIn("partners", json.loads(body))
        status, page = self.call("GET", "/ops")
        self.assertEqual(status, 200)
        self.assertIn("PortFlow", page)


if __name__ == "__main__":
    unittest.main()
