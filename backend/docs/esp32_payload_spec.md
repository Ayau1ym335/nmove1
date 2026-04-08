# NMove ESP32 Payload Specification

## Endpoint
POST /sessions/ingest
Authorization: Bearer <patient_jwt_token>
Content-Type: application/json

## Full payload example
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "ESP32-A1B2C3",
  "readings": [
    {
      "timestamp": "2024-01-15T10:30:00.123Z",
      "ax": 0.12,
      "ay": -9.81,
      "az": 0.05,
      "gx": 1.2,
      "gy": -0.8,
      "gz": 0.3,
      "leg_side": "left",
      "temperature": 36.5,
      "sequence_number": 1042
    }
  ]
}
```

## Field reference

| Field            | Type    | Required | Range              | Notes                        |
|------------------|---------|----------|--------------------|------------------------------|
| session_id       | UUID    | Yes      | —                  | From POST /sessions/start    |
| device_id        | string  | No       | max 100 chars      | ESP32 chip ID                |
| readings         | array   | Yes      | 1–500 items        | One batch per HTTP call      |
| timestamp        | string  | Yes      | ISO 8601 + UTC     | e.g. 2024-01-15T10:30:00Z   |
| ax / ay / az     | float   | Yes      | ±156.9 m/s²        | Accelerometer axes           |
| gx / gy / gz     | float   | Yes      | ±2000 deg/s        | Gyroscope axes               |
| leg_side         | string  | Yes      | "left" or "right"  | All readings same side       |
| temperature      | float   | No       | -40 to 125 °C      | ESP32 chip temperature       |
| sequence_number  | integer | No       | 0–65535            | Rolls over at 65535          |

## Recommended batch size
Send batches of 50–100 readings every 500ms for real-time feel.
Maximum 500 readings per request.
All readings in a batch must be from the same leg_side.

## Typical session flow
1. POST /sessions/start → get session_id
2. POST /sessions/ingest (repeat every 500ms)
3. POST /sessions/{session_id}/close

## Error codes
| Status | Meaning                                      |
|--------|----------------------------------------------|
| 202    | Accepted — all readings written              |
| 400    | Validation error — check detail field        |
| 401    | Missing or invalid JWT                       |
| 403    | Token is not a patient token                 |
| 404    | session_id not found or wrong user           |
| 409    | Session is already closed                    |
| 500    | Server error — retry with backoff            |
