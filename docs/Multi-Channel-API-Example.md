# Multi-Channel Measurement API

## Overview

The Multi-Channel Measurement API allows you to query measurements from multiple sensor channels in a single HTTP request, reducing network round-trips and improving efficiency when working with multi-channel sensors like BME680, BME688, or Atlas Scientific multi-probes.

## Endpoint

**POST** `/api/measurements/multi`

## Authentication

Requires authentication using API key in the header:
```
Authorization: Bearer YOUR_API_KEY
```

## Request Format

```json
{
  "channels": [
    {
      "unique_id": "sensor_unique_id",
      "unit": "unit_name",
      "channel": 0,
      "measure": "measurement_type"
    }
  ],
  "past_seconds": 3600
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channels` | array | Yes | List of channel specifications to query |
| `past_seconds` | integer | No | How many seconds in the past to query (default: 3600) |

### Channel Specification

Each channel in the `channels` array must include:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unique_id` | string | Yes | The unique ID of the device |
| `unit` | string | Yes | The unit of the measurement (e.g., 'C', '%', 'hPa') |
| `channel` | integer | Yes | The channel number (0-based) |
| `measure` | string | No | The measurement type (e.g., 'temperature', 'humidity') |

## Response Format

```json
{
  "measurements": [
    {
      "unique_id": "sensor_unique_id",
      "unit": "C",
      "channel": 0,
      "measure": "temperature",
      "time": 1703894523.456,
      "value": 23.5
    },
    {
      "unique_id": "sensor_unique_id",
      "unit": "%",
      "channel": 1,
      "measure": "humidity",
      "time": 1703894523.456,
      "value": 65.3
    }
  ]
}
```

## Examples

### Example 1: Query Multiple Channels from a BME680 Sensor

```bash
curl -X POST "https://mycodo.local/api/measurements/multi" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": [
      {
        "unique_id": "bme680_sensor_001",
        "unit": "C",
        "channel": 0,
        "measure": "temperature"
      },
      {
        "unique_id": "bme680_sensor_001",
        "unit": "%",
        "channel": 1,
        "measure": "humidity"
      },
      {
        "unique_id": "bme680_sensor_001",
        "unit": "hPa",
        "channel": 2,
        "measure": "pressure"
      },
      {
        "unique_id": "bme680_sensor_001",
        "unit": "ohm",
        "channel": 3,
        "measure": "resistance"
      }
    ],
    "past_seconds": 3600
  }'
```

### Example 2: Query Different Sensors

```bash
curl -X POST "https://mycodo.local/api/measurements/multi" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": [
      {
        "unique_id": "temp_sensor_001",
        "unit": "C",
        "channel": 0,
        "measure": "temperature"
      },
      {
        "unique_id": "humidity_sensor_001",
        "unit": "%",
        "channel": 0,
        "measure": "humidity"
      }
    ],
    "past_seconds": 1800
  }'
```

### Example 3: Python Client

```python
import requests

API_URL = "https://mycodo.local/api/measurements/multi"
API_KEY = "YOUR_API_KEY"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "channels": [
        {
            "unique_id": "bme680_sensor_001",
            "unit": "C",
            "channel": 0,
            "measure": "temperature"
        },
        {
            "unique_id": "bme680_sensor_001",
            "unit": "%",
            "channel": 1,
            "measure": "humidity"
        }
    ],
    "past_seconds": 3600
}

response = requests.post(API_URL, json=payload, headers=headers, verify=False)

if response.status_code == 200:
    data = response.json()
    for measurement in data["measurements"]:
        print(f"{measurement['measure']}: {measurement['value']} {measurement['unit']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Error Responses

### 403 Forbidden
User does not have permission to view settings.

### 422 Unprocessable Entity
- Missing or invalid request parameters
- Invalid unit ID
- Invalid channel number (must be >= 0)
- Empty channels list

### 500 Internal Server Error
An exception occurred while processing the request.

## Benefits

1. **Reduced Network Overhead**: Query multiple channels in a single HTTP request instead of multiple requests
2. **Lower Latency**: Single round-trip for all measurements
3. **Power Efficiency**: Particularly beneficial for mobile clients
4. **Synchronized Data**: All measurements are queried in a coordinated manner

## Notes

- The endpoint returns the last measurement for each channel within the specified time window
- If a measurement is not available for a channel, `time` and `value` will be `null`
- The `past_seconds` parameter defaults to 3600 (1 hour) if not specified
- All channels are queried independently, so one failing channel won't affect others

## Future Enhancements

WebSocket support for real-time multi-channel updates is planned for a future release.
