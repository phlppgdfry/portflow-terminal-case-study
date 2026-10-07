-- Local demo persistence (SQLite). Mirrors database/schema.sql, which is the
-- Oracle target design; keep table and column names identical.

CREATE TABLE IF NOT EXISTS partner (
    partner_id    TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    channel       TEXT NOT NULL CHECK (channel IN ('REST', 'EDI', 'BOTH')),
    status        TEXT NOT NULL CHECK (status IN ('ONBOARDING', 'ACTIVE', 'SUSPENDED')),
    contact_email TEXT,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS edi_message (
    message_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_code  TEXT,
    message_ref   TEXT,
    channel       TEXT NOT NULL CHECK (channel IN ('REST', 'EDI')),
    status        TEXT NOT NULL CHECK (status IN ('ACCEPTED', 'REJECTED')),
    shipment_ref  TEXT,
    vehicle_count INTEGER NOT NULL DEFAULT 0,
    raw_payload   TEXT NOT NULL,
    received_at   TEXT NOT NULL,
    processed_at  TEXT NOT NULL,
    CONSTRAINT uq_message_partner_ref UNIQUE (partner_code, message_ref)
);

CREATE TABLE IF NOT EXISTS message_error (
    error_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES edi_message (message_id),
    error_code TEXT NOT NULL,
    field_path TEXT,
    detail     TEXT
);

CREATE TABLE IF NOT EXISTS shipment (
    shipment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id       TEXT NOT NULL REFERENCES partner (partner_id),
    shipment_ref     TEXT NOT NULL,
    terminal_code    TEXT NOT NULL,
    expected_arrival TEXT NOT NULL,
    message_id       INTEGER NOT NULL REFERENCES edi_message (message_id),
    created_at       TEXT NOT NULL,
    CONSTRAINT uq_shipment_partner_ref UNIQUE (partner_id, shipment_ref)
);

CREATE TABLE IF NOT EXISTS vehicle (
    vehicle_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id INTEGER NOT NULL REFERENCES shipment (shipment_id),
    vin         TEXT NOT NULL,
    make        TEXT,
    model       TEXT,
    status      TEXT NOT NULL DEFAULT 'EXPECTED' CHECK (status IN ('EXPECTED', 'ARRIVED')),
    arrived_at  TEXT,
    CONSTRAINT uq_vehicle_shipment_vin UNIQUE (shipment_id, vin)
);

CREATE TABLE IF NOT EXISTS terminal_event (
    event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle (vehicle_id),
    vin        TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('ARRIVED')),
    event_time TEXT NOT NULL,
    source     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_message_status_received ON edi_message (status, received_at);
CREATE INDEX IF NOT EXISTS ix_vehicle_vin ON vehicle (vin);

INSERT OR IGNORE INTO partner (partner_id, name, channel, status, contact_email) VALUES
    ('OSP', 'Osprey Vehicle Logistics', 'REST', 'ACTIVE', 'integration@osprey.example'),
    ('HRN', 'Heron Shipping Lines', 'EDI', 'ACTIVE', 'edi-support@heron.example'),
    ('GNT', 'Gannet Auto Carriers', 'EDI', 'ONBOARDING', 'it@gannet.example');
