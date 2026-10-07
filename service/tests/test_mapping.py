import unittest

from portflow.edi import from_edi, tokenize
from portflow.mapping import PayloadSyntaxError, from_json, parse_edi_arrival

from helpers import sample


class EdiParsingTest(unittest.TestCase):
    def test_sample_message_maps_to_canonical_manifest(self):
        manifest, issues = from_edi(sample("sample-edi-message.edi"))
        self.assertEqual(issues, [])
        self.assertEqual(manifest.partner_id, "HRN")
        self.assertEqual(manifest.message_ref, "000125")
        self.assertEqual(manifest.shipment_ref, "HRN-2026-00125")
        self.assertEqual(manifest.expected_arrival, "2026-10-08T14:00")
        self.assertEqual(manifest.terminal_code, "BEZEE")
        self.assertEqual([v.vin for v in manifest.vehicles][:1], ["WVWZZZE1ZPP012345"])
        self.assertEqual((manifest.vehicles[3].make, manifest.vehicles[3].model), ("Renault", "Megane E-Tech"))

    def test_release_character_keeps_separator_as_data(self):
        segments = tokenize("UNB+A+B'FTX+AAI+++Deck 3?: high?'s'UNZ+1'")
        self.assertEqual(segments[1].value(3), "Deck 3: high's")

    def test_at15_utc_arrival_is_converted_to_terminal_time(self):
        # CR-001: Gannet sends UTC (format 303). 11:30 UTC is 13:30 in Zeebrugge in October.
        manifest, issues = from_edi(sample("sample-edi-gnt-utc.edi"))
        self.assertEqual(issues, [])
        self.assertEqual(manifest.expected_arrival, "2026-10-09T13:30")

    def test_unreleased_plus_in_utc_offset_is_rejected(self):
        # CR-001 T2: '+' is the element separator, so it must be sent as '?+'.
        broken = sample("sample-edi-gnt-utc.edi").replace("?+00", "+00")
        _, issues = from_edi(broken)
        self.assertEqual([i.code for i in issues], ["V-ARRIVAL-DATE"])

    def test_winter_time_offset(self):
        self.assertEqual(parse_edi_arrival("202612011130+00", "303")[0], "2026-12-01T12:30")

    def test_date_only_format_is_rejected(self):
        # INC-002: a partner upgrade switched DTM to format 102 (date only).
        manifest, issues = from_edi(sample("sample-edi-invalid.edi"))
        self.assertIsNone(manifest.expected_arrival)
        self.assertEqual([i.code for i in issues], ["V-ARRIVAL-DATE"])

    def test_wrong_segment_count_is_a_syntax_error(self):
        broken = sample("sample-edi-message.edi").replace("UNT+19+1", "UNT+18+1")
        with self.assertRaisesRegex(PayloadSyntaxError, "UNT segment count"):
            from_edi(broken)

    def test_control_reference_mismatch_is_a_syntax_error(self):
        broken = sample("sample-edi-message.edi").replace("UNZ+1+000125", "UNZ+1+000999")
        with self.assertRaisesRegex(PayloadSyntaxError, "control reference"):
            from_edi(broken)

    def test_truncated_interchange_is_a_syntax_error(self):
        truncated = sample("sample-edi-message.edi").rstrip().rstrip("'")
        with self.assertRaises(PayloadSyntaxError):
            from_edi(truncated)

    def test_replacement_messages_are_not_supported(self):
        replaced = sample("sample-edi-message.edi").replace("BGM+VMN+HRN-2026-00125+9", "BGM+VMN+HRN-2026-00125+5")
        _, issues = from_edi(replaced)
        self.assertEqual([i.code for i in issues], ["V-FUNCTION"])


class JsonMappingTest(unittest.TestCase):
    def test_offset_is_converted_to_terminal_time(self):
        manifest, issues = from_json(sample("sample-vehicle-import.json"))
        self.assertEqual(issues, [])
        self.assertEqual(manifest.expected_arrival, "2026-10-08T09:30")
        self.assertEqual(manifest.shipment_ref, "OSP-2026-03317")

    def test_invalid_json_is_a_syntax_error(self):
        with self.assertRaises(PayloadSyntaxError):
            from_json('{"partnerId": "OSP",')

    def test_date_without_time_is_rejected(self):
        _, issues = from_json('{"expectedArrival": "2026-10-08"}')
        self.assertEqual([i.code for i in issues], ["V-ARRIVAL-DATE"])


if __name__ == "__main__":
    unittest.main()
