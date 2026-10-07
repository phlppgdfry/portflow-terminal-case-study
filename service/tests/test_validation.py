import unittest

from portflow.model import Manifest, Vehicle
from portflow.validation import VIN_PATTERN, validate


def manifest(**overrides) -> Manifest:
    base = dict(
        channel="REST",
        partner_id="OSP",
        message_ref="M1",
        shipment_ref="S1",
        expected_arrival="2026-10-08T09:30",
        terminal_code="BEZEE",
        vehicles=[Vehicle("YV1XZK9V1R2000731"), Vehicle("KNAB2512AST123456")],
    )
    base.update(overrides)
    return Manifest(**base)


def codes(m: Manifest) -> list[str]:
    return [i.code for i in validate(m, "BEZEE")]


class VinTest(unittest.TestCase):
    def test_valid_vins(self):
        for vin in ("WVWZZZE1ZPP012345", "VF1RJB00X71234567", "SALGA2BJ0RA112233"):
            self.assertRegex(vin, VIN_PATTERN)

    def test_invalid_vins(self):
        for vin in ("WVWZZZE1ZPP01234", "WVWZZZE1ZPP0123456", "WVWZZZE1ZPP0123O5", "wvwzzze1zpp012345", "WVWZZZE1ZPP0123I5"):
            self.assertNotRegex(vin, VIN_PATTERN, vin)


class RuleTest(unittest.TestCase):
    def test_valid_manifest_has_no_issues(self):
        self.assertEqual(codes(manifest()), [])

    def test_missing_mandatory_fields(self):
        self.assertEqual(
            codes(manifest(partner_id=None, shipment_ref="", expected_arrival=None)),
            ["V-REQUIRED", "V-REQUIRED", "V-REQUIRED"],
        )

    def test_other_terminal_is_rejected(self):
        self.assertEqual(codes(manifest(terminal_code="BEANR")), ["V-TERMINAL"])

    def test_empty_manifest_is_rejected(self):
        self.assertEqual(codes(manifest(vehicles=[])), ["V-NO-VEHICLES"])

    def test_vin_problems_are_reported_per_vehicle(self):
        m = manifest(vehicles=[Vehicle("YV1XZK9V1R2000731"), Vehicle("YV1XZK9V1R2000731"), Vehicle("BAD"), Vehicle(None)])
        issues = validate(m, "BEZEE")
        self.assertEqual(
            [(i.code, i.field) for i in issues],
            [
                ("V-VIN-DUPLICATE", "vehicles[1].vin"),
                ("V-VIN-FORMAT", "vehicles[2].vin"),
                ("V-REQUIRED", "vehicles[3].vin"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
