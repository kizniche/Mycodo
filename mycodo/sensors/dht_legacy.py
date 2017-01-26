# coding=utf-8
# This module isn't currently used but still remains for reference
import time
import Adafruit_DHT
from sensorutils import dewpoint


class DHT(object):
    def __init__(self, device, pin):
        self._temperature = None
        self._humidity = None
        self.device = device
        self.pin = pin
        self.running = True

    def read(self, rereads=2):
        humidity = []
        temperature = []
        for _ in range(rereads):
            if not self.running:
                break
            time.sleep(2)
            hum, temp = self.read_retry(self.device, self.pin)
            humidity.append(hum)
            temperature.append(temp)
        if (None in temperature or
                None in humidity or
                max(temperature)-min(temperature) > 5 or
                max(humidity)-min(humidity) > 10):
            self._temperature = self._humidity = None
        else:
            self._temperature = sum(temperature, 0.0) / len(temperature)
            self._humidity = sum(humidity, 0.0) / len(humidity)

    def read_retry(self, sensor, pin, retries=25, delay_seconds=2):
        for _ in range(retries):
            if not self.running:
                break
            humidity, temperature = Adafruit_DHT.read(sensor, pin)
            if ((humidity is not None and temperature is not None) and
                    (humidity < 100)):
                return humidity, temperature
            time.sleep(delay_seconds)
        return None, None

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return temperature and humidity information.
        """
        self.read()
        if self.temperature is None or self.humidity is None:
            return None
        response = {
            'humidity': float("{0:.2f}".format(self.humidity)),
            'temperature': float("{0:.2f}".format(self.temperature)),
            'dewpoint': float("{0:.2f}".format(dewpoint(self.temperature, self.humidity)))
        }
        return response

    def stop_sensor(self):
        self.running = False


if __name__ == "__main__":
    dht = DHT(Adafruit_DHT.DHT22, 17)  # Change 17 to your GPIO for testing
    time_diff = time.time()
    time_success = time.time()
    count = 0
    total_diff = 0
    none_count = 0
    max_diff = 0
    for measurements in dht:
        if measurements is not None:
            count += 1
            diff = time.time()-time_diff
            diff_success = time.time()-time_success
            total_diff += diff
            if diff > max_diff:
                max_diff = diff
            print("Temperature: {temp}".format(temp=measurements['temperature']))
            print("Humidity: {hum}".format(hum=measurements['humidity']))
            print("Dew Point: {dp}".format(dp=dewpoint(measurements['temperature'], measurements['humidity'])))
            print("No Resp. = {cnt}, Avg Read Time: {avg_read:.2f}, "
                  "Max Read Time: {max_read:.2f}, Read Time: {read:.2f}, "
                  "Time Success: {success:.2f}".format(cnt=none_count,
                                                       avg_read=total_diff/count,
                                                       max_read=max_diff,
                                                       read=diff,
                                                       success=diff_success))
            time_diff = time.time()
            time_success = time.time()
        else:
            none_count += 1
            time_diff = time.time()
