// Variable-sized payload decoder for The Things Network
//
// Example of a decoder that receives a variable-sized payload
// The first byte of the payload determines the size to be decoded
//
// If the first byte represents the character 'B', then the payload is 7 bytes
// Each byte pair following the first byte represents a float value for
// humidity, pressure, and temperature, respectively.
// Dew point and vapor pressure deficit are calculated form these values to
// reduce the payload needing to be sent.
//
// If the first byte represents the character 'K', then the payload is 3 bytes.
// The pair of bytes following the first byte represents CO2
//
// All original measurement values are converted to a high and low byte for the payload.
// See https://github.com/kizniche/ttgo-tbeam-sensor-node-bme280/blob/master/main/bme280.ino
// for an example of how humidity, pressure, and temperature are encoded into the payload.

function Decoder(bytes, port) {
    // Decode an uplink message from a buffer
    // (array) of bytes to an object of fields.
    var decoded = {};

    // First byte determines the payload
    // Payload is based on which sensor conducted the measurements
    // Each sensor is on a different measurement period
    if (String.fromCharCode(bytes[0]) === 'B') {
        // Humidity
        var rawHum = bytes[1] + bytes[2] * 256;
        decoded.humidity = sflt162f(rawHum) * 100;
        // Pressure
        var rawPress = bytes[3] + bytes[4] * 256;
        decoded.pressure = sflt162f(rawPress) * 100000;
        // Temperature
        var rawTemp = bytes[5] + bytes[6] * 256;
        decoded.temperature = sflt162f(rawTemp) * 100;
        // Dew point
        decoded.dewpoint = calculateDP(decoded.temperature, decoded.humidity);
        // Vapor Pressure Deficit
        decoded.vpd = calculateVPD(decoded.temperature, decoded.humidity);
    } else if (String.fromCharCode(bytes[0]) === 'K') {
        // CO2
        var rawCO2 = bytes[1] + bytes[2] * 256;
        decoded.co2 = sflt162f(rawCO2) * 10000;
    }

    return decoded;
}

function calculateVPD(temperature, relative_humidity) {
    // Calculates Vapor Pressure Deficit
    var saturated_vapor_pressure = 610.7 * Math.pow(10, (7.5 * temperature / (237.3 + temperature)));
    return ((100 - relative_humidity) / 100) * saturated_vapor_pressure;
}

function calculateDP(temperature, humidity) {
    // Calculates Dew point
    if (temperature === null || humidity === null) {
        return;
    }
    var tem2 = temperature;
    var r = humidity;
    var tem = -1.0 * tem2;
    var es = 6.112 * Math.exp(-1.0 * 17.67 * tem / (243.5 - tem));
    var ed = r/100.0 * es;
    var eln = Math.log(ed / 6.112);

    return -243.5 * eln / (eln - 17.67);
}

function sflt162f(rawSflt16) {
    // rawSflt16 is the 2-byte number decoded from wherever;
    // it's in range 0..0xFFFF
    // bit 15 is the sign bit
    // bits 14..11 are the exponent
    // bits 10..0 are the the mantissa. Unlike IEEE format,
    // 	the msb is transmitted; this means that numbers
    //	might not be normalized, but makes coding for
    //	underflow easier.
    // As with IEEE format, negative zero is possible, so
    // we special-case that in hopes that JavaScript will
    // also cooperate.
    //
    // The result is a number in the open interval (-1.0, 1.0);
    //

    // throw away high bits for repeatability.
    rawSflt16 &= 0xFFFF;

    // special case minus zero:
    if (rawSflt16 === 0x8000)
        return -0.0;

    // extract the sign.
    var sSign = ((rawSflt16 & 0x8000) !== 0) ? -1 : 1;

    // extract the exponent
    var exp1 = (rawSflt16 >> 11) & 0xF;

    // extract the "mantissa" (the fractional part)
    var mant1 = (rawSflt16 & 0x7FF) / 2048.0;

    // convert back to a floating point number. We hope
    // that Math.pow(2, k) is handled efficiently by
    // the JS interpreter! If this is time critical code,
    // you can replace by a suitable shift and divide.
    return sSign * mant1 * Math.pow(2, exp1 - 15);
}
