"""Service-level tests. AT-xx refers to testing/acceptance-tests.md."""

import sqlite3
import unittest
from contextlib import ExitStack

from helpers import Env, manifest_json, sample


class ManifestServiceTest(unittest.TestCase):
    def setUp(self):
        self.env = Env()
        self.service = self.env.service

    def tearDown(self):
        self.env.close()

    def query(self, sql, *params):
        with sqlite3.connect(self.env.settings.db_path) as conn:
            return conn.execute(sql, params).fetchall()

    def error_codes(self, outcome):
        return [e.code for e in outcome.errors]

    def test_at01_valid_rest_manifest_is_accepted(self):
        outcome = self.service.submit(manifest_json(), "REST")
        self.assertEqual(outcome.status, "ACCEPTED")
        self.assertEqual(self.query("SELECT COUNT(*) FROM vehicle")[0][0], 3)
        self.assertEqual(self.query("SELECT expected_arrival FROM shipment")[0][0], "2026-10-08T09:30")

    def test_at02_valid_edi_manifest_is_accepted(self):
        outcome = self.service.submit(sample("sample-edi-message.edi"), "EDI")
        self.assertEqual(outcome.status, "ACCEPTED")
        self.assertEqual(self.query("SELECT COUNT(*) FROM vehicle WHERE status = 'EXPECTED'")[0][0], 4)

    def test_at03_invalid_vehicle_data_is_rejected_and_explained(self):
        payload = manifest_json(vehicles=[{"vin": "WVWZZZE1ZPP0123O5"}, {"model": "EX30"}])
        outcome = self.service.submit(payload, "REST")
        self.assertEqual(outcome.status, "REJECTED")
        self.assertEqual(self.error_codes(outcome), ["V-VIN-FORMAT", "V-REQUIRED"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM shipment")[0][0], 0)
        stored = self.query("SELECT error_code FROM message_error WHERE message_id = ?", outcome.message_id)
        self.assertEqual([r[0] for r in stored], ["V-VIN-FORMAT", "V-REQUIRED"])

    def test_at04_unknown_partner_is_rejected(self):
        outcome = self.service.submit(manifest_json(partnerId="XYZ"), "REST")
        self.assertEqual(self.error_codes(outcome), ["V-PARTNER-UNKNOWN"])

    def test_at05_duplicate_message_is_ignored(self):
        first = self.service.submit(manifest_json(), "REST")
        second = self.service.submit(manifest_json(), "REST")
        self.assertEqual(second.status, "DUPLICATE")
        self.assertEqual(second.message_id, first.message_id)
        self.assertEqual(self.query("SELECT COUNT(*) FROM edi_message")[0][0], 1)

    def test_at06_shipment_announced_twice_is_rejected(self):
        self.service.submit(manifest_json(), "REST")
        outcome = self.service.submit(manifest_json(messageRef="OSP-MSG-88413"), "REST")
        self.assertEqual(outcome.status, "REJECTED")
        self.assertEqual(self.error_codes(outcome), ["V-SHIPMENT-EXISTS"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM vehicle")[0][0], 3)

    def test_at07_database_unavailable_message_waits_and_recovers(self):
        with ExitStack() as held:  # every pooled connection is busy
            for _ in range(self.env.pool.size):
                held.enter_context(self.env.pool.connection())
            outcome = self.service.submit(manifest_json(), "REST")
            self.assertEqual(outcome.status, "PENDING")
            self.assertEqual(len(self.env.spool), 1)
            self.assertEqual(self.service.drain_spool(), 0)  # still down: nothing lost, nothing done
        self.assertEqual(self.service.drain_spool(), 1)
        self.assertEqual(len(self.env.spool), 0)
        self.assertEqual(self.query("SELECT status FROM edi_message")[0][0], "ACCEPTED")

    def test_at08_unreadable_payload_is_stored_as_rejected(self):
        outcome = self.service.submit("UNB+UNOC:3+HRN'UNH+1+VMANIF", "EDI")
        self.assertEqual(self.error_codes(outcome), ["E-SYNTAX"])
        self.assertEqual(self.query("SELECT raw_payload FROM edi_message")[0][0], "UNB+UNOC:3+HRN'UNH+1+VMANIF")

    def test_at09_partner_in_onboarding_is_rejected_until_activated(self):
        outcome = self.service.submit(sample("sample-edi-gnt-utc.edi"), "EDI")
        self.assertEqual(self.error_codes(outcome), ["V-PARTNER-INACTIVE"])
        with sqlite3.connect(self.env.settings.db_path) as conn:
            conn.execute("UPDATE partner SET status = 'ACTIVE' WHERE partner_id = 'GNT'")
        retry = sample("sample-edi-gnt-utc.edi").replace("770001", "770002")
        self.assertEqual(self.service.submit(retry, "EDI").status, "ACCEPTED")

    def test_at14_partner_must_use_its_registered_channel(self):
        outcome = self.service.submit(manifest_json(partnerId="HRN"), "REST")
        self.assertEqual(self.error_codes(outcome), ["V-PARTNER-CHANNEL"])

    def test_at12_prb001_pool_is_whole_after_failed_units_of_work(self):
        """Regression test for PRB-001: the error path must return its connection."""
        self.service.submit(manifest_json(), "REST")
        for n in range(self.env.pool.size * 2):
            outcome = self.service.submit(manifest_json(messageRef=f"RESEND-{n}"), "REST")
            self.assertEqual(outcome.status, "REJECTED")
        self.assertEqual(self.env.pool.available, self.env.pool.size)


class Inc001ReproductionTest(unittest.TestCase):
    """With the 1.2.0 defect switched back on, the INC-001 symptoms appear."""

    def test_leaking_error_path_exhausts_the_pool(self):
        env = Env(pool_size=3, leak_on_error=True)
        try:
            env.service.submit(manifest_json(), "REST")
            for n in range(3):  # each resent shipment hits the unique key and leaks one connection
                env.service.submit(manifest_json(messageRef=f"RESEND-{n}"), "REST")
            self.assertEqual(env.pool.available, 0)
            outcome = env.service.submit(manifest_json(messageRef="NEW", shipmentId="OSP-NEW"), "REST")
            self.assertEqual(outcome.status, "PENDING")
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
