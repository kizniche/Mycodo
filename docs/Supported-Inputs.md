Supported Inputs are listed below.

## Built-In Inputs (System)

### Linux: Bash Command

- Measurements: Return Value

This Input will execute a command in the shell and store the output as a float value. Perform any unit conversions within your script or command. A measurement/unit is required to be selected.

### Linux: Python 3 Code

- Measurements: Store Value(s)

All channels require a Measurement Unit to be selected and saved in order to store values to the database.

### Mycodo: MQTT Subscribe (paho)

- Measurements: Variable measurements
- Libraries: paho-mqtt
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)

Be sure you select and save the Measurement Unit for each of the values you are receiving from a subscribed topic. Once the unit has been saved, you can convert to other units in the Convert Measurement section.

### Mycodo: Mycodo RAM

- Measurements: Size RAM in Use
- Libraries: resource.getrusage()

### Mycodo: Mycodo Version

- Measurements: Version as Major.Minor.Revision

### Mycodo: TTN Integration: Data Storage

- Measurements: Variable measurements
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)

This Input receives and stores measurements from the Data Storage Integration on The Things Network.

### Raspberry Pi: CPU/GPU Temperature

- Measurements: Temperature

The internal CPU and GPU temperature of the Raspberry Pi.

### Raspberry Pi: Edge Detection

- Measurements: Rising/Falling Edge
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

### Raspberry Pi: GPIO State

- Measurements: GPIO State
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

### Raspberry Pi: Signal (PWM)

- Measurements: Frequency/Pulse Width/Duty Cycle
- Libraries: pigpio
- Dependencies: pigpio

### Raspberry Pi: Signal (Revolutions)

- Measurements: RPM
- Libraries: pigpio
- Dependencies: pigpio

### System: CPU Load

- Measurements: CPULoad
- Libraries: os.getloadavg()

### System: Free Space

- Measurements: Unallocated Disk Space
- Libraries: os.statvfs()

### System: Server Ping

- Measurements: Boolean
- Libraries: ping

This Input executes the bash command "ping -c [times] -w [deadline] [host]" to determine if the host can be pinged.

### System: Server Port Open

- Measurements: Boolean
- Libraries: nc

This Input executes the bash command "nc -zv [host] [port]" to determine if the host at a particular port is accessible.

## Built-In Inputs (Devices)

### AMS: AS7262

