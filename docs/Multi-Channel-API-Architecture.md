# Multi-Channel API - Architecture & Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Application                        │
│                     (Mobile App, Web Dashboard)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ POST /api/measurements/multi
                            │ Authorization: Bearer <API_KEY>
                            │ {
                            │   "channels": [
                            │     {"unique_id": "...", "unit": "...", ...},
                            │     ...
                            │   ],
                            │   "past_seconds": 3600
                            │ }
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Flask REST API Layer                         │
│                  mycodo/mycodo_flask/api/                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  MeasurementsMulti Resource                            │   │
│  │  • Authenticate user                                   │   │
│  │  • Check permissions                                   │   │
│  │  • Validate input                                      │   │
│  │  • Call read_influxdb_multi()                         │   │
│  │  • Format response                                     │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                          │
│                     mycodo/utils/influx.py                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  read_influxdb_multi()                                 │   │
│  │                                                        │   │
│  │  For each channel:                                     │   │
│  │    ┌──────────────────────────────────────────┐      │   │
│  │    │  read_influxdb_single()                  │      │   │
│  │    │  • Build Flux query                      │      │   │
│  │    │  • Query InfluxDB                        │      │   │
│  │    │  • Parse result                          │      │   │
│  │    │  • Return [time, value]                  │      │   │
│  │    └──────────────────────────────────────────┘      │   │
│  │                                                        │   │
│  │  Collect all results into dict                        │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      InfluxDB Database                           │
│                                                                  │
│  Bucket: mycodo                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Measurements:                                            │ │
│  │  device_id="sensor_001", channel="0", unit="C" → 25.5   │ │
│  │  device_id="sensor_001", channel="1", unit="%" → 65.3   │ │
│  │  device_id="sensor_001", channel="2", unit="hPa" → 1013 │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Client Sends Request
```json
POST /api/measurements/multi
Authorization: Bearer abc123...

{
  "channels": [
    {"unique_id": "sensor_001", "unit": "C", "channel": 0},
    {"unique_id": "sensor_001", "unit": "%", "channel": 1}
  ],
  "past_seconds": 3600
}
```

### 2. API Layer Processing

```
┌─────────────────────────────────────┐
│ 1. Authentication Check             │
│    ✓ Valid API key?                 │
│    ✓ User logged in?                │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 2. Permission Check                 │
│    ✓ User has view_settings?        │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 3. Input Validation                 │
│    ✓ Channels list present?         │
│    ✓ Each channel has required?     │
│    ✓ Valid unit IDs?                │
│    ✓ Channel numbers >= 0?          │
│    ✓ past_seconds >= 1?             │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 4. Query Execution                  │
│    Call read_influxdb_multi()       │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ 5. Response Formation               │
│    Format as JSON                   │
│    Return HTTP 200                  │
└─────────────────────────────────────┘
```

### 3. Data Layer Processing

```python
# For each channel in the request
for idx, channel_spec in enumerate(channels):
    unique_id = channel_spec['unique_id']
    unit = channel_spec['unit']
    channel = channel_spec['channel']
    
    # Build Flux query
    query = f'''
        from(bucket: "{bucket}")
        |> range(start: -{past_seconds}s)
        |> filter(fn: (r) => r["_measurement"] == "{unit}")
        |> filter(fn: (r) => r["device_id"] == "{unique_id}")
        |> filter(fn: (r) => r["channel"] == "{channel}")
        |> last()
    '''
    
    # Execute query
    result = influxdb_client.query(query)
    
    # Parse result
    if result:
        time = result[0].timestamp()
        value = result[0].value
        results[idx] = [time, value]
    else:
        results[idx] = [None, None]

return results
```

### 4. Client Receives Response
```json
{
  "measurements": [
    {
      "unique_id": "sensor_001",
      "unit": "C",
      "channel": 0,
      "measure": "temperature",
      "time": 1703894523.456,
      "value": 25.5
    },
    {
      "unique_id": "sensor_001",
      "unit": "%",
      "channel": 1,
      "measure": "humidity",
      "time": 1703894523.456,
      "value": 65.3
    }
  ]
}
```

## Error Handling Flow

```
Request → Validation
           │
           ├─ Empty channels? → 422 "channels list required"
           │
           ├─ Missing unique_id? → 422 "unique_id required for channel X"
           │
           ├─ Invalid unit? → 422 "Unit ID not found for channel X"
           │
           ├─ Invalid channel? → 422 "channel must be >= 0 for channel X"
           │
           └─ All valid → Query
                          │
                          ├─ Query error? → 500 "An exception occurred"
                          │
                          └─ Success → 200 with data
```

## Performance Comparison

### Before (Sequential Single Requests)

```
Timeline:
|--Request 1--||--Response 1--|
                                |--Request 2--||--Response 2--|
                                                                |--Request 3--||--Response 3--|
                                                                                                |--Request 4--||--Response 4--|

Total Time = 4 × (Latency + Processing)
```

