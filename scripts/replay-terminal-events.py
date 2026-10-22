"""Reproduce the synthetic contract scenario, without a server, credentials or dependencies."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'service'))
from portflow.terminal_events import EventError, TerminalLedger


def main():
    fixture = json.loads((ROOT / 'integrations/sample-terminal-events.json').read_text())
    ledger = TerminalLedger({'BEZEE': {'synthetic-tos'}})
    outcomes = []
    for row in fixture['deliveries']:
        try:
            outcome = ledger.apply(row['event'], row['receivedAt'])['outcome']
        except EventError as exc:
            outcome = exc.code
        if outcome != row['expected']:
            raise SystemExit(f"Unexpected outcome for {row['event']['eventId']}: {outcome}")
        outcomes.append(outcome)
    state = ledger.state('BEZEE', 'DEMO-VISIT-001')
    if any(state[k] != value for k, value in fixture['expectedFinal'].items()):
        raise SystemExit('Final state does not match the documented fixture.')
    print(json.dumps({'synthetic': True, 'deliveries': len(outcomes), 'outcomes': outcomes,
                      'finalState': state}, indent=2))


if __name__ == '__main__':
    main()
