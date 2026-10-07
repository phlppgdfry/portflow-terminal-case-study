-- Fictional sample data for the PortFlow schema. Timestamps are relative to
-- the moment the script runs, so the diagnostic queries always return rows.
-- Payloads are abridged. Partner names and VINs are invented.

INSERT INTO partner (partner_id, name, channel, status, contact_email)
VALUES ('OSP', 'Osprey Vehicle Logistics', 'REST', 'ACTIVE', 'integration@osprey.example');
INSERT INTO partner (partner_id, name, channel, status, contact_email)
VALUES ('HRN', 'Heron Shipping Lines', 'EDI', 'ACTIVE', 'edi-support@heron.example');
INSERT INTO partner (partner_id, name, channel, status, contact_email)
VALUES ('GNT', 'Gannet Auto Carriers', 'EDI', 'ONBOARDING', 'it@gannet.example');

-- Inbound messages: three accepted, four rejected for different reasons.
INSERT INTO edi_message (message_id, partner_code, message_ref, channel, status, shipment_ref, vehicle_count,
                         raw_payload, received_at, processed_at)
VALUES (1, 'HRN', '000119', 'EDI', 'ACCEPTED', 'HRN-2026-00119', 4,
        'UNB+UNOC:3+HRN:ZZZ+PORTFLOW:ZZZ+...+000119''...',
        SYSTIMESTAMP - INTERVAL '5' HOUR, SYSTIMESTAMP - INTERVAL '5' HOUR + INTERVAL '0.4' SECOND);
INSERT INTO edi_message (message_id, partner_code, message_ref, channel, status, shipment_ref, vehicle_count,
                         raw_payload, received_at, processed_at)
VALUES (2, 'HRN', '000120', 'EDI', 'REJECTED', 'HRN-2026-00120', 2,
        'UNB+UNOC:3+HRN:ZZZ+PORTFLOW:ZZZ+...+000120''...DTM+132:20261010:102''...',
        SYSTIMESTAMP - INTERVAL '3' HOUR, SYSTIMESTAMP - INTERVAL '3' HOUR + INTERVAL '0.2' SECOND);
INSERT INTO edi_message (message_id, partner_code, message_ref, channel, status, shipment_ref, vehicle_count,
                         raw_payload, received_at, processed_at)
VALUES (3, 'OSP', 'OSP-MSG-88401', 'REST', 'ACCEPTED', 'OSP-2026-03310', 3,
        '{"partnerId":"OSP","messageRef":"OSP-MSG-88401","shipmentId":"OSP-2026-03310",...}',
        SYSTIMESTAMP - INTERVAL '2' HOUR, SYSTIMESTAMP - INTERVAL '2' HOUR + INTERVAL '0.1' SECOND);
INSERT INTO edi_message (message_id, partner_code, message_ref, channel, status, shipment_ref, vehicle_count,
                         raw_payload, received_at, processed_at)
VALUES (4, 'HRN', '000121', 'EDI', 'REJECTED', 'HRN-2026-00121', 3,
        'UNB+UNOC:3+HRN:ZZZ+PORTFLOW:ZZZ+...+000121''...PIA+5+WVWZZZE1ZPP0123O5:VIN''...',
        SYSTIMESTAMP - INTERVAL '1' HOUR, SYSTIMESTAMP - INTERVAL '1' HOUR + INTERVAL '0.3' SECOND);
INSERT INTO edi_message (message_id, partner_code, message_ref, channel, status, shipment_ref, vehicle_count,
                         raw_payload, received_at, processed_at)
VALUES (5, 'OSP', 'OSP-MSG-88402', 'REST', 'REJECTED', 'OSP-2026-03310', 3,
        '{"partnerId":"OSP","messageRef":"OSP-MSG-88402","shipmentId":"OSP-2026-03310",...}',
        SYSTIMESTAMP - INTERVAL '30' MINUTE, SYSTIMESTAMP - INTERVAL '30' MINUTE + INTERVAL '0.1' SECOND);
INSERT INTO edi_message (message_id, partner_code, message_ref, channel, status, shipment_ref, vehicle_count,
                         raw_payload, received_at, processed_at)
VALUES (6, 'GNT', '770001', 'EDI', 'REJECTED', 'GNT-26-4410', 2,
        'UNB+UNOC:3+GNT:ZZZ+PORTFLOW:ZZZ+...+770001''...',
        SYSTIMESTAMP - INTERVAL '20' MINUTE, SYSTIMESTAMP - INTERVAL '20' MINUTE + INTERVAL '0.1' SECOND);
INSERT INTO edi_message (message_id, partner_code, message_ref, channel, status, shipment_ref, vehicle_count,
                         raw_payload, received_at, processed_at)
