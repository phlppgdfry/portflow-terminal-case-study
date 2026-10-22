"""Standalone synthetic terminal-event reference model; no HTTP or persistence adapter."""
from copy import deepcopy
from datetime import datetime
import json
import re

from .validation import VIN_PATTERN


class EventError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)', value
    ):
        raise EventError('TIMESTAMP', 'Use an ISO timestamp with seconds and an explicit offset.')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise EventError('TIMESTAMP', 'Invalid calendar time or UTC offset.') from exc


class TerminalLedger:
    """One in-memory ledger. Trusted adapter configuration establishes source access."""
    TYPES = {'gate_in', 'yard_placed', 'hold_opened', 'hold_released', 'gate_out'}
    BASE = {'schemaVersion', 'source', 'eventId', 'terminalId', 'visitId', 'vin',
            'type', 'occurredAt', 'observedAt'}

    def __init__(self, allowed_sources):
        self._allowed = {terminal: set(sources) for terminal, sources in allowed_sources.items()}
        self._accepted = {}
        self._visits = {}

    def state(self, terminal, visit):
        return deepcopy(self._visits.get((terminal, visit)))

    def apply(self, event, received_at):
        """Return applied/replayed plus a detached state; failures never mutate state."""
        if not isinstance(event, dict):
            raise EventError('SHAPE', 'Event must be a JSON object.')
        kind = event.get('type')
        if not isinstance(kind, str) or kind not in self.TYPES:
            raise EventError('TYPE', 'Unsupported event type.')
        extra = {'holdId'} if kind.startswith('hold_') else {'yardLocation'} if kind == 'yard_placed' else set()
        if set(event) != self.BASE | extra:
            raise EventError('SHAPE', 'Missing or unknown fields for this event type.')
        if type(event['schemaVersion']) is not int or event['schemaVersion'] != 1:
            raise EventError('VERSION', 'Only wire schema 1 is supported.')
        for name in (self.BASE - {'schemaVersion'}) | extra:
            if not isinstance(event[name], str) or not event[name].strip() or len(event[name]) > 128:
                raise EventError('FIELD', f'{name} must be a non-empty string of at most 128 characters.')
        if not re.fullmatch(VIN_PATTERN, event['vin']):
            raise EventError('VIN', 'VIN must match the canonical 17-character VIN format.')
        terminal, source = event['terminalId'], event['source']
        if source not in self._allowed.get(terminal, set()):
            raise EventError('SOURCE', 'Source is not configured for this terminal.')
        occurred, observed, received = map(instant, (event['occurredAt'], event['observedAt'], received_at))
        if occurred > observed or observed > received:
            raise EventError('CLOCK_ORDER', 'Require occurredAt <= observedAt <= adapter receipt time.')
        key = (terminal, source, event['eventId'])
        payload = json.dumps(event, sort_keys=True, separators=(',', ':'))
        if key in self._accepted:
            original, result = self._accepted[key]
            if original != payload:
                raise EventError('ID_CONFLICT', 'An accepted source event ID cannot describe different evidence.')
            return {'outcome': 'replayed', **deepcopy(result)}
        visit_key = (terminal, event['visitId'])
        previous = self._visits.get(visit_key)
        if previous:
            if event['vin'] != previous['vin'] or source != previous['source']:
                raise EventError('VISIT_IDENTITY', 'A visit keeps its vehicle and owning source.')
            if occurred < instant(previous['lastOccurredAt']):
                raise EventError('OUT_OF_ORDER', 'Late new evidence needs explicit reconciliation; do not reorder silently.')
            if previous['status'] == 'DEPARTED':
                raise EventError('DEPARTED', 'A completed visit is immutable in this reference model.')
        elif kind != 'gate_in':
            raise EventError('GATE_REQUIRED', 'Gate-in must establish the visit first.')
        state = deepcopy(previous) if previous else {
            'vin': event['vin'], 'source': source, 'status': 'AT_GATE',
            'yardLocation': None, 'openHolds': [],
        }
        if kind == 'gate_in' and previous:
            raise EventError('DUPLICATE_GATE', 'A second gate-in needs a new visit ID.')
        if kind == 'yard_placed':
            state['status'] = 'IN_YARD'
            state['yardLocation'] = event['yardLocation']
        elif kind == 'hold_opened':
            if event['holdId'] in state['openHolds']:
                raise EventError('HOLD_OPEN', 'This hold is already open.')
            state['openHolds'].append(event['holdId'])
            state['openHolds'].sort()
        elif kind == 'hold_released':
            if event['holdId'] not in state['openHolds']:
                raise EventError('HOLD_UNKNOWN', 'Release must reference an open hold.')
            state['openHolds'].remove(event['holdId'])
        elif kind == 'gate_out':
            if state['status'] != 'IN_YARD':
                raise EventError('YARD_REQUIRED', 'Gate-out requires a recorded yard placement.')
            if state['openHolds']:
                raise EventError('HOLD_BLOCKED', 'Every open hold must be released before departure.')
            state['status'] = 'DEPARTED'
        state['lastOccurredAt'] = event['occurredAt']
        state['lastEventId'] = event['eventId']
        self._visits[visit_key] = state
        result = {'state': deepcopy(state), 'receivedAt': received_at}
        self._accepted[key] = (payload, deepcopy(result))
        return {'outcome': 'applied', **result}
