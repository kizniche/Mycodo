# Multi-Channel Measurement API - Implementation Summary

## Overview

This implementation adds a REST API endpoint for querying multiple sensor measurement channels in a single HTTP request, addressing the issue raised about inefficient mobile client operations when dealing with multi-channel sensors.

## Problem Solved

**Original Issue**: Mobile clients had to make N separate API calls to query N sensor channels, resulting in:
- High network overhead
- Increased latency (N round-trips)
- Battery drain on mobile devices
- Inefficient use of network resources

**Solution**: New `POST /api/measurements/multi` endpoint that accepts multiple channel specifications and returns all measurements in one response.

## Implementation Details

### 1. Core Function: `read_influxdb_multi()` 
**Location**: `mycodo/utils/influx.py`

```python
def read_influxdb_multi(channels_data, past_seconds=None, value='LAST')
```

**Features**:
- Queries multiple channels efficiently
- Reuses existing `read_influxdb_single()` for reliability
- Handles errors gracefully per-channel
- Returns indexed dictionary of results

**Design Decision**: Rather than creating complex multi-channel InfluxDB queries, this function iterates through channels using the proven single-channel query function. This approach:
- Leverages battle-tested code
- Ensures one failing channel doesn't break others
- Maintains consistency with existing behavior
- Simplifies error handling and debugging

### 2. REST API Endpoint
**Location**: `mycodo/mycodo_flask/api/measurement.py`

```python
@ns_measurement.route('/multi')
class MeasurementsMulti(Resource)
```

**Security**:
- Requires authentication (`@flask_login.login_required`)
- Checks user permissions (`view_settings`)
- Validates all input parameters

**Validation**:
- Channels list cannot be empty
- Each channel must have: unique_id, unit, channel
- Unit must exist in system
- Channel number must be >= 0
- past_seconds must be >= 1

**Error Handling**:
- 403: Permission denied
- 422: Invalid input with specific error message
- 500: Unexpected server error with traceback

### 3. API Models
**Location**: `mycodo/mycodo_flask/api/measurement.py`

Four new Flask-RESTX models for type safety and API documentation:
- `channel_spec_fields`: Single channel specification
- `multi_measurement_request_fields`: Complete request
- `multi_measurement_channel_result`: Single result
- `multi_measurement_response_fields`: Complete response

### 4. Testing
**Location**: `mycodo/tests/software_tests/test_influxdb/test_influxdb.py`

New test function: `test_influxdb_multi()`
- Writes test data to multiple channels
- Queries using multi-channel function
- Validates correct values returned for each channel

### 5. Documentation

**API Usage Guide** (`docs/Multi-Channel-API-Example.md`):
- Complete API reference
- Request/response formats
- Multiple usage examples (curl, Python)
- Real-world sensor scenarios (BME680)
- Error handling

**Testing Guide** (`docs/Multi-Channel-API-Testing.md`):
- Automated test instructions
- 6 manual testing scenarios
- Performance testing methodology
- Verification checklist
- Common issues and solutions

## Performance Benefits

### Before (N separate requests):
```
Time = (N channels) × (latency + processing_time)
```

### After (single multi-channel request):
```
Time = 1 × (latency + N × processing_time)
```

**Savings**: Eliminates (N-1) network round-trips

**Example**: For a BME680 sensor with 4 channels and 50ms latency:
- Before: 4 × (50ms + 10ms) = 240ms
- After: 1 × (50ms + 40ms) = 90ms
- **Improvement: 62.5% faster**

## Usage Example

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
      }
    ],
    "past_seconds": 3600
  }'
```

## Backward Compatibility

✅ **100% Backward Compatible**
- No changes to existing API endpoints
- No changes to database schema
- No changes to existing functionality
- New endpoint is purely additive

## WebSocket Support

**Status**: Not implemented in this PR

**Rationale**:
1. Current codebase lacks WebSocket infrastructure (Flask-SocketIO not present)
2. Would require significant additional work:
   - Add Flask-SocketIO dependency
   - Create connection management system
   - Implement subscription/unsubscription logic
   - Add real-time push notification system
   - Test concurrent connections and scalability

3. REST API provides core functionality needed
4. Can be extended to WebSocket in future PR

**Recommendation**: Implement WebSocket as separate feature after REST API is validated in production.

## Code Quality

### Testing
- ✅ Unit test for multi-channel function
- ✅ Python syntax validation passed
- ✅ Follows existing test patterns
- ⏳ Integration testing requires live environment

### Code Style
- ✅ Follows existing Mycodo patterns
- ✅ Consistent naming conventions
- ✅ Comprehensive docstrings
- ✅ Clear error messages
- ✅ Proper type hints in comments

### Security
- ✅ Authentication required
- ✅ Permission checks enforced
- ✅ Input validation comprehensive
- ✅ SQL injection not possible (parameterized queries)
- ✅ No sensitive data in error messages

## Files Modified

| File | Lines Added | Purpose |
|------|-------------|---------|
| `mycodo/utils/influx.py` | +59 | Core multi-channel query function |
| `mycodo/mycodo_flask/api/measurement.py` | +129 | REST API endpoint and models |
| `mycodo/tests/software_tests/test_influxdb/test_influxdb.py` | +52 | Unit test |
| `docs/Multi-Channel-API-Example.md` | +212 | API documentation |
| `docs/Multi-Channel-API-Testing.md` | +247 | Testing guide |
| **Total** | **+699** | |

## Deployment Notes

### No Migration Required
- No database schema changes
- No configuration changes required
- No dependency changes

### Deployment Steps
1. Deploy code update
2. Restart Flask application
3. Endpoint automatically available at `/api/measurements/multi`
4. No additional configuration needed

### Rollback Plan
If issues arise, simply revert the changes. The new endpoint is completely isolated and doesn't affect existing functionality.

## Future Enhancements

### 1. WebSocket Support (Separate PR)
Add real-time multi-channel subscriptions:
```javascript
socket.on('connect', function() {
  socket.emit('subscribe', {
    channels: ['ch1', 'ch2', 'ch3']
  });
});

socket.on('measurements', function(data) {
  console.log('Received:', data);
});
```

### 2. Batch Write Endpoint
Add ability to write multiple measurements at once:
```
POST /api/measurements/multi/create
```

### 3. Historical Multi-Channel
Extend to support historical ranges, not just last value:
```json
{
  "channels": [...],
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-02T00:00:00Z"
}
```

### 4. Aggregation Functions
Support different aggregation per channel:
```json
{
  "channels": [
    {"unique_id": "sensor1", "unit": "C", "channel": 0, "aggregation": "MEAN"},
    {"unique_id": "sensor1", "unit": "%", "channel": 1, "aggregation": "MAX"}
  ]
}
```

## Success Metrics

### Before Deployment
- [ ] All unit tests pass
- [ ] Code review approved
- [ ] Documentation reviewed
- [ ] Security review completed

### After Deployment
- [ ] Monitor API response times
- [ ] Track error rates for new endpoint
- [ ] Collect user feedback
- [ ] Measure reduction in API calls
- [ ] Monitor mobile client battery usage

## Conclusion

This implementation provides a clean, efficient solution to the multi-channel querying problem with:
- ✅ Minimal code changes (699 lines total)
- ✅ Comprehensive documentation
- ✅ Backward compatibility
- ✅ Proper testing
- ✅ Security maintained
- ✅ Performance improvements

The REST API provides immediate value to mobile clients while leaving the door open for WebSocket enhancements in the future.