VALUES (7, 'OSP', 'OSP-MSG-88412', 'REST', 'ACCEPTED', 'OSP-2026-03317', 3,
        '{"partnerId":"OSP","messageRef":"OSP-MSG-88412","shipmentId":"OSP-2026-03317",...}',
        SYSTIMESTAMP - INTERVAL '10' MINUTE, SYSTIMESTAMP - INTERVAL '10' MINUTE + INTERVAL '6.5' SECOND);

INSERT INTO message_error (message_id, error_code, field_path, detail)
VALUES (2, 'V-ARRIVAL-DATE', 'DTM+132', 'date format 102 not accepted; use 203 or 303');
INSERT INTO message_error (message_id, error_code, field_path, detail)
VALUES (4, 'V-VIN-FORMAT', 'vehicles[0].vin', '''WVWZZZE1ZPP0123O5'' is not a valid VIN');
INSERT INTO message_error (message_id, error_code, field_path, detail)
VALUES (5, 'V-SHIPMENT-EXISTS', 'shipmentId', 'shipment OSP-2026-03310 was already announced');
INSERT INTO message_error (message_id, error_code, field_path, detail)
VALUES (6, 'V-PARTNER-INACTIVE', 'partnerId', 'partner status is ONBOARDING');

-- Shipments created by the accepted messages.
INSERT INTO shipment (shipment_id, partner_id, shipment_ref, terminal_code, expected_arrival, message_id)
VALUES (1, 'HRN', 'HRN-2026-00119', 'BEZEE', SYSTIMESTAMP - INTERVAL '3' HOUR, 1);
INSERT INTO shipment (shipment_id, partner_id, shipment_ref, terminal_code, expected_arrival, message_id)
VALUES (2, 'OSP', 'OSP-2026-03310', 'BEZEE', SYSTIMESTAMP + INTERVAL '4' HOUR, 3);
INSERT INTO shipment (shipment_id, partner_id, shipment_ref, terminal_code, expected_arrival, message_id)
VALUES (3, 'OSP', 'OSP-2026-03317', 'BEZEE', SYSTIMESTAMP + INTERVAL '1' DAY, 7);

INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status, arrived_at)
VALUES (1, 1, 'WVWZZZE1ZPP012345', 'Volkswagen', 'ID.4', 'ARRIVED', SYSTIMESTAMP - INTERVAL '170' MINUTE(3));
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status, arrived_at)
VALUES (2, 1, 'WVGZZZE2ZRP004211', 'Volkswagen', 'ID.5', 'ARRIVED', SYSTIMESTAMP - INTERVAL '165' MINUTE(3));
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status, arrived_at)
VALUES (3, 1, 'TMBJR7NX3RY004422', 'Skoda', 'Enyaq', 'ARRIVED', SYSTIMESTAMP - INTERVAL '160' MINUTE(3));
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status)
VALUES (4, 1, 'VF1RJB00X71234567', 'Renault', 'Megane E-Tech', 'EXPECTED');
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status)
VALUES (5, 2, 'YV1XZK9V1R2000731', 'Volvo', 'EX30', 'EXPECTED');
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status)
VALUES (6, 2, 'KNAB2512AST123456', 'Kia', 'EV3', 'EXPECTED');
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status)
VALUES (7, 2, 'YV1XZK9V1R2000748', 'Volvo', 'EX30', 'EXPECTED');
-- The same Kia announced again on the next shipment: a data-quality finding for query Q8.
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status)
VALUES (8, 3, 'KNAB2512AST123456', 'Kia', 'EV3', 'EXPECTED');
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status)
VALUES (9, 3, 'WBA11AA020CK45678', 'BMW', 'iX1', 'EXPECTED');
INSERT INTO vehicle (vehicle_id, shipment_id, vin, make, model, status)
VALUES (10, 3, 'SALGA2BJ0RA112233', 'Land Rover', 'Range Rover', 'EXPECTED');

INSERT INTO terminal_event (vehicle_id, vin, event_type, event_time, source)
VALUES (1, 'WVWZZZE1ZPP012345', 'ARRIVED', SYSTIMESTAMP - INTERVAL '170' MINUTE(3), 'GATE');
INSERT INTO terminal_event (vehicle_id, vin, event_type, event_time, source)
VALUES (2, 'WVGZZZE2ZRP004211', 'ARRIVED', SYSTIMESTAMP - INTERVAL '165' MINUTE(3), 'GATE');
INSERT INTO terminal_event (vehicle_id, vin, event_type, event_time, source)
VALUES (3, 'TMBJR7NX3RY004422', 'ARRIVED', SYSTIMESTAMP - INTERVAL '160' MINUTE(3), 'GATE');

COMMIT;
