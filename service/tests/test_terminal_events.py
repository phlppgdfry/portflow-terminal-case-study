from copy import deepcopy
import json
from pathlib import Path
import unittest
from portflow.terminal_events import EventError, TerminalLedger

FIXTURE = json.loads((Path(__file__).resolve().parents[2] / 'integrations/sample-terminal-events.json').read_text())

class TerminalEventTest(unittest.TestCase):
    def setUp(self):
        self.ledger = TerminalLedger({'BEZEE': {'synthetic-tos', 'other'}, 'OTHER': {'synthetic-tos'}})

    def apply(self, i, **changes):
        row = deepcopy(FIXTURE['deliveries'][i]); row['event'].update(changes)
        return self.ledger.apply(row['event'], row['receivedAt'])

    def rejects(self, code, fn):
        before = self.ledger.state('BEZEE', 'DEMO-VISIT-001')
        with self.assertRaises(EventError) as error: fn()
        self.assertEqual(error.exception.code, code)
        self.assertEqual(self.ledger.state('BEZEE', 'DEMO-VISIT-001'), before)

    def test_full_fixture(self):
        for row in FIXTURE['deliveries']:
            try: outcome = self.ledger.apply(row['event'], row['receivedAt'])['outcome']
            except EventError as exc: outcome = exc.code
            self.assertEqual(outcome, row['expected'])
        state = self.ledger.state('BEZEE', 'DEMO-VISIT-001')
        for key, value in FIXTURE['expectedFinal'].items(): self.assertEqual(state[key], value)

    def test_hold_blocks_until_matching_release(self):
        for i in (0,1,2): self.apply(i)
        self.rejects('HOLD_BLOCKED', lambda: self.apply(3))
        self.rejects('HOLD_UNKNOWN', lambda: self.apply(4, holdId='wrong'))
        self.apply(4)
        self.assertEqual(self.apply(5)['state']['status'], 'DEPARTED')

    def test_every_hold_must_be_released(self):
        for i in (0,1,2): self.apply(i)
        self.apply(2, eventId='second', holdId='SAFETY')
        self.apply(4)
        self.rejects('HOLD_BLOCKED', lambda: self.apply(5))

    def test_gate_required_before_yard(self):
        self.rejects('GATE_REQUIRED', lambda: self.apply(1))

    def test_yard_required_before_out(self):
        self.apply(0)
        self.rejects('YARD_REQUIRED', lambda: self.apply(5))

    def test_second_gate_requires_new_visit(self):
        self.apply(0)
        self.rejects('DUPLICATE_GATE', lambda: self.apply(0, eventId='new'))
        self.assertEqual(self.apply(0, eventId='visit2', visitId='visit2')['outcome'], 'applied')

    def test_replay_returns_original_without_rewinding(self):
        original = self.apply(0); self.apply(1)
        replay = self.apply(0)
        self.assertEqual(replay['outcome'], 'replayed')
        self.assertEqual(replay['state'], original['state'])
        self.assertEqual(self.ledger.state('BEZEE', 'DEMO-VISIT-001')['status'], 'IN_YARD')
        self.rejects('ID_CONFLICT', lambda: self.apply(0, observedAt='2026-10-22T08:00:02Z'))

    def test_late_new_evidence_needs_reconciliation(self):
        self.apply(0); self.apply(1)
        self.rejects('OUT_OF_ORDER', lambda: self.apply(2, occurredAt='2026-10-22T08:05:00Z'))

    def test_departed_visit_immutable(self):
        for i in (0,1,5): self.apply(i)
        self.rejects('DEPARTED', lambda: self.apply(5, eventId='new'))

    def test_visit_source_and_vehicle_stable(self):
        self.apply(0)
        self.rejects('VISIT_IDENTITY', lambda: self.apply(1, source='other'))
        self.rejects('VISIT_IDENTITY', lambda: self.apply(1, vin='WVWZZZE1ZPP012345'))
        self.rejects('SOURCE', lambda: self.apply(1, source='unknown'))

    def test_terminal_scope_independent(self):
        self.apply(0)
        self.assertEqual(self.apply(0, terminalId='OTHER')['outcome'], 'applied')
        self.assertEqual(self.ledger.state('OTHER', 'DEMO-VISIT-001')['status'], 'AT_GATE')

    def test_schema_shape_vin_and_identity(self):
        for changes, code in [({'schemaVersion':2},'VERSION'), ({'schemaVersion':True},'VERSION'),
                              ({'vin':'BAD'},'VIN'), ({'eventId':' '},'FIELD'),
                              ({'unknown':1},'SHAPE'), ({'type':'release'},'TYPE')]:
            with self.subTest(changes=changes): self.rejects(code, lambda: self.apply(0, **changes))
        self.rejects('SHAPE', lambda: self.ledger.apply([], '2026-10-22T09:00:00Z'))

    def test_clocks_and_offsets(self):
        for value in ['2026-10-22T08:00:00','2026-02-30T08:00:00Z','2026-10-22T08:00:00+00:60']:
            self.rejects('TIMESTAMP', lambda: self.apply(0, occurredAt=value))
        self.rejects('CLOCK_ORDER', lambda: self.apply(0, occurredAt='2026-10-22T09:00:00Z'))
        self.rejects('CLOCK_ORDER', lambda: self.apply(0, observedAt='2026-10-22T09:00:00Z'))
        self.assertEqual(self.apply(0, occurredAt='2026-10-22T10:00:00+02:00')['outcome'], 'applied')

    def test_returned_state_detached(self):
        result = self.apply(0); result['state']['openHolds'].append('injected')
        state = self.ledger.state('BEZEE', 'DEMO-VISIT-001'); state['status'] = 'DEPARTED'
        self.assertEqual(self.apply(0)['state']['openHolds'], [])
        self.assertEqual(self.ledger.state('BEZEE', 'DEMO-VISIT-001')['status'], 'AT_GATE')
