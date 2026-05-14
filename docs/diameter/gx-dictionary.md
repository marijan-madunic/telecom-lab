# Gx Diameter Dictionary Mapping

This document describes the simplified Diameter AVP mapping used in the telecom-lab PCRF policy-control flow.

The implementation does not provide a full 3GPP Diameter stack. Instead, it simulates Gx-style CCR/CCA signaling using structured JSON payloads and Diameter-inspired AVP names.

## Example CCR Payload

```json
{
  "session_id": "session-001",
  "imsi": "001010000000001",
  "apn": "internet",
  "qos_class": "gold",
  "requested_bandwidth": "100Mbps"
}