- Measurements: Light at 450, 500, 550, 570, 600, 650 nm
- Libraries: as7262
- Dependencies: [as7262](https://pypi.org/project/as7262)
- Manufacturer URL: [Link](https://ams.com/as7262)
- Datasheet URL: [Link](https://ams.com/documents/20143/36005/AS7262_DS000486_2-00.pdf/0031f605-5629-e030-73b2-f365fd36a43b)
- Product URL: [Link](https://www.sparkfun.com/products/14347)

### AMS: CCS811

- Measurements: CO2/VOC/Temperature
- Libraries: Adafruit_CCS811
- Dependencies: [Adafruit_CCS811](https://pypi.org/project/Adafruit_CCS811), [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO)
- Manufacturer URL: [Link](https://www.sciosense.com/products/environmental-sensors/ccs811-gas-sensor-solution/)
- Datasheet URL: [Link](https://www.sciosense.com/wp-content/uploads/2020/01/CCS811-Datasheet.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3566), [Link 2](https://www.sparkfun.com/products/14193)

### AMS: TSL2561

- Measurements: Light
- Libraries: tsl2561
- Dependencies: [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO), [Adafruit_PureIO](https://pypi.org/project/Adafruit_PureIO), [tsl2561](https://pypi.org/project/tsl2561)
- Manufacturer URL: [Link](https://ams.com/tsl2561)
- Datasheet URL: [Link](https://ams.com/documents/20143/36005/TSL2561_DS000110_3-00.pdf/18a41097-2035-4333-c70e-bfa544c0a98b)
- Product URL: [Link](https://www.adafruit.com/product/439)

### AMS: TSL2591

- Measurements: Light
- Libraries: maxlklaxl/python-tsl2591
- Dependencies: [tsl2591](https://github.com/maxlklaxl/python-tsl2591)
- Manufacturer URL: [Link](https://ams.com/tsl25911)
- Datasheet URL: [Link](https://ams.com/documents/20143/36005/TSL2591_DS000338_6-00.pdf/090eb50d-bb18-5b45-4938-9b3672f86b80)
- Product URL: [Link](https://www.adafruit.com/product/1980)

### AOSONG: AM2315/AM2320

- Measurements: Humidity/Temperature
- Libraries: quick2wire-api
- Dependencies: [quick2wire-api](https://pypi.org/project/quick2wire-api)
- Datasheet URL: [Link](https://cdn-shop.adafruit.com/datasheets/AM2315.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1293)

### AOSONG: DHT11

- Measurements: Humidity/Temperature
- Libraries: pigpio
- Dependencies: pigpio
- Datasheet URL: [Link](http://www.adafruit.com/datasheets/DHT11-chinese.pdf)
- Product URL: [Link](https://www.adafruit.com/product/386)

### AOSONG: DHT22

- Measurements: Humidity/Temperature
- Libraries: pigpio
- Dependencies: pigpio
- Datasheet URL: [Link](http://www.adafruit.com/datasheets/DHT22.pdf)
- Product URL: [Link](https://www.adafruit.com/product/385)

### ASAIR: AHTx0

- Measurements: Temperature/Humidity
- Libraries: Adafruit-CircuitPython-AHTx0
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [Adafruit_CircuitPython_AHTx0](https://pypi.org/project/Adafruit_CircuitPython_AHTx0)
- Manufacturer URL: [Link](http://www.aosong.com/en/products-40.html)
- Datasheet URL: [Link](https://server4.eca.ir/eshop/AHT10/Aosong_AHT10_en_draft_0c.pdf)

### Analog Devices: ADT7410

- Measurements: Temperature
- Libraries: Adafruit_CircuitPython
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [Adafruit_CircuitPython_ADT7410](https://pypi.org/project/Adafruit_CircuitPython_ADT7410)
- Datasheet URL: [Link](https://www.analog.com/media/en/technical-documentation/data-sheets/ADT7410.pdf)
- Product URL: [Link](https://www.analog.com/en/products/adt7410.html)

### Analog Devices: ADXL34x (343, 344, 345, 346)

- Measurements: Acceleration
- Libraries: Adafruit_CircuitPython
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [Adafruit_CircuitPython_ADXL34x](https://pypi.org/project/Adafruit_CircuitPython_ADXL34x)
- Datasheet URLs: [Link 1](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL343.pdf), [Link 2](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL344.pdf), [Link 3](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL345.pdf), [Link 4](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL346.pdf)
- Product URLs: [Link 1](https://www.analog.com/en/products/adxl343.html), [Link 2](https://www.analog.com/en/products/adxl344.html), [Link 3](https://www.analog.com/en/products/adxl345.html), [Link 4](https://www.analog.com/en/products/adxl346.html)

### AnyLeaf: AnyLeaf ORP

- Measurements: Oxidation Reduction Potential
- Libraries: anyleaf
- Dependencies: [python3-numpy](https://packages.debian.org/buster/python3-numpy), [python3-scipy](https://packages.debian.org/buster/python3-scipy), [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [anyleaf](https://pypi.org/project/anyleaf)
- Manufacturer URL: [Link](https://anyleaf.org/ph-module)
- Datasheet URL: [Link](https://anyleaf.org/static/ph-module-datasheet.pdf)

### AnyLeaf: AnyLeaf pH

- Measurements: Ion concentration
- Libraries: anyleaf
- Dependencies: [python3-numpy](https://packages.debian.org/buster/python3-numpy), [python3-scipy](https://packages.debian.org/buster/python3-scipy), [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [anyleaf](https://pypi.org/project/anyleaf)
- Manufacturer URL: [Link](https://anyleaf.org/ph-module)
- Datasheet URL: [Link](https://anyleaf.org/static/ph-module-datasheet.pdf)

### Atlas Scientific: Atlas CO2

- Measurements: CO2
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://atlas-scientific.com/co2/)
- Datasheet URL: [Link](https://atlas-scientific.com/files/EZO_CO2_Datasheet.pdf)

### Atlas Scientific: Atlas Color

- Measurements: RGB, CIE, LUX, Proximity
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/ezo-rgb/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO_RGB_Datasheet.pdf)

### Atlas Scientific: Atlas DO

- Measurements: Dissolved Oxygen
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/dissolved-oxygen.html)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/DO_EZO_Datasheet.pdf)

### Atlas Scientific: Atlas EC

- Measurements: Electrical Conductivity
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/conductivity/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EC_EZO_Datasheet.pdf)

### Atlas Scientific: Atlas Flow Meter

- Measurements: Total Volume, Flow Rate
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/flow/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/flow_EZO_Datasheet.pdf)

Set the Measurement Time Base to a value most appropriate for your anticipated flow (it will affect accuracy). This flow rate time base that is set and returned from the sensor will be converted to liters per minute, which is the default unit for this input module. If you desire a different rate to be stored in the database (such as liters per second or hour), then use the Convert to Unit option.

### Atlas Scientific: Atlas ORP

- Measurements: Oxidation Reduction Potential
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/orp/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/ORP_EZO_Datasheet.pdf)

### Atlas Scientific: Atlas PT-1000

- Measurements: Temperature
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/temperature/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO_RTD_Datasheet.pdf)

### Atlas Scientific: Atlas Pressure

- Measurements: Pressure
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/pressure/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO-PRS-Datasheet.pdf)

### Atlas Scientific: Atlas pH

- Measurements: Ion Concentration
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/ph/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/pH_EZO_Datasheet.pdf)

Calibration Measurement is an optional setting that provides a temperature measurement (in Celsius) of the water that the pH is being measured from.

### BOSCH: BME280

- Measurements: Pressure/Humidity/Temperature
- Libraries: Adafruit_BME280
- Dependencies: [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO), [Adafruit_BME280](https://github.com/adafruit/Adafruit_Python_BME280)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/bst/products/all_products/bme280)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/2652), [Link 2](https://www.sparkfun.com/products/13676)

### BOSCH: BME280

- Measurements: Pressure/Humidity/Temperature
- Libraries: RPi.bme280
- Dependencies: [RPi.bme280](https://pypi.org/project/RPi.bme280)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/bst/products/all_products/bme280)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/2652), [Link 2](https://www.sparkfun.com/products/13676)

### BOSCH: BME680

- Measurements: Temperature/Humidity/Pressure/Gas
- Libraries: Adafruit_CircuitPython_BME680
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [Adafruit_CircuitPython_BME680](https://pypi.org/project/Adafruit_CircuitPython_BME680)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3660), [Link 2](https://www.sparkfun.com/products/16466)

### BOSCH: BME680

- Measurements: Temperature/Humidity/Pressure/Gas
- Libraries: bme680
- Dependencies: [bme680](https://pypi.org/project/bme680), [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3660), [Link 2](https://www.sparkfun.com/products/16466)

### BOSCH: BMP180

- Measurements: Pressure/Temperature
- Libraries: Adafruit_BMP
- Dependencies: [Adafruit_BMP](https://pypi.org/project/Adafruit_BMP), [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO)
- Datasheet URL: [Link](https://ae-bst.resource.bosch.com/media/_tech/media/product_flyer/BST-BMP180-FL000.pdf)

### BOSCH: BMP280

- Measurements: Pressure/Temperature
- Libraries: Adafruit_GPIO
- Dependencies: [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/pressure-sensors-bmp280-1.html)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf)
- Product URL: [Link](https://www.adafruit.com/product/2651)

### BOSCH: BMP280

- Measurements: Pressure/Temperature
- Libraries: bmp280-python
- Dependencies: [smbus2](https://pypi.org/project/smbus2), [bmp280](https://pypi.org/project/bmp280)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/pressure-sensors-bmp280-1.html)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf)
- Product URL: [Link](https://www.adafruit.com/product/2651)

This is similar to the other BMP280 Input, except it uses a different library, whcih includes the ability to set forced mode.

### CO2Meter: K30

- Measurements: CO2
- Libraries: serial
- Manufacturer URL: [Link](https://www.co2meter.com/products/k-30-co2-sensor-module)
- Datasheet URL: [Link](http://co2meters.com/Documentation/Datasheets/DS_SE_0118_CM_0024_Revised9%20(1).pdf)

### Catnip Electronics: Chirp

- Measurements: Light/Moisture/Temperature
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://wemakethings.net/chirp/)
- Product URL: [Link](https://www.tindie.com/products/miceuz/chirp-plant-watering-alarm/)

### Cozir: Cozir CO2

- Measurements: CO2/Humidity/Temperature
- Libraries: pierre-haessig/pycozir
- Dependencies: [cozir](https://github.com/pierre-haessig/pycozir)
- Manufacturer URL: [Link](https://www.co2meter.com/products/cozir-2000-ppm-co2-sensor)
- Datasheet URL: [Link](https://cdn.shopify.com/s/files/1/0019/5952/files/Datasheet_COZIR_A_CO2Meter_4_15.pdf)

### Generic: Hall Flow Meter

- Measurements: Flow Rate, Total Volume
- Libraries: pigpio
- Dependencies: pigpio

### Grove Pi: DHT11/DHT22

- Measurements: Humidity/Temperature
- Libraries: grovepi
- Dependencies: [grovepi](https://pypi.org/project/grovepi)
- Manufacturer URLs: [Link 1](https://wiki.seeedstudio.com/Grove-Temperature_and_Humidity_Sensor_Pro/), [Link 2](https://wiki.seeedstudio.com/Grove-TemperatureAndHumidity_Sensor/)

Enter the Grove Pi+ GPIO pin connected to the sensor and select the sensor type.

### MAXIM: DS1822

- Measurements: Temperature
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS1822.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS1822.pdf)

### MAXIM: DS1825

- Measurements: Temperature
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS1825.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS1825.pdf)

### MAXIM: DS18B20

- Measurements: Temperature
- Libraries: ow-shell
- Dependencies: [ow-shell](https://packages.debian.org/buster/ow-shell)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS18B20.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/374), [Link 2](https://www.adafruit.com/product/381), [Link 3](https://www.sparkfun.com/products/245)
- Additional URL: [Link](https://github.com/cpetrich/counterfeit_DS18B20)

Warning: Counterfeit DS18B20 sensors are common and can cause a host of issues. Review the Additional URL for more information about how to determine if your sensor is authentic.

### MAXIM: DS18B20

- Measurements: Temperature
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS18B20.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/374), [Link 2](https://www.adafruit.com/product/381), [Link 3](https://www.sparkfun.com/products/245)
- Additional URL: [Link](https://github.com/cpetrich/counterfeit_DS18B20)

Warning: Counterfeit DS18B20 sensors are common and can cause a host of issues. Review the Additional URL for more information about how to determine if your sensor is authentic.

### MAXIM: DS18S20

- Measurements: Temperature
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS18S20.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS18S20.pdf)

### MAXIM: DS28EA00

- Measurements: Temperature
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/DS28EA00.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS28EA00.pdf)

### MAXIM: MAX31850K

- Measurements: Temperature
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/MAX31850EVKIT.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31850-MAX31851.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1727)

### MAXIM: MAX31855

- Measurements: Temperature (Object/Die)
- Libraries: Adafruit_MAX31855
- Dependencies: [Adafruit_MAX31855](https://github.com/adafruit/Adafruit_Python_MAX31855), [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31855.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31855.pdf)
- Product URL: [Link](https://www.adafruit.com/product/269)

### MAXIM: MAX31856

- Measurements: Temperature (Object/Die)
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/MAX31856.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31856.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3263)

### MAXIM: MAX31865

- Measurements: Temperature
- Libraries: Adafruit-CircuitPython-MAX31865
- Dependencies: [adafruit-circuitpython-max31865](https://pypi.org/project/adafruit-circuitpython-max31865)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31865.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3328)

This module was added to allow support for multiple sensors to be connected at the same time, which the original MAX31865 module was not designed for.

### MAXIM: MAX31865

- Measurements: Temperature
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31865.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3328)

Note: This module does not allow for multiple sensors to be connected at the same time. For multi-sensor support, use the MAX31865 CircuitPython Input.

### Melexis: MLX90614

- Measurements: Temperature (Ambient/Object)
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.melexis.com/en/product/MLX90614/Digital-Plug-Play-Infrared-Thermometer-TO-Can)
- Datasheet URL: [Link](https://www.melexis.com/-/media/files/documents/datasheets/mlx90614-datasheet-melexis.pdf)
- Product URL: [Link](https://www.sparkfun.com/products/9570)

### Microchip: MCP3008

- Measurements: Voltage (Analog-to-Digital Converter)
- Libraries: Adafruit_MCP3008
- Dependencies: [Adafruit_MCP3008](https://pypi.org/project/Adafruit_MCP3008)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/en010530)
- Datasheet URL: [Link](http://ww1.microchip.com/downloads/en/DeviceDoc/21295d.pdf)
- Product URL: [Link](https://www.adafruit.com/product/856)

### Microchip: MCP342x (x=2,3,4,6,7,8)

- Measurements: Voltage (Analog-to-Digital Converter)
- Libraries: MCP342x
- Dependencies: [smbus2](https://pypi.org/project/smbus2), [MCP342x](https://pypi.org/project/MCP342x)
- Manufacturer URLs: [Link 1](https://www.microchip.com/wwwproducts/en/MCP3422), [Link 2](https://www.microchip.com/wwwproducts/en/MCP3423), [Link 3](https://www.microchip.com/wwwproducts/en/MCP3424), [Link 4](https://www.microchip.com/wwwproducts/en/MCP3426https://www.microchip.com/wwwproducts/en/MCP3427), [Link 5](https://www.microchip.com/wwwproducts/en/MCP3428)
- Datasheet URLs: [Link 1](http://ww1.microchip.com/downloads/en/DeviceDoc/22088c.pdf), [Link 2](http://ww1.microchip.com/downloads/en/DeviceDoc/22226a.pdf)

### Microchip: MCP9808

- Measurements: Temperature
- Libraries: Adafruit_MCP9808
- Dependencies: [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO), [Adafruit_MCP9808](https://github.com/adafruit/Adafruit_Python_MCP9808)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/en556182)
- Datasheet URL: [Link](http://ww1.microchip.com/downloads/en/DeviceDoc/MCP9808-0.5C-Maximum-Accuracy-Digital-Temperature-Sensor-Data-Sheet-DS20005095B.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1782)

### Multiple Manufacturers: HCSR04

- Measurements: Ultrasonic Distance
- Libraries: Adafruit-CircuitPython-HCSR04
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [adafruit-circuitpython-hcsr04](https://pypi.org/project/adafruit-circuitpython-hcsr04)
- Manufacturer URL: [Link](https://www.cytron.io/p-5v-hc-sr04-ultrasonic-sensor)
- Datasheet URL: [Link](http://web.eece.maine.edu/~zhu/book/lab/HC-SR04%20User%20Manual.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3942)
- Additional URL: [Link](https://learn.adafruit.com/ultrasonic-sonar-distance-sensors/python-circuitpython)

### Panasonic: AMG8833

- Measurements: 8x8 Temperature Grid
- Libraries: Adafruit_AMG88xx/Pillow/colour
- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [zlib1g-dev](https://packages.debian.org/buster/zlib1g-dev), [colour](https://pypi.org/project/colour), [Pillow](https://pypi.org/project/Pillow), [Adafruit_AMG88xx](https://github.com/adafruit/Adafruit_AMG88xx_python)

### ROHM: BH1750

- Measurements: Light
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Datasheet URL: [Link](http://rohmfs.rohm.com/en/products/databook/datasheet/ic/sensor/light/bh1721fvc-e.pdf)
- Product URL: [Link](https://www.dfrobot.com/product-531.html)

### Raspberry Pi Foundation: Sense HAT

- Measurements: hum/temp/press/compass/magnet/accel/gyro
- Libraries: sense-hat
- Dependencies: [sense-hat](https://packages.debian.org/buster/sense-hat)
- Manufacturer URL: [Link](https://www.raspberrypi.org/products/sense-hat/)

This module acquires measurements from the Raspberry Pi Sense HAT sensors, which include the LPS25H, LSM9DS1, and HTS221.

### Ruuvi: RuuviTag

- Measurements: Acceleration/Humidity/Pressure/Temperature
- Libraries: ruuvitag_sensor
- Dependencies: [python3-dev](https://packages.debian.org/buster/python3-dev), [python3-psutil](https://packages.debian.org/buster/python3-psutil), [bluez](https://packages.debian.org/buster/bluez), [bluez-hcidump](https://packages.debian.org/buster/bluez-hcidump), [ruuvitag_sensor](https://pypi.org/project/ruuvitag_sensor)
- Manufacturer URL: [Link](https://ruuvi.com/)
- Datasheet URL: [Link](https://ruuvi.com/files/ruuvitag-tech-spec-2019-7.pdf)

### STMicroelectronics: VL53L0X

- Measurements: Millimeter (Time-of-Flight Distance)
- Libraries: VL53L0X_rasp_python
- Dependencies: [VL53L0X](https://github.com/grantramsay/VL53L0X_rasp_python)
- Manufacturer URL: [Link](https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html)
- Datasheet URL: [Link](https://www.st.com/resource/en/datasheet/vl53l0x.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3317), [Link 2](https://www.pololu.com/product/2490)

### STMicroelectronics: VL53L1X

- Measurements: Millimeter (Time-of-Flight Distance)
- Libraries: VL53L1X
- Dependencies: [smbus2](https://pypi.org/project/smbus2), [vl53l1x](https://pypi.org/project/vl53l1x)
- Manufacturer URL: [Link](https://www.st.com/en/imaging-and-photonics-solutions/vl53l1x.html)
- Datasheet URL: [Link](https://www.st.com/resource/en/datasheet/vl53l1x.pdf)
- Product URLs: [Link 1](https://www.pololu.com/product/3415), [Link 2](https://www.sparkfun.com/products/14722)

Notes when setting a custom timing budget: A higher timing budget results in greater measurement accuracy, but also a higher power consumption. The inter measurement period must be >= the timing budget, otherwise it will be double the expected value.

### Sensirion: SCD30

- Measurements: CO2/Humidity/Temperature
- Libraries: Adafruit-CircuitPython-SCD30
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [adafruit-circuitPython-scd30](https://pypi.org/project/adafruit-circuitPython-scd30)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensors-co2/)
- Datasheet URL: [Link](https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/9.5_CO2/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf)
- Product URLs: [Link 1](https://www.sparkfun.com/products/15112), [Link 2](https://www.futureelectronics.com/p/4115766)

### Sensirion: SCD30

- Measurements: CO2/Humidity/Temperature
- Libraries: scd30_i2c
- Dependencies: [scd30_i2c](https://pypi.org/project/scd30_i2c)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensors-co2/)
- Datasheet URL: [Link](https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/9.5_CO2/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf)
- Product URLs: [Link 1](https://www.sparkfun.com/products/15112), [Link 2](https://www.futureelectronics.com/p/4115766)

### Sensirion: SHT1x/7x

- Measurements: Humidity/Temperature
- Libraries: sht_sensor
- Dependencies: [sht_sensor](https://pypi.org/project/sht_sensor)
- Manufacturer URLs: [Link 1](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-accurate-measurements/), [Link 2](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/pintype-digital-humidity-sensors/)

### Sensirion: SHT2x

- Measurements: Humidity/Temperature
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/)

### Sensirion: SHT3x (30, 31, 35)

- Measurements: Humidity/Temperature
- Libraries: Adafruit_SHT31
- Dependencies: [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO), [Adafruit_SHT31](https://pypi.org/project/Adafruit_SHT31)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-various-applications/)

### Sensorion: SHT31 Smart Gadget

- Measurements: Humidity/Temperature
- Libraries: bluepy
- Dependencies: [pi-bluetooth](https://packages.debian.org/buster/pi-bluetooth), [libglib2.0-dev](https://packages.debian.org/buster/libglib2.0-dev), [bluepy](https://pypi.org/project/bluepy)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/development-kit/)

### Sonoff: TH16/10 (Tasmota firmware) with AM2301

- Measurements: Humidity/Temperature
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)
- Manufacturer URL: [Link](https://sonoff.tech/product/wifi-diy-smart-switches/th10-th16)

### Sonoff: TH16/10 (Tasmota firmware) with DS18B20

- Measurements: Temperature
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)
- Manufacturer URL: [Link](https://sonoff.tech/product/wifi-diy-smart-switches/th10-th16)

### TE Connectivity: HTU21D

- Measurements: Humidity/Temperature
- Libraries: pigpio
- Dependencies: pigpio
- Manufacturer URL: [Link](https://www.te.com/usa-en/product-CAT-HSC0004.html)
- Datasheet URL: [Link](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FHPC199_6%7FA6%7Fpdf%7FEnglish%7FENG_DS_HPC199_6_A6.pdf%7FCAT-HSC0004)
- Product URL: [Link](https://www.adafruit.com/product/1899)

### Texas Instruments: ADS1015

- Measurements: Voltage (Analog-to-Digital Converter)
- Libraries: Adafruit_CircuitPython
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [Adafruit_CircuitPython_ADS1x15](https://pypi.org/project/Adafruit_CircuitPython_ADS1x15)

### Texas Instruments: ADS1115

- Measurements: Voltage (Analog-to-Digital Converter)
- Libraries: Adafruit_CircuitPython_ADS1x15
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [Adafruit_CircuitPython_ADS1x15](https://pypi.org/project/Adafruit_CircuitPython_ADS1x15)

### Texas Instruments: ADS1256

- Measurements: Voltage (Waveshare, Analog-to-Digital Converter)
- Libraries: wiringpi, kizniche/PiPyADC-py3
- Dependencies: [wiringpi](https://pypi.org/project/wiringpi), [pipyadc_py3](https://github.com/kizniche/PiPyADC-py3)

### Texas Instruments: ADS1x15

- Measurements: Voltage (Analog-to-Digital Converter)
- Libraries: Adafruit_ADS1x15 [DEPRECATED]
- Dependencies: [Adafruit_GPIO](https://pypi.org/project/Adafruit_GPIO), [Adafruit_ADS1x15](https://pypi.org/project/Adafruit_ADS1x15)

The Adafruit_ADS1x15 is deprecated. It's advised to use The Circuit Python ADS1x15 Input.

### Texas Instruments: HDC1000

- Measurements: Humidity/Temperature
- Libraries: fcntl/io
- Manufacturer URL: [Link](https://www.ti.com/product/HDC1000)
- Datasheet URL: [Link](https://www.ti.com/lit/ds/symlink/hdc1000.pdf)

### Texas Instruments: INA219x

- Measurements: Electrical Current (DC)
- Libraries: Adafruit_CircuitPython
- Dependencies: [adafruit-circuitpython-ina219](https://pypi.org/project/adafruit-circuitpython-ina219)
- Manufacturer URL: [Link](https://www.ti.com/product/INA219)
- Datasheet URL: [Link](https://www.ti.com/lit/gpn/ina219)

### Texas Instruments: TMP006

- Measurements: Temperature (Object/Die)
- Libraries: Adafruit_TMP
- Dependencies: [Adafruit_TMP](https://pypi.org/project/Adafruit_TMP)
- Datasheet URL: [Link](http://www.adafruit.com/datasheets/tmp006.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1296)

### Weather: OpenWeatherMap (City, Current)

- Measurements: Humidity/Temperature/Pressure/Wind
- Additional URL: [Link](openweathermap.org)

Obtain a free API key at openweathermap.org. If the city you enter does not return measurements, try another city. Note: the free API subscription is limited to 60 calls per minute

### Weather: OpenWeatherMap (Lat/Lon, Current/Future)

- Measurements: Humidity/Temperature/Pressure/Wind
- Additional URL: [Link](openweathermap.org)

Obtain a free API key at openweathermap.org. Notes: The free API subscription is limited to 60 calls per minute. If a Day (Future) time is selected, Minimum and Maximum temperatures are available as measurements.

### Winsen: MH-Z16

- Measurements: CO2
- Libraries: smbus2/serial
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.winsen-sensor.com/sensors/co2-sensor/mh-z16.html)
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/MH-Z16.pdf)

### Winsen: MH-Z19

- Measurements: CO2
- Libraries: serial
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/PDF/Infrared%20Gas%20Sensor/NDIR%20CO2%20SENSOR/MH-Z19%20CO2%20Ver1.0.pdf)

This is the version of the sensor that does not include the ability to conduct automatic baseline correction (ABC). See the B version of the sensor if you wish to use ABC.

### Winsen: MH-Z19B

- Measurements: CO2
- Libraries: serial
- Manufacturer URL: [Link](https://www.winsen-sensor.com/sensors/co2-sensor/mh-z19b.html)
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/MH-Z19B.pdf)

This is the B version of the sensor that includes the ability to conduct automatic baseline correction (ABC).

### Winsen: ZH03B

- Measurements: Particulates
- Libraries: serial
- Manufacturer URL: [Link](https://www.winsen-sensor.com/sensors/dust-sensor/zh3b.html)
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/ZH03B.pdf)

### Xiaomi: Miflora

- Measurements: EC/Light/Moisture/Temperature
- Libraries: miflora
- Dependencies: [libglib2.0-dev](https://packages.debian.org/buster/libglib2.0-dev), [miflora](https://pypi.org/project/miflora), [bluepy](https://pypi.org/project/bluepy)

### Xiaomi: Mijia LYWSD03MMC (ATC and non-ATC modes)

- Measurements: Battery/Humidity/Temperature
- Libraries: bluepy/bluez
- Dependencies: [bluez](https://packages.debian.org/buster/bluez), [bluetooth](https://packages.debian.org/buster/bluetooth), [libbluetooth-dev](https://packages.debian.org/buster/libbluetooth-dev), [bluepy](https://pypi.org/project/bluepy), [pybluez](https://pypi.org/project/pybluez)

More information about ATC mode can be found at https://github.com/JsBergbau/MiTemperature2

