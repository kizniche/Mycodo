# Multi-Channel Measurement API - Testing Guide

## Automated Tests

Run the automated test suite with:
```bash
pytest mycodo/tests/software_tests/test_influxdb/test_influxdb.py::test_influxdb_multi -v
```

## Manual Testing Steps

### Prerequisites
1. Mycodo must be running with InfluxDB configured
2. You need a valid API key for authentication
3. At least one sensor with multiple channels configured (or manual data entries)

### Test Scenario 1: Basic Multi-Channel Query

**Goal**: Verify that multiple channels can be queried in a single request

1. **Setup Test Data** (if needed):
   Use the single-channel API to create test measurements:
   ```bash
   # Create temperature measurement
   curl -X POST "https://localhost/api/measurements/create/test_sensor_001/C/0/25.5" \
     -H "Authorization: Bearer YOUR_API_KEY"
   
   # Create humidity measurement
   curl -X POST "https://localhost/api/measurements/create/test_sensor_001/percent/1/65.3" \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

2. **Query Multi-Channel**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "test_sensor_001", "unit": "C", "channel": 0},
         {"unique_id": "test_sensor_001", "unit": "percent", "channel": 1}
       ],
       "past_seconds": 3600
     }'
   ```

3. **Expected Result**:
   - HTTP 200 status code
   - JSON response with both measurements
   - Each measurement should have: unique_id, unit, channel, time, and value

### Test Scenario 2: Invalid Input Validation

**Goal**: Verify proper error handling for invalid inputs

1. **Test Empty Channels List**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [],
       "past_seconds": 3600
     }'
   ```
   - Expected: HTTP 422 with error message about empty channels

2. **Test Missing Required Field**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "test_sensor_001", "channel": 0}
       ],
       "past_seconds": 3600
     }'
   ```
   - Expected: HTTP 422 with error about missing unit

3. **Test Invalid Unit**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "test_sensor_001", "unit": "invalid_unit", "channel": 0}
       ],
       "past_seconds": 3600
     }'
   ```
   - Expected: HTTP 422 with error about unit not found

4. **Test Negative Channel**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "test_sensor_001", "unit": "C", "channel": -1}
       ],
       "past_seconds": 3600
     }'
   ```
   - Expected: HTTP 422 with error about channel must be >= 0

### Test Scenario 3: Real Sensor Data

**Goal**: Test with actual multi-channel sensor like BME680

1. **Configure BME680 sensor** in Mycodo (if available)

2. **Query All Channels**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "YOUR_BME680_ID", "unit": "C", "channel": 0, "measure": "temperature"},
         {"unique_id": "YOUR_BME680_ID", "unit": "percent", "channel": 1, "measure": "humidity"},
         {"unique_id": "YOUR_BME680_ID", "unit": "hPa", "channel": 2, "measure": "pressure"},
         {"unique_id": "YOUR_BME680_ID", "unit": "kOhm", "channel": 3, "measure": "resistance"}
       ],
       "past_seconds": 3600
     }'
   ```

3. **Expected Result**:
   - All four measurements returned
   - Values should be realistic for sensor type
   - Timestamps should be recent (within past_seconds)

### Test Scenario 4: Missing Data Handling

**Goal**: Verify graceful handling when data is not available

1. **Query Non-Existent Sensor**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "non_existent_sensor", "unit": "C", "channel": 0}
       ],
       "past_seconds": 3600
     }'
   ```

2. **Expected Result**:
   - HTTP 200 status (not an error)
   - Response includes the channel specification
   - `time` and `value` fields are `null`

### Test Scenario 5: Performance Test

**Goal**: Verify performance improvement over multiple single requests

1. **Time Single Requests** (baseline):
   ```bash
   time for i in 0 1 2 3; do
     curl -s "https://localhost/api/measurements/last/YOUR_SENSOR_ID/UNIT/$i/3600" \
       -H "Authorization: Bearer YOUR_API_KEY"
   done
   ```

2. **Time Multi-Channel Request**:
   ```bash
   time curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "YOUR_SENSOR_ID", "unit": "UNIT", "channel": 0},
         {"unique_id": "YOUR_SENSOR_ID", "unit": "UNIT", "channel": 1},
         {"unique_id": "YOUR_SENSOR_ID", "unit": "UNIT", "channel": 2},
         {"unique_id": "YOUR_SENSOR_ID", "unit": "UNIT", "channel": 3}
       ],
       "past_seconds": 3600
     }'
   ```

3. **Expected Result**:
   - Multi-channel request should be significantly faster
   - Especially noticeable with network latency

### Test Scenario 6: Mixed Sensors

**Goal**: Verify querying channels from different sensors

1. **Query Multiple Sensors**:
   ```bash
   curl -X POST "https://localhost/api/measurements/multi" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "channels": [
         {"unique_id": "sensor_001", "unit": "C", "channel": 0},
         {"unique_id": "sensor_002", "unit": "percent", "channel": 0},
         {"unique_id": "sensor_003", "unit": "lux", "channel": 0}
       ],
       "past_seconds": 3600
     }'
   ```

2. **Expected Result**:
   - All sensors queried successfully
   - Each returns its own data independently

## Verification Checklist

- [ ] Endpoint is accessible at `/api/measurements/multi`
- [ ] Authentication is required
- [ ] Permission check works (view_settings)
- [ ] Valid requests return HTTP 200
- [ ] Response format matches documentation
- [ ] Empty channels list returns HTTP 422
- [ ] Missing required fields return HTTP 422
- [ ] Invalid units return HTTP 422
- [ ] Negative channel numbers return HTTP 422
- [ ] Missing data returns null values (not error)
- [ ] Multiple channels work correctly
- [ ] Mixed sensors work correctly
- [ ] Performance is better than individual requests
- [ ] Error messages are clear and helpful

## Common Issues

### Issue: 403 Forbidden
- **Cause**: User lacks view_settings permission
- **Solution**: Grant appropriate permissions or use admin account

### Issue: 422 "Unit ID not found"
- **Cause**: Invalid unit string
- **Solution**: Check available units in Mycodo configuration

### Issue: All values are null
- **Cause**: No data in specified time range
- **Solution**: Increase past_seconds or verify sensor is recording data

### Issue: Connection refused
- **Cause**: Mycodo not running or wrong URL
- **Solution**: Verify Mycodo service is running