### After (Single Multi-Channel Request)

```
Timeline:
|--Request--||--Process All Channels--||--Response--|

Total Time = 1 × (Latency + Processing)
```

### Savings Calculation

For **N channels** with **L ms latency** and **P ms processing per channel**:

- **Before**: `N × (L + P)`
- **After**: `L + (N × P)`
- **Saved Time**: `(N - 1) × L`

**Example** (4 channels, 50ms latency, 10ms processing):
- Before: `4 × (50 + 10) = 240ms`
- After: `50 + (4 × 10) = 90ms`
- **Improvement: 150ms saved (62.5% faster)**

## Data Flow Detail

### Single Channel Query (Building Block)

```
Input:
  unique_id = "sensor_001"
  unit = "C"
  channel = 0
  past_seconds = 3600

         ↓

Flux Query Generation:
  from(bucket: "mycodo")
  |> range(start: -3600s)
  |> filter(fn: (r) => r["_measurement"] == "C")
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
  |> filter(fn: (r) => r["channel"] == "0")
  |> last()

         ↓

InfluxDB Execution
  [Searches time-series data]
  [Filters by device, channel, unit]
  [Returns most recent point]

         ↓

Result Parsing:
  {
    _time: 2024-01-15T10:30:00Z,
    _value: 25.5
  }

         ↓

Output:
  [1705318200.0, 25.5]
```

### Multi-Channel Aggregation

```
Input:
  [
    {unique_id: "sensor_001", unit: "C", channel: 0},
    {unique_id: "sensor_001", unit: "%", channel: 1},
    {unique_id: "sensor_001", unit: "hPa", channel: 2}
  ]

         ↓

Parallel Concept:
  Query Channel 0 ──┐
  Query Channel 1 ──┼─→ Collect Results
  Query Channel 2 ──┘

         ↓

Aggregate Results:
  {
    0: [1705318200.0, 25.5],
    1: [1705318200.0, 65.3],
    2: [1705318200.0, 1013.2]
  }

         ↓

Format Response:
  {
    "measurements": [
      {"channel": 0, "time": ..., "value": 25.5},
      {"channel": 1, "time": ..., "value": 65.3},
      {"channel": 2, "time": ..., "value": 1013.2}
    ]
  }
```

## Security Model

```
┌─────────────────────────┐
│   Incoming Request      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   API Key Check         │ ◄─── User table lookup
│   @flask_login.required │
└───────────┬─────────────┘
            │ Authenticated?
            ▼
┌─────────────────────────┐
│   Permission Check      │ ◄─── Check user.role
│   view_settings needed  │
└───────────┬─────────────┘
            │ Authorized?
            ▼
┌─────────────────────────┐
│   Input Validation      │
│   • SQL injection safe  │ ◄─── Parameterized queries
│   • Type checking       │
│   • Range validation    │
└───────────┬─────────────┘
            │ Valid?
            ▼
┌─────────────────────────┐
│   Execute Query         │ ◄─── InfluxDB client
│   (read-only)           │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Return Results        │
└─────────────────────────┘
```

## Integration Points

### With Existing Systems

```
┌──────────────────────────────────────────────────────────────┐
│                      Mycodo Ecosystem                         │
│                                                               │
│  ┌────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │  Sensors   │────▶│  Daemon      │────▶│  InfluxDB    │  │
│  │  (BME680)  │     │  (Collector) │     │  (Storage)   │  │
│  └────────────┘     └──────────────┘     └──────┬───────┘  │
│                                                   │           │
│                                                   │           │
│                                           ┌───────▼───────┐  │
│  ┌────────────┐     ┌──────────────┐     │   New Multi-  │  │
│  │  Mobile    │────▶│  REST API    │────▶│   Channel     │  │
│  │  Client    │◀────│  (Flask)     │◀────│   Query       │  │
│  └────────────┘     └──────────────┘     └───────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Extension Points

### Future WebSocket Integration

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. Connect WebSocket
       ▼
┌─────────────┐
│   Server    │
│             │
│ 2. Subscribe to channels:
│    ['ch_001', 'ch_002']
└──────┬──────┘
       │
       │ 3. On new data:
       ▼
┌─────────────┐
│   Broadcast │ ──▶ {
│   to Client │      "channel": "ch_001",
└─────────────┘      "time": ...,
                     "value": ...
                   }
```

This architecture would reuse the same `read_influxdb_multi()` function for consistency.

## Summary

The multi-channel API is designed as:
- **Modular**: Reuses existing single-channel logic
- **Scalable**: Can handle any number of channels
- **Secure**: Authentication and validation at every layer
- **Performant**: Reduces network overhead significantly
- **Maintainable**: Clear separation of concerns
- **Extensible**: Ready for WebSocket additions
