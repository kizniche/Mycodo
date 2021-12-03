Supported Inputs are listed below.

## Built-In Inputs (System)

### Linux: Bash Command

- Manufacturer: Linux
- Measurements: Return Value
- Interfaces: Mycodo

This Input will execute a command in the shell and store the output as a float value. Perform any unit conversions within your script or command. A measurement/unit is required to be selected.

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Command Timeout

- Type: Integer
- Default Value: 60
- Description: How long to wait for the command to finish before killing the process.

##### User

- Type: Text
- Default Value: mycodo
- Description: The user to execute the command

##### Current Working Directory

- Type: Text
- Default Value: /home/pi
- Description: The current working directory of the shell environment.

### Linux: Python 3 Code

- Manufacturer: Linux
- Measurements: Store Value(s)
- Interfaces: Mycodo

All channels require a Measurement Unit to be selected and saved in order to store values to the database.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Mycodo: MQTT Subscribe (JSON payload)

- Manufacturer: Mycodo
- Measurements: Variable measurements
- Interfaces: Mycodo
- Libraries: paho-mqtt, jmespath
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt), [jmespath](https://pypi.org/project/jmespath)

A single topic is subscribed to and the returned JSON payload contains one or more key/value pairs. The given JSON Key is used as a JMESPATH expression to find the corresponding value that will be stored for that channel. Be sure you select and save the Measurement Unit for each channel. Once the unit has been saved, you can convert to other units in the Convert Measurement section. Example expressions for jmespath (https://jmespath.org) include <i>temperature</i>, <i>sensors[0].temperature</i>, and <i>bathroom.temperature</i> which refer to the temperature as a direct key within the first entry of sensors or as a subkey of bathroom, respectively. Jmespath elements and keys that contain special characters have to be enclosed in double quotes, e.g. <i>"sensor-1".temperature</i>.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Host

- Type: Text
- Default Value: localhost
- Description: Host address or IP

##### Port

- Type: Integer
- Default Value: 1883
- Description: Host port number

##### Topic

- Type: Text
- Default Value: mqtt/test/input
- Description: The topic to subscribe to

##### Keep Alive

- Type: Integer
- Default Value: 60
- Description: Maximum amount of time between received signals. Set to 0 to disable.

##### Client ID

- Type: Text
- Default Value: mycodo_mqtt_client
- Description: Unique client ID for connecting to the server

##### Use Login

- Type: Boolean
- Description: Send login credentials

##### Use TLS

- Type: Boolean
- Description: Send login credentials using TLS

##### Username

- Type: Text
- Default Value: user
- Description: Username for connecting to the server

##### Password

- Type: Text
- Description: Password for connecting to the server. Leave blank to disable.

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### JSON Key

- Type: Text
- Description: JMES Path expression to find value in JSON response

### Mycodo: MQTT Subscribe (Value payload)

- Manufacturer: Mycodo
- Measurements: Variable measurements
- Interfaces: Mycodo
- Libraries: paho-mqtt
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)

A topic is subscribed to for each channel Subscription Topic and the returned payload value will be stored for that channel. Be sure you select and save the Measurement Unit for each of the channels. Once the unit has been saved, you can convert to other units in the Convert Measurement section.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Host

- Type: Text
- Default Value: localhost
- Description: Host address or IP

##### Port

- Type: Integer
- Default Value: 1883
- Description: Host port number

##### Keep Alive

- Type: Integer
- Default Value: 60
- Description: Maximum amount of time between received signals. Set to 0 to disable.

##### Client ID

- Type: Text
- Default Value: mycodo_mqtt_client
- Description: Unique client ID for connecting to the server

##### Use Login

- Type: Boolean
- Description: Send login credentials

##### Use TLS

- Type: Boolean
- Description: Send login credentials using TLS

##### Username

- Type: Text
- Default Value: user
- Description: Username for connecting to the server

##### Password

- Type: Text
- Description: Password for connecting to the server. Leave blank to disable.

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Subscription Topic

- Type: Text
- Description: The MQTT topic to subscribe to

### Mycodo: Mycodo RAM

- Manufacturer: Mycodo
- Measurements: Size RAM in Use
- Interfaces: Mycodo
- Libraries: resource.getrusage()

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

### Mycodo: Mycodo Version

- Manufacturer: Mycodo
- Measurements: Version as Major.Minor.Revision
- Interfaces: Mycodo

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

### Mycodo: Spacer

- Manufacturer: Mycodo
- Interfaces: Mycodo

A spacer to organize Inputs.

#### Options

##### Color

- Type: Text
- Default Value: #000000
- Description: The color of the name text

### Mycodo: TTN Integration: Data Storage (TTN v2)

- Manufacturer: Mycodo
- Measurements: Variable measurements
- Interfaces: Mycodo
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)

This Input receives and stores measurements from the Data Storage Integration on The Things Network.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Start Offset (seconds)

- Type: Integer
- Description: The duration (seconds) to wait before the first operation

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Application ID

- Type: Text
- Description: The Things Network Application ID

##### App API Key

- Type: Text
- Description: The Things Network Application API Key

##### Device ID

- Type: Text
- Description: The Things Network Device ID

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Variable Name

- Type: Text
- Description: The TTN variable name

### Mycodo: TTN Integration: Data Storage (TTN v3)

- Manufacturer: Mycodo
- Measurements: Variable measurements
- Interfaces: Mycodo
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)

This Input receives and stores measurements from the Data Storage Integration on The Things Network.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Start Offset (seconds)

- Type: Integer
- Description: The duration (seconds) to wait before the first operation

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Application ID

- Type: Text
- Description: The Things Network Application ID

##### App API Key

- Type: Text
- Description: The Things Network Application API Key

##### Device ID

- Type: Text
- Description: The Things Network Device ID

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Variable Name

- Type: Text
- Description: The TTN variable name

### Raspberry Pi: CPU/GPU Temperature

- Manufacturer: Raspberry Pi
- Measurements: Temperature
- Interfaces: RPi

The internal CPU and GPU temperature of the Raspberry Pi.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

### Raspberry Pi: Edge Detection

- Manufacturer: Raspberry Pi
- Measurements: Rising/Falling Edge
- Interfaces: GPIO
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

#### Options

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Pin Mode

- Type: Select
- Options: \[**Floating** | Pull Down | Pull Up\] (Default in **bold**)
- Description: Enables or disables the pull-up or pull-down resistor

### Raspberry Pi: GPIO State

- Manufacturer: Raspberry Pi
- Measurements: GPIO State
- Interfaces: GPIO
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Pin Mode

- Type: Select
- Options: \[**Floating** | Pull Down | Pull Up\] (Default in **bold**)
- Description: Enables or disables the pull-up or pull-down resistor

### Raspberry Pi: Signal (PWM)

- Manufacturer: Raspberry Pi
- Measurements: Frequency/Pulse Width/Duty Cycle
- Interfaces: GPIO
- Libraries: pigpio
- Dependencies: pigpio

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Raspberry Pi: Signal (Revolutions)

- Manufacturer: Raspberry Pi
- Measurements: RPM
- Interfaces: GPIO
- Libraries: pigpio
- Dependencies: pigpio

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### System: CPU Load

- Manufacturer: System
- Measurements: CPULoad
- Interfaces: Mycodo
- Libraries: os.getloadavg()

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

### System: Free Space

- Manufacturer: System
- Measurements: Unallocated Disk Space
- Interfaces: Mycodo
- Libraries: os.statvfs()

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

### System: Server Ping

- Manufacturer: System
- Measurements: Boolean
- Interfaces: Mycodo
- Libraries: ping

This Input executes the bash command "ping -c [times] -w [deadline] [host]" to determine if the host can be pinged.

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### System: Server Port Open

- Manufacturer: System
- Measurements: Boolean
- Interfaces: Mycodo
- Libraries: nc

This Input executes the bash command "nc -zv [host] [port]" to determine if the host at a particular port is accessible.

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

## Built-In Inputs (Devices)

### AMS: AS7262

- Manufacturer: AMS
- Measurements: Light at 450, 500, 550, 570, 600, 650 nm
- Interfaces: I<sup>2</sup>C
- Libraries: as7262
- Dependencies: [as7262](https://pypi.org/project/as7262)
- Manufacturer URL: [Link](https://ams.com/as7262)
- Datasheet URL: [Link](https://ams.com/documents/20143/36005/AS7262_DS000486_2-00.pdf/0031f605-5629-e030-73b2-f365fd36a43b)
- Product URL: [Link](https://www.sparkfun.com/products/14347)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Gain

- Type: Select
- Options: \[1x | 3.7x | 16x | **64x**\] (Default in **bold**)
- Description: Set the sensor gain

##### Illumination LED Current

- Type: Select
- Options: \[**12.5 mA** | 25 mA | 50 mA | 100 mA\] (Default in **bold**)
- Description: Set the illumination LED current (milliamps)

##### Illumination LED Mode

- Type: Select
- Options: \[**On** | Off\] (Default in **bold**)
- Description: Turn the illumination LED on or off during a measurement

##### Indicator LED Current

- Type: Select
- Options: \[**1 mA** | 2 mA | 4 mA | 8 mA\] (Default in **bold**)
- Description: Set the indicator LED current (milliamps)

##### Indicator LED Mode

- Type: Select
- Options: \[**On** | Off\] (Default in **bold**)
- Description: Turn the indicator LED on or off during a measurement

##### Integration Time

- Type: Decimal
- Default Value: 15.0
- Description: The integration time (0 - ~91 ms)

### AMS: CCS811 (with Temperature)

- Manufacturer: AMS
- Measurements: CO2/VOC/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CCS811
- Dependencies: [Adafruit_CCS811](https://pypi.org/project/Adafruit_CCS811), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO)
- Manufacturer URL: [Link](https://www.sciosense.com/products/environmental-sensors/ccs811-gas-sensor-solution/)
- Datasheet URL: [Link](https://www.sciosense.com/wp-content/uploads/2020/01/CCS811-Datasheet.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3566), [Link 2](https://www.sparkfun.com/products/14193)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### AMS: CCS811 (without Temperature)

- Manufacturer: AMS
- Measurements: CO2/VOC
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_CCS811
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-ccs811](https://pypi.org/project/adafruit-circuitpython-ccs811)
- Manufacturer URL: [Link](https://www.sciosense.com/products/environmental-sensors/ccs811-gas-sensor-solution/)
- Datasheet URL: [Link](https://www.sciosense.com/wp-content/uploads/2020/01/CCS811-Datasheet.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3566)
- Additional URL: [Link](https://learn.adafruit.com/adafruit-ccs811-air-quality-sensor)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### AMS: TSL2561

- Manufacturer: AMS
- Measurements: Light
- Interfaces: I<sup>2</sup>C
- Libraries: tsl2561
- Dependencies: [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit-PureIO](https://pypi.org/project/Adafruit-PureIO), [tsl2561](https://pypi.org/project/tsl2561)
- Manufacturer URL: [Link](https://ams.com/tsl2561)
- Datasheet URL: [Link](https://ams.com/documents/20143/36005/TSL2561_DS000110_3-00.pdf/18a41097-2035-4333-c70e-bfa544c0a98b)
- Product URL: [Link](https://www.adafruit.com/product/439)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### AMS: TSL2591

- Manufacturer: AMS
- Measurements: Light
- Interfaces: I<sup>2</sup>C
- Libraries: maxlklaxl/python-tsl2591
- Dependencies: [tsl2591](https://github.com/maxlklaxl/python-tsl2591)
- Manufacturer URL: [Link](https://ams.com/tsl25911)
- Datasheet URL: [Link](https://ams.com/documents/20143/36005/TSL2591_DS000338_6-00.pdf/090eb50d-bb18-5b45-4938-9b3672f86b80)
- Product URL: [Link](https://www.adafruit.com/product/1980)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### AOSONG: AM2315/AM2320

- Manufacturer: AOSONG
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: quick2wire-api
- Dependencies: [quick2wire-api](https://pypi.org/project/quick2wire-api)
- Datasheet URL: [Link](https://cdn-shop.adafruit.com/datasheets/AM2315.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1293)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### AOSONG: DHT11

- Manufacturer: AOSONG
- Measurements: Humidity/Temperature
- Interfaces: GPIO
- Libraries: pigpio
- Dependencies: pigpio
- Datasheet URL: [Link](http://www.adafruit.com/datasheets/DHT11-chinese.pdf)
- Product URL: [Link](https://www.adafruit.com/product/386)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### AOSONG: DHT22

- Manufacturer: AOSONG
- Measurements: Humidity/Temperature
- Interfaces: GPIO
- Libraries: pigpio
- Dependencies: pigpio
- Datasheet URL: [Link](http://www.adafruit.com/datasheets/DHT22.pdf)
- Product URL: [Link](https://www.adafruit.com/product/385)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### ASAIR: AHTx0

- Manufacturer: ASAIR
- Measurements: Temperature/Humidity
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit-CircuitPython-AHTx0
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-ahtx0](https://pypi.org/project/adafruit-circuitpython-ahtx0)
- Manufacturer URL: [Link](http://www.aosong.com/en/products-40.html)
- Datasheet URL: [Link](https://server4.eca.ir/eshop/AHT10/Aosong_AHT10_en_draft_0c.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Adafruit: I2C Capacitive Moisture Sensor

- Manufacturer: Adafruit
- Measurements: Moisture/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: adafruit_seesaw
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-seesaw](https://pypi.org/project/adafruit-circuitpython-seesaw)
- Manufacturer URL: [Link](https://learn.adafruit.com/adafruit-stemma-soil-sensor-i2c-capacitive-moisture-sensor)
- Product URL: [Link](https://www.adafruit.com/product/4026)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Analog Devices: ADT7410

- Manufacturer: Analog Devices
- Measurements: Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-adt7410](https://pypi.org/project/adafruit-circuitpython-adt7410)
- Datasheet URL: [Link](https://www.analog.com/media/en/technical-documentation/data-sheets/ADT7410.pdf)
- Product URL: [Link](https://www.analog.com/en/products/adt7410.html)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Analog Devices: ADXL34x (343, 344, 345, 346)

- Manufacturer: Analog Devices
- Measurements: Acceleration
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-adxl34x](https://pypi.org/project/adafruit-circuitpython-adxl34x)
- Datasheet URLs: [Link 1](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL343.pdf), [Link 2](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL344.pdf), [Link 3](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL345.pdf), [Link 4](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL346.pdf)
- Product URLs: [Link 1](https://www.analog.com/en/products/adxl343.html), [Link 2](https://www.analog.com/en/products/adxl344.html), [Link 3](https://www.analog.com/en/products/adxl345.html), [Link 4](https://www.analog.com/en/products/adxl346.html)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Range

- Type: Select
- Options: \[±2 g (±19.6 m/s/s) | ±4 g (±39.2 m/s/s) | ±8 g (±78.4 m/s/s) | **±16 g (±156.9 m/s/s)**\] (Default in **bold**)
- Description: Set the measurement range

### AnyLeaf: AnyLeaf EC

- Manufacturer: AnyLeaf
- Measurements: Electrical Conductivity
- Interfaces: UART
- Libraries: anyleaf
- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [zlib1g-dev](https://packages.debian.org/buster/zlib1g-dev), [Pillow](https://pypi.org/project/Pillow), [python3-scipy](https://packages.debian.org/buster/python3-scipy), [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [anyleaf](https://pypi.org/project/anyleaf)
- Manufacturer URL: [Link](https://www.anyleaf.org/ec-module)
- Datasheet URL: [Link](https://www.anyleaf.org/static/ec-module-datasheet.pdf)

#### Options

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Conductivity Constant

- Type: Decimal
- Default Value: 1.0
- Description: Conductivity constant K

### AnyLeaf: AnyLeaf ORP

- Manufacturer: AnyLeaf
- Measurements: Oxidation Reduction Potential
- Interfaces: I<sup>2</sup>C
- Libraries: anyleaf
- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [zlib1g-dev](https://packages.debian.org/buster/zlib1g-dev), [Pillow](https://pypi.org/project/Pillow), [python3-scipy](https://packages.debian.org/buster/python3-scipy), [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [anyleaf](https://pypi.org/project/anyleaf)
- Manufacturer URL: [Link](https://anyleaf.org/ph-module)
- Datasheet URL: [Link](https://anyleaf.org/static/ph-module-datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Calibrate: Voltage (Internal)

- Type: Decimal
- Default Value: 0.4
- Description: Calibration data: internal voltage

##### Calibrate: ORP (Internal)

- Type: Decimal
- Default Value: 400.0
- Description: Calibration data: internal ORP

#### Actions

##### Calibrate: Buffer ORP (mV)

- Type: Decimal
- Default Value: 400.0
- Description: This is the nominal ORP of the calibration buffer in mV, usually labelled on the bottle.

##### Calibrate

- Type: Button
##### Clear Calibration Slots

- Type: Button
### AnyLeaf: AnyLeaf pH

- Manufacturer: AnyLeaf
- Measurements: Ion concentration
- Interfaces: I<sup>2</sup>C
- Libraries: anyleaf
- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [zlib1g-dev](https://packages.debian.org/buster/zlib1g-dev), [Pillow](https://pypi.org/project/Pillow), [python3-scipy](https://packages.debian.org/buster/python3-scipy), [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [anyleaf](https://pypi.org/project/anyleaf)
- Manufacturer URL: [Link](https://anyleaf.org/ph-module)
- Datasheet URL: [Link](https://anyleaf.org/static/ph-module-datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Temperature Compensation: Measurement

- Type: Select Measurement
- Selections: Input, Function, Math, 
- Description: Select a measurement for temperature compensation

##### Temperature Compensation: Max Age

- Type: Integer
- Default Value: 120
- Description: The maximum age (seconds) of the measurement to use

##### Cal data: V1 (internal)

- Type: Decimal
- Description: Calibration data: Voltage

##### Cal data: pH1 (internal)

- Type: Decimal
- Default Value: 7.0
- Description: Calibration data: pH

##### Cal data: T1 (internal)

- Type: Decimal
- Default Value: 23.0
- Description: Calibration data: Temperature

##### Cal data: V2 (internal)

- Type: Decimal
- Default Value: 0.17
- Description: Calibration data: Voltage

##### Cal data: pH2 (internal)

- Type: Decimal
- Default Value: 4.0
- Description: Calibration data: pH

##### Cal data: T2 (internal)

- Type: Decimal
- Default Value: 23.0
- Description: Calibration data: Temperature

##### Cal data: V3 (internal)

- Type: Decimal
- Description: Calibration data: Voltage

##### Cal data: pH3 (internal)

- Type: Decimal
- Description: Calibration data: pH

##### Cal data: T3 (internal)

- Type: Decimal
- Description: Calibration data: Temperature

#### Actions

##### Calibration buffer pH

- Type: Decimal
- Default Value: 7.0
- Description: This is the nominal pH of the calibration buffer, usually labelled on the bottle.

##### Calibrate, slot 1

- Type: Button
##### Calibrate, slot 2

- Type: Button
##### Calibrate, slot 3

- Type: Button
##### Clear Calibration Slots

- Type: Button
### Atlas Scientific: Atlas CO2

- Manufacturer: Atlas Scientific
- Measurements: CO2
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://atlas-scientific.com/co2/)
- Datasheet URL: [Link](https://atlas-scientific.com/files/EZO_CO2_Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### New I2C Address

- Type: Text
- Default Value: 0x69
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas Color

- Manufacturer: Atlas Scientific
- Measurements: RGB, CIE, LUX, Proximity
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/ezo-rgb/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO_RGB_Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### LED Only For Measure

- Type: Boolean
- Default Value: True
- Description: Turn the LED on only during the measurement

##### LED Percentage

- Type: Integer
- Default Value: 30
- Description: What percentage of power to supply to the LEDs during measurement

##### Gamma Correction

- Type: Decimal
- Default Value: 1.0
- Description: Gamma correction between 0.01 and 4.99 (default is 1.0)

#### Actions

##### The EZO-RGB color sensor is designed to be calibrated to a white object at the maximum brightness the object will be viewed under. In order to get the best results, Atlas Scientific strongly recommends that the sensor is mounted into a fixed location. Holding the sensor in your hand during calibration will decrease performance.<br>1. Embed the EZO-RGB color sensor into its intended use location.<br>2. Set LED brightness to the desired level.<br>3. Place a white object in front of the target object and press the Calibration button.<br>4. A single color reading will be taken and the device will be fully calibrated.

##### Calibrate

- Type: Button
##### The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.

##### New I2C Address

- Type: Text
- Default Value: 0x70
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas DO

- Manufacturer: Atlas Scientific
- Measurements: Dissolved Oxygen
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/dissolved-oxygen.html)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/DO_EZO_Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Temperature Compensation: Measurement

- Type: Select Measurement
- Selections: Input, Function, Math, 
- Description: Select a measurement for temperature compensation

##### Temperature Compensation: Max Age

- Type: Integer
- Default Value: 120
- Description: The maximum age (seconds) of the measurement to use

#### Actions

##### A one- or two-point calibration can be performed. After exposing the probe to air for 30 seconds until readings stabilize, press Calibrate (Air). If you require accuracy below 1.0 mg/L, you can place the probe in a 0 mg/L solution for 30 to 90 seconds until readings stabilize, then press Calibrate (0 mg/L). You can also clear the currently-saved calibration by pressing Clear Calibration.

##### Calibrate (Air)

- Type: Button
##### Calibrate (0 mg/L)

- Type: Button
##### Clear Calibration

- Type: Button
##### The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.

##### New I2C Address

- Type: Text
- Default Value: 0x66
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas EC

- Manufacturer: Atlas Scientific
- Measurements: Electrical Conductivity
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/conductivity/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EC_EZO_Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Temperature Compensation: Measurement

- Type: Select Measurement
- Selections: Input, Function, Math, 
- Description: Select a measurement for temperature compensation

##### Temperature Compensation: Max Age

- Type: Integer
- Default Value: 120
- Description: The maximum age (seconds) of the measurement to use

#### Actions

##### Calibration: a one- or two-point calibration can be performed. It's a good idea to clear the calibration before calibrating. Always perform a dry calibration with the probe in the air (not in any fluid). Then perform either a one- or two-point calibration with calibrated solutions. If performing a one-point calibration, use the Single Point Calibration field and button. If performing a two-point calibration, use the Low and High Point Calibration fields and buttons. Allow a minute or two after submerging your probe in a calibration solution for the measurements to equilibrate before calibrating to that solution. The EZO EC circuit default temperature compensation is set to 25 °C. If the temperature of the calibration solution is +/- 2 °C from 25 °C, consider setting the temperature compensation first. Note that at no point should you change the temperature compensation value during calibration. Therefore, if you have previously enabled temperature compensation, allow at least one measurement to occur (to set the compensation value), then disable the temperature compensation measurement while you calibrate.

##### Clear Calibration

- Type: Button
##### Calibrate Dry

- Type: Button
##### Single Point EC (µS)

- Type: Integer
- Default Value: 84
- Description: The EC (µS) of the single point calibration solution

##### Calibrate Single Point

- Type: Button
##### Low Point EC (µS)

- Type: Integer
- Default Value: 12880
- Description: The EC (µS) of the low point calibration solution

##### Calibrate Low Point

- Type: Button
##### High Point EC (µS)

- Type: Integer
- Default Value: 80000
- Description: The EC (µS) of the high point calibration solution

##### Calibrate High Point

- Type: Button
##### The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.

##### New I2C Address

- Type: Text
- Default Value: 0x64
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas Flow Meter

- Manufacturer: Atlas Scientific
- Measurements: Total Volume, Flow Rate
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/flow/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/flow_EZO_Datasheet.pdf)

Set the Measurement Time Base to a value most appropriate for your anticipated flow (it will affect accuracy). This flow rate time base that is set and returned from the sensor will be converted to liters per minute, which is the default unit for this input module. If you desire a different rate to be stored in the database (such as liters per second or hour), then use the Convert to Unit option.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Flow Meter Type

- Type: Select
- Options: \[**Atlas Scientific 3/8" Flow Meter** | Atlas Scientific 1/4" Flow Meter | Atlas Scientific 1/2" Flow Meter | Atlas Scientific 3/4" Flow Meter | Non-Atlas Scientific Flow Meter\] (Default in **bold**)
- Description: Set the type of flow meter used

##### Atlas Meter Time Base

- Type: Select
- Options: \[Liters per Second | **Liters per Minute** | Liters per Hour\] (Default in **bold**)
- Description: If using an Atlas Scientific flow meter, set the flow rate/time base

##### Internal Resistor

- Type: Select
- Options: \[**Use Atlas Scientific Flow Meter** | Disable Internal Resistor | 1 K Ω Pull-Up | 1 K Ω Pull-Down | 10 K Ω Pull-Up | 10 K Ω Pull-Down | 100 K Ω Pull-Up | 100 K Ω Pull-Down\] (Default in **bold**)
- Description: Set an internal resistor for the flow meter

##### Custom K Value(s)

- Type: Text
- Description: If using a non-Atlas Scientific flow meter, enter the meter's K value(s). For a single K value, enter '[volume per pulse],[number of pulses]'. For multiple K values (up to 16), enter '[volume at frequency],[frequency in Hz];[volume at frequency],[frequency in Hz];...'. Leave blank to disable.

##### K Value Time Base

- Type: Select
- Options: \[**Use Atlas Scientific Flow Meter** | Liters per Second | Liters per Minute | Liters per Hour\] (Default in **bold**)
- Description: If using a non-Atlas Scientific flow meter, set the flow rate/time base for the custom K values entered.

#### Actions

##### The total volume can be cleared with the following button or with a Function Action.

##### Clear Total Volume

- Type: Button
##### The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.

##### New I2C Address

- Type: Text
- Default Value: 0x68
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas Humidity

- Manufacturer: Atlas Scientific
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://atlas-scientific.com/probes/humidity-sensor/)
- Datasheet URL: [Link](https://atlas-scientific.com/files/EZO-HUM-Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### LED Mode

- Type: Select
- Options: \[**Always On** | Always Off | Only On During Measure\] (Default in **bold**)
- Description: When to turn the LED on

#### Actions

##### New I2C Address

- Type: Text
- Default Value: 0x6f
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas ORP

- Manufacturer: Atlas Scientific
- Measurements: Oxidation Reduction Potential
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/orp/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/ORP_EZO_Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Temperature Compensation: Measurement

- Type: Select Measurement
- Selections: Input, Function, Math, 
- Description: Select a measurement for temperature compensation

##### Temperature Compensation: Max Age

- Type: Integer
- Default Value: 120
- Description: The maximum age (seconds) of the measurement to use

#### Actions

##### A one-point calibration can be performed. Enter the solution's mV, set the probe in the solution, then press Calibrate. You can also clear the currently-saved calibration by pressing Clear Calibration.

##### Calibration Solution mV

- Type: Integer
- Default Value: 225
- Description: The value of the calibration solution, in mV

##### Calibrate

- Type: Button
##### Clear Calibration

- Type: Button
##### The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.

##### New I2C Address

- Type: Text
- Default Value: 0x62
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas PT-1000

- Manufacturer: Atlas Scientific
- Measurements: Temperature
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/temperature/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO_RTD_Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### New I2C Address

- Type: Text
- Default Value: 0x66
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas Pressure

- Manufacturer: Atlas Scientific
- Measurements: Pressure
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/pressure/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO-PRS-Datasheet.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### LED Mode

- Type: Select
- Options: \[**Always On** | Always Off | Only On During Measure\] (Default in **bold**)
- Description: When to turn the LED on

#### Actions

##### New I2C Address

- Type: Text
- Default Value: 0x6a
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Atlas Scientific: Atlas pH

- Manufacturer: Atlas Scientific
- Measurements: Ion Concentration
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Libraries: pylibftdi/fcntl/io/serial
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://www.atlas-scientific.com/ph/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/pH_EZO_Datasheet.pdf)

Calibration Measurement is an optional setting that provides a temperature measurement (in Celsius) of the water that the pH is being measured from.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### FTDI Device

- Type: Text
- Description: The FTDI device connected to the input/output/etc.

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Temperature Compensation: Measurement

- Type: Select Measurement
- Selections: Input, Function, Math, 
- Description: Select a measurement for temperature compensation

##### Temperature Compensation: Max Age

- Type: Integer
- Default Value: 120
- Description: The maximum age (seconds) of the measurement to use

#### Actions

##### Calibration: a one-, two- or three-point calibration can be performed. It's a good idea to clear the calibration before calibrating. The first calibration must be the Mid point. The second must be the Low point. And the third must be the High point. You can perform a one-, two- or three-point calibration, but they must be performed in this order. Allow a minute or two after submerging your probe in a calibration solution for the measurements to equilibrate before calibrating to that solution. The EZO pH circuit default temperature compensation is set to 25 °C. If the temperature of the calibration solution is +/- 2 °C from 25 °C, consider setting the temperature compensation first. Note that if you have a Temperature Compensation Measurement selected from the Options, this will overwrite the manual Temperature Compensation set here, so be sure to disable this option if you would like to specify the temperature to compensate with.

##### Compensation Temperature (°C)

- Type: Decimal
- Default Value: 25.0
- Description: The temperature of the calibration solutions

##### Set Temperature Compensation

- Type: Button
##### Clear Calibration

- Type: Button
##### Mid Point pH

- Type: Decimal
- Default Value: 7.0
- Description: The pH of the mid point calibration solution

##### Calibrate Mid

- Type: Button
##### Low Point pH

- Type: Decimal
- Default Value: 4.0
- Description: The pH of the low point calibration solution

##### Calibrate Low

- Type: Button
##### High Point pH

- Type: Decimal
- Default Value: 10.0
- Description: The pH of the high point calibration solution

##### Calibrate High

- Type: Button
##### The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.

##### New I2C Address

- Type: Text
- Default Value: 0x63
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### BOSCH: BME280

- Manufacturer: BOSCH
- Measurements: Pressure/Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_BME280
- Dependencies: [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit_BME280](https://github.com/adafruit/Adafruit_Python_BME280)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/bst/products/all_products/bme280)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/2652), [Link 2](https://www.sparkfun.com/products/13676)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### BOSCH: BME280

- Manufacturer: BOSCH
- Measurements: Pressure/Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_BME280
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-bme280](https://pypi.org/project/adafruit-circuitpython-bme280)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/bst/products/all_products/bme280)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/2652), [Link 2](https://www.sparkfun.com/products/13676)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### BOSCH: BME280

- Manufacturer: BOSCH
- Measurements: Pressure/Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: RPi.bme280
- Dependencies: [RPi.bme280](https://pypi.org/project/RPi.bme280)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/bst/products/all_products/bme280)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/2652), [Link 2](https://www.sparkfun.com/products/13676)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### BOSCH: BME680

- Manufacturer: BOSCH
- Measurements: Temperature/Humidity/Pressure/Gas
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_BME680
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-bme680](https://pypi.org/project/adafruit-circuitpython-bme680)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3660), [Link 2](https://www.sparkfun.com/products/16466)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Humidity Oversampling

- Type: Select
- Options: \[NONE | 1X | **2X** | 4X | 8X | 16X\] (Default in **bold**)
- Description: A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.

##### Temperature Oversampling

- Type: Select
- Options: \[NONE | 1X | 2X | 4X | **8X** | 16X\] (Default in **bold**)
- Description: A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.

##### Pressure Oversampling

- Type: Select
- Options: \[NONE | 1X | 2X | **4X** | 8X | 16X\] (Default in **bold**)
- Description: A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.

##### IIR Filter Size

- Type: Select
- Options: \[0 | 1 | **3** | 7 | 15 | 31 | 63 | 127\] (Default in **bold**)
- Description: Optionally remove short term fluctuations from the temperature and pressure readings, increasing their resolution but reducing their bandwidth.

##### Temperature Offset

- Type: Decimal
- Description: The amount to offset the temperature, either negative or positive

##### Sea Level Pressure (ha)

- Type: Decimal
- Default Value: 1013.25
- Description: The pressure at sea level for the sensor location

### BOSCH: BME680

- Manufacturer: BOSCH
- Measurements: Temperature/Humidity/Pressure/Gas
- Interfaces: I<sup>2</sup>C
- Libraries: bme680
- Dependencies: [bme680](https://pypi.org/project/bme680), [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3660), [Link 2](https://www.sparkfun.com/products/16466)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Humidity Oversampling

- Type: Select
- Options: \[NONE | 1X | **2X** | 4X | 8X | 16X\] (Default in **bold**)
- Description: A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.

##### Temperature Oversampling

- Type: Select
- Options: \[NONE | 1X | 2X | 4X | **8X** | 16X\] (Default in **bold**)
- Description: A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.

##### Pressure Oversampling

- Type: Select
- Options: \[NONE | 1X | 2X | **4X** | 8X | 16X\] (Default in **bold**)
- Description: A higher oversampling value means more stable readings with less noise and jitter. However each step of oversampling adds ~2 ms latency, causing a slower response time to fast transients.

##### IIR Filter Size

- Type: Select
- Options: \[0 | 1 | **3** | 7 | 15 | 31 | 63 | 127\] (Default in **bold**)
- Description: Optionally remove short term fluctuations from the temperature and pressure readings, increasing their resolution but reducing their bandwidth.

##### Gas Heater Temperature (°C)

- Type: Integer
- Default Value: 320
- Description: What temperature to set

##### Gas Heater Duration (ms)

- Type: Integer
- Default Value: 150
- Description: How long of a duration to heat. 20-30 ms are necessary for the heater to reach the intended target temperature.

##### Gas Heater Profile

- Type: Select
- Description: Select one of the 10 configured heating durations/set points

##### Temperature Offset

- Type: Decimal
- Description: The amount to offset the temperature, either negative or positive

### BOSCH: BMP180

- Manufacturer: BOSCH
- Measurements: Pressure/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_BMP
- Dependencies: [Adafruit-BMP](https://pypi.org/project/Adafruit-BMP), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO)
- Datasheet URL: [Link](https://ae-bst.resource.bosch.com/media/_tech/media/product_flyer/BST-BMP180-FL000.pdf)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### BOSCH: BMP280

- Manufacturer: BOSCH
- Measurements: Pressure/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_GPIO
- Dependencies: [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/pressure-sensors-bmp280-1.html)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf)
- Product URL: [Link](https://www.adafruit.com/product/2651)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### BOSCH: BMP280

- Manufacturer: BOSCH
- Measurements: Pressure/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: bmp280-python
- Dependencies: [smbus2](https://pypi.org/project/smbus2), [bmp280](https://pypi.org/project/bmp280)
- Manufacturer URL: [Link](https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/pressure-sensors-bmp280-1.html)
- Datasheet URL: [Link](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf)
- Product URL: [Link](https://www.adafruit.com/product/2651)

This is similar to the other BMP280 Input, except it uses a different library, whcih includes the ability to set forced mode.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Enable Forced Mode

- Type: Boolean
- Description: Enable heater to evaporate condensation. Turn on heater x seconds every y measurements.

### CO2Meter: K30

- Manufacturer: CO2Meter
- Measurements: CO2
- Interfaces: UART
- Libraries: serial
- Manufacturer URL: [Link](https://www.co2meter.com/products/k-30-co2-sensor-module)
- Datasheet URL: [Link](http://co2meters.com/Documentation/Datasheets/DS_SE_0118_CM_0024_Revised9%20(1).pdf)

#### Options

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Catnip Electronics: Chirp

- Manufacturer: Catnip Electronics
- Measurements: Light/Moisture/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://wemakethings.net/chirp/)
- Product URL: [Link](https://www.tindie.com/products/miceuz/chirp-plant-watering-alarm/)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Cozir: Cozir CO2

- Manufacturer: Cozir
- Measurements: CO2/Humidity/Temperature
- Interfaces: UART
- Libraries: pierre-haessig/pycozir
- Dependencies: [cozir](https://github.com/pierre-haessig/pycozir)
- Manufacturer URL: [Link](https://www.co2meter.com/products/cozir-2000-ppm-co2-sensor)
- Datasheet URL: [Link](https://cdn.shopify.com/s/files/1/0019/5952/files/Datasheet_COZIR_A_CO2Meter_4_15.pdf)

#### Options

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Generic: Hall Flow Meter

- Manufacturer: Generic
- Measurements: Flow Rate, Total Volume
- Interfaces: GPIO
- Libraries: pigpio
- Dependencies: pigpio

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Pulses per Liter

- Type: Decimal
- Default Value: 1.0
- Description: Enter the conversion factor for this meter (pulses to Liter).

#### Actions

##### Clear Total Volume

- Type: Button
### Infineon: DPS310

- Manufacturer: Infineon
- Measurements: Pressure/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit-CircuitPython-DPS310
- Dependencies: [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-dps310](https://pypi.org/project/adafruit-circuitpython-dps310)
- Manufacturer URL: [Link](https://www.infineon.com/cms/en/product/sensor/pressure-sensors/pressure-sensors-for-iot/dps310/)
- Datasheet URL: [Link](https://www.infineon.com/dgdl/Infineon-DPS310-DataSheet-v01_02-EN.pdf?fileId=5546d462576f34750157750826c42242)
- Product URLs: [Link 1](https://www.adafruit.com/product/4494), [Link 2](https://shop.pimoroni.com/products/adafruit-dps310-precision-barometric-pressure-altitude-sensor-stemma-qt-qwiic), [Link 3](https://www.berrybase.de/sensoren-module/luftdruck-wasserdruck/adafruit-dps310-pr-228-zisions-barometrischer-druck-und-h-246-hen-sensor)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### MAXIM: DS1822

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: 1-Wire
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS1822.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS1822.pdf)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### Set the resolution, precision, and response time for the sensor. This setting will be written to the EEPROM to allow persistence after power loss. The EEPROM has a limited amount of writes (>50k).

##### Resolution

- Type: Select
- Description: Select the resolution for the sensor

##### Set Resolution

- Type: Button
### MAXIM: DS1825

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: 1-Wire
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS1825.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS1825.pdf)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### Set the resolution, precision, and response time for the sensor. This setting will be written to the EEPROM to allow persistence after power loss. The EEPROM has a limited amount of writes (>50k).

##### Resolution

- Type: Select
- Description: Select the resolution for the sensor

##### Set Resolution

- Type: Button
### MAXIM: DS18B20

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: 1-Wire
- Libraries: ow-shell
- Dependencies: [ow-shell](https://packages.debian.org/buster/ow-shell)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS18B20.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/374), [Link 2](https://www.adafruit.com/product/381), [Link 3](https://www.sparkfun.com/products/245)
- Additional URL: [Link](https://github.com/cpetrich/counterfeit_DS18B20)

Warning: Counterfeit DS18B20 sensors are common and can cause a host of issues. Review the Additional URL for more information about how to determine if your sensor is authentic.

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### MAXIM: DS18B20

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: 1-Wire
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS18B20.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/374), [Link 2](https://www.adafruit.com/product/381), [Link 3](https://www.sparkfun.com/products/245)
- Additional URL: [Link](https://github.com/cpetrich/counterfeit_DS18B20)

Warning: Counterfeit DS18B20 sensors are common and can cause a host of issues. Review the Additional URL for more information about how to determine if your sensor is authentic.

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### Set the resolution, precision, and response time for the sensor. This setting will be written to the EEPROM to allow persistence after power loss. The EEPROM has a limited amount of writes (>50k).

##### Resolution

- Type: Select
- Description: Select the resolution for the sensor

##### Set Resolution

- Type: Button
### MAXIM: DS18S20

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: 1-Wire
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/DS18S20.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS18S20.pdf)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### Set the resolution, precision, and response time for the sensor. This setting will be written to the EEPROM to allow persistence after power loss. The EEPROM has a limited amount of writes (>50k).

##### Resolution

- Type: Select
- Description: Select the resolution for the sensor

##### Set Resolution

- Type: Button
### MAXIM: DS28EA00

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: 1-Wire
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/DS28EA00.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS28EA00.pdf)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### Set the resolution, precision, and response time for the sensor. This setting will be written to the EEPROM to allow persistence after power loss. The EEPROM has a limited amount of writes (>50k).

##### Resolution

- Type: Select
- Description: Select the resolution for the sensor

##### Set Resolution

- Type: Button
### MAXIM: MAX31850K

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: 1-Wire
- Libraries: w1thermsensor
- Dependencies: [w1thermsensor](https://pypi.org/project/w1thermsensor)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/MAX31850EVKIT.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31850-MAX31851.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1727)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

#### Actions

##### Set the resolution, precision, and response time for the sensor. This setting will be written to the EEPROM to allow persistence after power loss. The EEPROM has a limited amount of writes (>50k).

##### Resolution

- Type: Select
- Description: Select the resolution for the sensor

##### Set Resolution

- Type: Button
### MAXIM: MAX31855

- Manufacturer: MAXIM
- Measurements: Temperature (Object/Die)
- Interfaces: UART
- Libraries: Adafruit_MAX31855
- Dependencies: [Adafruit_MAX31855](https://github.com/adafruit/Adafruit_Python_MAX31855), [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31855.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31855.pdf)
- Product URL: [Link](https://www.adafruit.com/product/269)

#### Options

##### CS Pin

- Type: Integer
- Description: The GPIO (using BCM numbering) connected to the Cable Select pin

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### MAXIM: MAX31856

- Manufacturer: MAXIM
- Measurements: Temperature (Object/Die)
- Interfaces: UART
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/sensors/MAX31856.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31856.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3263)

#### Options

##### CS Pin

- Type: Integer
- Description: The GPIO (using BCM numbering) connected to the Cable Select pin

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### MAXIM: MAX31865

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: SPI
- Libraries: Adafruit-CircuitPython-MAX31865
- Dependencies: [adafruit-circuitpython-max31865](https://pypi.org/project/adafruit-circuitpython-max31865)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31865.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3328)

This module was added to allow support for multiple sensors to be connected at the same time, which the original MAX31865 module was not designed for.

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Chip Select Pin

- Type: Integer
- Default Value: 8
- Description: Enter the GPIO Chip Select Pin for your device.

##### Number of wires

- Type: Select
- Options: \[**2 Wires** | 3 Wires | 4 Wires\] (Default in **bold**)
- Description: Select the number of wires your thermocouple has.

### MAXIM: MAX31865

- Manufacturer: MAXIM
- Measurements: Temperature
- Interfaces: UART
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/interface/sensor-interface/MAX31865.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3328)

Note: This module does not allow for multiple sensors to be connected at the same time. For multi-sensor support, use the MAX31865 CircuitPython Input.

#### Options

##### CS Pin

- Type: Integer
- Description: The GPIO (using BCM numbering) connected to the Cable Select pin

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Melexis: MLX90393

- Manufacturer: Melexis
- Measurements: Magnetic Flux
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit-CircuitPython-MLX90393
- Dependencies: [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-mlx90393](https://pypi.org/project/adafruit-circuitpython-mlx90393)
- Manufacturer URL: [Link](https://www.melexis.com/en/product/MLX90393/Triaxis-Micropower-Magnetometer)
- Datasheet URL: [Link](https://cdn-learn.adafruit.com/assets/assets/000/069/600/original/MLX90393-Datasheet-Melexis.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/4022), [Link 2](https://shop.pimoroni.com/products/adafruit-wide-range-triple-axis-magnetometer-mlx90393), [Link 3](https://www.berrybase.de/sensoren-module/bewegung-distanz/adafruit-wide-range-drei-achsen-magnetometer-mlx90393)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Melexis: MLX90614

- Manufacturer: Melexis
- Measurements: Temperature (Ambient/Object)
- Interfaces: I<sup>2</sup>C
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.melexis.com/en/product/MLX90614/Digital-Plug-Play-Infrared-Thermometer-TO-Can)
- Datasheet URL: [Link](https://www.melexis.com/-/media/files/documents/datasheets/mlx90614-datasheet-melexis.pdf)
- Product URL: [Link](https://www.sparkfun.com/products/9570)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Microchip: MCP3008

- Manufacturer: Microchip
- Measurements: Voltage (Analog-to-Digital Converter)
- Interfaces: UART
- Libraries: Adafruit_MCP3008
- Dependencies: [Adafruit-MCP3008](https://pypi.org/project/Adafruit-MCP3008)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/en010530)
- Datasheet URL: [Link](http://ww1.microchip.com/downloads/en/DeviceDoc/21295d.pdf)
- Product URL: [Link](https://www.adafruit.com/product/856)

#### Options

##### CS Pin

- Type: Integer
- Description: The GPIO (using BCM numbering) connected to the Cable Select pin

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### VREF (volts)

- Type: Decimal
- Default Value: 3.3
- Description: Set the VREF voltage

### Microchip: MCP342x (x=2,3,4,6,7,8)

- Manufacturer: Microchip
- Measurements: Voltage (Analog-to-Digital Converter)
- Interfaces: I<sup>2</sup>C
- Libraries: MCP342x
- Dependencies: [smbus2](https://pypi.org/project/smbus2), [MCP342x](https://pypi.org/project/MCP342x)
- Manufacturer URLs: [Link 1](https://www.microchip.com/wwwproducts/en/MCP3422), [Link 2](https://www.microchip.com/wwwproducts/en/MCP3423), [Link 3](https://www.microchip.com/wwwproducts/en/MCP3424), [Link 4](https://www.microchip.com/wwwproducts/en/MCP3426https://www.microchip.com/wwwproducts/en/MCP3427), [Link 5](https://www.microchip.com/wwwproducts/en/MCP3428)
- Datasheet URLs: [Link 1](http://ww1.microchip.com/downloads/en/DeviceDoc/22088c.pdf), [Link 2](http://ww1.microchip.com/downloads/en/DeviceDoc/22226a.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Microchip: MCP9808

- Manufacturer: Microchip
- Measurements: Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_MCP9808
- Dependencies: [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit_MCP9808](https://github.com/adafruit/Adafruit_Python_MCP9808)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/en556182)
- Datasheet URL: [Link](http://ww1.microchip.com/downloads/en/DeviceDoc/MCP9808-0.5C-Maximum-Accuracy-Digital-Temperature-Sensor-Data-Sheet-DS20005095B.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1782)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Multiple Manufacturers: HC-SR04

- Manufacturer: Multiple Manufacturers
- Measurements: Ultrasonic Distance
- Interfaces: GPIO
- Libraries: Adafruit-CircuitPython-HCSR04
- Dependencies: [libgpiod-dev](https://packages.debian.org/buster/libgpiod-dev), [pyusb](https://pypi.org/project/pyusb), [adafruit-circuitpython-hcsr04](https://pypi.org/project/adafruit-circuitpython-hcsr04)
- Manufacturer URL: [Link](https://www.cytron.io/p-5v-hc-sr04-ultrasonic-sensor)
- Datasheet URL: [Link](http://web.eece.maine.edu/~zhu/book/lab/HC-SR04%20User%20Manual.pdf)
- Product URL: [Link](https://www.adafruit.com/product/3942)
- Additional URL: [Link](https://learn.adafruit.com/ultrasonic-sonar-distance-sensors/python-circuitpython)

#### Options

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Trigger Pin

- Type: Integer
- Description: Enter the GPIO Trigger Pin for your device (BCM numbering).

##### Echo Pin

- Type: Integer
- Description: Enter the GPIO Echo Pin for your device (BCM numbering).

### Panasonic: AMG8833

- Manufacturer: Panasonic
- Measurements: 8x8 Temperature Grid
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_AMG88xx/Pillow/colour
- Dependencies: [libjpeg-dev](https://packages.debian.org/buster/libjpeg-dev), [zlib1g-dev](https://packages.debian.org/buster/zlib1g-dev), [colour](https://pypi.org/project/colour), [Pillow](https://pypi.org/project/Pillow), [Adafruit_AMG88xx](https://github.com/adafruit/Adafruit_AMG88xx_python)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### ROHM: BH1750

- Manufacturer: ROHM
- Measurements: Light
- Interfaces: I<sup>2</sup>C
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Datasheet URL: [Link](http://rohmfs.rohm.com/en/products/databook/datasheet/ic/sensor/light/bh1721fvc-e.pdf)
- Product URL: [Link](https://www.dfrobot.com/product-531.html)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Raspberry Pi Foundation: Sense HAT

- Manufacturer: Raspberry Pi Foundation
- Measurements: hum/temp/press/compass/magnet/accel/gyro
- Interfaces: I<sup>2</sup>C
- Libraries: sense-hat
- Dependencies: [sense-hat](https://pypi.org/project/sense-hat)
- Manufacturer URL: [Link](https://www.raspberrypi.org/products/sense-hat/)

This module acquires measurements from the Raspberry Pi Sense HAT sensors, which include the LPS25H, LSM9DS1, and HTS221.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Ruuvi: RuuviTag

- Manufacturer: Ruuvi
- Measurements: Acceleration/Humidity/Pressure/Temperature
- Interfaces: BT
- Libraries: ruuvitag_sensor
- Dependencies: [python3-dev](https://packages.debian.org/buster/python3-dev), [python3-psutil](https://packages.debian.org/buster/python3-psutil), [bluez](https://packages.debian.org/buster/bluez), [bluez-hcidump](https://packages.debian.org/buster/bluez-hcidump), [ruuvitag-sensor](https://pypi.org/project/ruuvitag-sensor)
- Manufacturer URL: [Link](https://ruuvi.com/)
- Datasheet URL: [Link](https://ruuvi.com/files/ruuvitag-tech-spec-2019-7.pdf)

#### Options

##### MAC (XX:XX:XX:XX:XX:XX)

- Type: Text
- Description: The MAC address of the Bluetooth device

##### BT Adapter (hci[X])

- Type: Integer
- Description: The adapter of the Bluetooth device

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### STMicroelectronics: VL53L0X

- Manufacturer: STMicroelectronics
- Measurements: Millimeter (Time-of-Flight Distance)
- Interfaces: I<sup>2</sup>C
- Libraries: VL53L0X_rasp_python
- Dependencies: [VL53L0X](https://github.com/grantramsay/VL53L0X_rasp_python)
- Manufacturer URL: [Link](https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html)
- Datasheet URL: [Link](https://www.st.com/resource/en/datasheet/vl53l0x.pdf)
- Product URLs: [Link 1](https://www.adafruit.com/product/3317), [Link 2](https://www.pololu.com/product/2490)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Accuracy

- Type: Select
- Options: \[**Good Accuracy (33 ms, 1.2 m range)** | Better Accuracy (66 ms, 1.2 m range) | Best Accuracy (200 ms, 1.2 m range) | Long Range (33 ms, 2 m) | High Speed, Low Accuracy (20 ms, 1.2 m)\] (Default in **bold**)
- Description: Set the accuracy. A longer measurement duration yields a more accurate measurement

#### Actions

##### New I2C Address

- Type: Text
- Default Value: 0x52
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### STMicroelectronics: VL53L1X

- Manufacturer: STMicroelectronics
- Measurements: Millimeter (Time-of-Flight Distance)
- Interfaces: I<sup>2</sup>C
- Libraries: VL53L1X
- Dependencies: [smbus2](https://pypi.org/project/smbus2), [vl53l1x](https://pypi.org/project/vl53l1x)
- Manufacturer URL: [Link](https://www.st.com/en/imaging-and-photonics-solutions/vl53l1x.html)
- Datasheet URL: [Link](https://www.st.com/resource/en/datasheet/vl53l1x.pdf)
- Product URLs: [Link 1](https://www.pololu.com/product/3415), [Link 2](https://www.sparkfun.com/products/14722)

Notes when setting a custom timing budget: A higher timing budget results in greater measurement accuracy, but also a higher power consumption. The inter measurement period must be >= the timing budget, otherwise it will be double the expected value.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Range

- Type: Select
- Options: \[**Short Range** | Medium Range | Long Range | Custom Timing Budget\] (Default in **bold**)
- Description: Select a range or select to set a custom Timing Budget and Inter Measurement Period.

##### Timing Budget (microseconds)

- Type: Integer
- Default Value: 66000
- Description: Set the timing budget. Must be less than or equal to the Inter Measurement Period.

##### Inter Measurement Period (milliseconds)

- Type: Integer
- Default Value: 70
- Description: Set the Inter Measurement Period

### Seeedstudio: DHT11/22

- Manufacturer: Seeedstudio
- Measurements: Humidity/Temperature
- Interfaces: GROVE
- Libraries: grovepi
- Dependencies: [libatlas-base-dev](https://packages.debian.org/buster/libatlas-base-dev), [grovepi](https://pypi.org/project/grovepi)
- Manufacturer URLs: [Link 1](https://wiki.seeedstudio.com/Grove-Temperature_and_Humidity_Sensor_Pro/), [Link 2](https://wiki.seeedstudio.com/Grove-TemperatureAndHumidity_Sensor/)

Enter the Grove Pi+ GPIO pin connected to the sensor and select the sensor type.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Sensor Type

- Type: Select
- Options: \[**DHT11 (Blue)** | DHT22 (White)\] (Default in **bold**)
- Description: Sensor type

### Sensirion: SCD-4x (SCD-40, SCD-41)

- Manufacturer: Sensirion
- Measurements: CO2/Temperature/Humidity
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit-CircuitPython-SCD4x
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-scd4x](https://pypi.org/project/adafruit-circuitpython-scd4x)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensor-scd4x/)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensirion: SCD30

- Manufacturer: Sensirion
- Measurements: CO2/Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit-CircuitPython-SCD30
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitPython-scd30](https://pypi.org/project/adafruit-circuitPython-scd30)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensors-co2/)
- Datasheet URL: [Link](https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/9.5_CO2/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf)
- Product URLs: [Link 1](https://www.sparkfun.com/products/15112), [Link 2](https://www.futureelectronics.com/p/4115766)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensirion: SCD30

- Manufacturer: Sensirion
- Measurements: CO2/Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: scd30_i2c
- Dependencies: [scd30-i2c](https://pypi.org/project/scd30-i2c)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensors-co2/)
- Datasheet URL: [Link](https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/9.5_CO2/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf)
- Product URLs: [Link 1](https://www.sparkfun.com/products/15112), [Link 2](https://www.futureelectronics.com/p/4115766)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensirion: SHT1x/7x

- Manufacturer: Sensirion
- Measurements: Humidity/Temperature
- Interfaces: GPIO
- Libraries: sht_sensor
- Dependencies: [sht-sensor](https://pypi.org/project/sht-sensor)
- Manufacturer URLs: [Link 1](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-accurate-measurements/), [Link 2](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/pintype-digital-humidity-sensors/)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensirion: SHT2x

- Manufacturer: Sensirion
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: sht20
- Dependencies: [sht20](https://pypi.org/project/sht20)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Temperature Resolution

- Type: Select
- Options: \[11-bit | 12-bit | 13-bit | **14-bit**\] (Default in **bold**)
- Description: The resolution of the temperature measurement

### Sensirion: SHT2x

- Manufacturer: Sensirion
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensirion: SHT31-D

- Manufacturer: Sensirion
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_SHT31
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-sht31d](https://pypi.org/project/adafruit-circuitpython-sht31d)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-various-applications/)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensirion: SHT3x (30, 31, 35)

- Manufacturer: Sensirion
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_SHT31
- Dependencies: [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit-SHT31](https://pypi.org/project/Adafruit-SHT31)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-various-applications/)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Enable Heater

- Type: Boolean
- Description: Enable heater to evaporate condensation. Turn on heater x seconds every y measurements.

##### Heater On Seconds

- Type: Decimal
- Default Value: 1.0
- Description: How long to turn the heater on (seconds).

##### Heater On Period

- Type: Integer
- Default Value: 10
- Description: After how many measurements to turn the heater on. This will repeat.

### Sensirion: SHT4X

- Manufacturer: Sensirion
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_SHT4X
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit_circuitpython_sht4x](https://pypi.org/project/adafruit_circuitpython_sht4x)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-various-applications/)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensirion: SHTC3

- Manufacturer: Sensirion
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_SHT3C
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit_circuitpython_shtc3](https://pypi.org/project/adafruit_circuitpython_shtc3)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/digital-humidity-sensors-for-various-applications/)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sensorion: SHT31 Smart Gadget

- Manufacturer: Sensorion
- Measurements: Humidity/Temperature
- Interfaces: BT
- Libraries: bluepy
- Dependencies: [pi-bluetooth](https://packages.debian.org/buster/pi-bluetooth), [libglib2.0-dev](https://packages.debian.org/buster/libglib2.0-dev), [bluepy](https://pypi.org/project/bluepy)
- Manufacturer URL: [Link](https://www.sensirion.com/en/environmental-sensors/humidity-sensors/development-kit/)

#### Options

##### MAC (XX:XX:XX:XX:XX:XX)

- Type: Text
- Description: The MAC address of the Bluetooth device

##### BT Adapter (hci[X])

- Type: Integer
- Description: The adapter of the Bluetooth device

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Download Stored Data

- Type: Boolean
- Default Value: True
- Description: Download the data logged to the device.

##### Set Logging Interval

- Type: Integer
- Default Value: 600
- Description: Set the logging interval (seconds) the device will store measurements on its internal memory.

### Silicon Labs: SI1145

- Manufacturer: Silicon Labs
- Measurements: Light (UV/Visible/IR), Proximity (cm)
- Interfaces: I<sup>2</sup>C
- Libraries: si1145
- Dependencies: [SI1145](https://pypi.org/project/SI1145)
- Manufacturer URL: [Link](https://learn.adafruit.com/adafruit-si1145-breakout-board-uv-ir-visible-sensor)
- Datasheet URL: [Link](https://www.silabs.com/support/resources.p-sensors_optical-sensors_si114x)
- Product URL: [Link](https://www.adafruit.com/product/1777)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Silicon Labs: Si7021

- Manufacturer: Silicon Labs
- Measurements: Temperature/Humidity
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit-CircuitPython-Si7021
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-si7021](https://pypi.org/project/adafruit-circuitpython-si7021)
- Datasheet URL: [Link](https://www.silabs.com/documents/public/data-sheets/Si7021-A20.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Sonoff: TH16/10 (Tasmota firmware) with AM2301

- Manufacturer: Sonoff
- Measurements: Humidity/Temperature
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)
- Manufacturer URL: [Link](https://sonoff.tech/product/wifi-diy-smart-switches/th10-th16)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### IP Address

- Type: Text
- Default Value: 192.168.0.100
- Description: The IP address of the device

### Sonoff: TH16/10 (Tasmota firmware) with DS18B20

- Manufacturer: Sonoff
- Measurements: Temperature
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)
- Manufacturer URL: [Link](https://sonoff.tech/product/wifi-diy-smart-switches/th10-th16)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### IP Address

- Type: Text
- Default Value: 192.168.0.100
- Description: The IP address of the device

### TE Connectivity: HTU21D

- Manufacturer: TE Connectivity
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit-CircuitPython-HTU21D
- Dependencies: [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-HTU21D](https://pypi.org/project/adafruit-circuitpython-HTU21D)
- Manufacturer URL: [Link](https://www.te.com/usa-en/product-CAT-HSC0004.html)
- Datasheet URL: [Link](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FHPC199_6%7FA6%7Fpdf%7FEnglish%7FENG_DS_HPC199_6_A6.pdf%7FCAT-HSC0004)
- Product URL: [Link](https://www.adafruit.com/product/1899)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### TE Connectivity: HTU21D

- Manufacturer: TE Connectivity
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: pigpio
- Dependencies: pigpio
- Manufacturer URL: [Link](https://www.te.com/usa-en/product-CAT-HSC0004.html)
- Datasheet URL: [Link](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FHPC199_6%7FA6%7Fpdf%7FEnglish%7FENG_DS_HPC199_6_A6.pdf%7FCAT-HSC0004)
- Product URL: [Link](https://www.adafruit.com/product/1899)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Tasmota: Tasmota Outlet Energy Monitor (HTTP)

- Manufacturer: Tasmota
- Measurements: Total Energy, Amps, Watts
- Interfaces: HTTP
- Libraries: requests
- Manufacturer URL: [Link](https://tasmota.github.io)
- Product URL: [Link](https://templates.blakadder.com/plug.html)

This input queries the energy usage information from a WiFi outlet that is running the tasmota firmware. There are many WiFi outlets that support tasmota, and many of of those have energy monitoring capabilities. When used with an MQTT Output, you can both control your tasmota outlets as well as mionitor their energy usage.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Host

- Type: Text
- Default Value: 192.168.0.50
- Description: Host address or IP

### Texas Instruments: ADS1015

- Manufacturer: Texas Instruments
- Measurements: Voltage (Analog-to-Digital Converter)
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [Adafruit_CircuitPython_ADS1x15](https://pypi.org/project/Adafruit_CircuitPython_ADS1x15)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Measurements to Average

- Type: Integer
- Default Value: 5
- Description: The number of times to measure each channel. An average of the measurements will be stored.

### Texas Instruments: ADS1115: Generic Analog pH/EC

- Manufacturer: Texas Instruments
- Measurements: Ion Concentration/Electrical Conductivity
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_ADS1x15
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [Adafruit_CircuitPython_ADS1x15](https://pypi.org/project/Adafruit_CircuitPython_ADS1x15)

This input relies on an ADS1115 analog-to-digital converter (ADC) to measure pH and/or electrical conductivity (EC) from analog sensors. You can enable or disable either measurement if you want to only connect a pH sensor or an EC sensor by selecting which measurements you want to under Measurements Enabled. Select which channel each sensor is connected to on the ADC. There are default calibration values initially set for the Input. There are also functions to allow you to easily calibrate your sensors with calibration solutions. If you use the Calibrate Slot actions, these values will be calculated and will replace the currently-set values. You can use the Clear Calibration action to delete the database values and return to using the default values. If you delete the Input or create a new Input to use your ADC/sensors with, you will need to recalibrate in order to store new calibration data.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### ADC Channel: pH

- Type: Select
- Options: \[**Channel 0** | Channel 1 | Channel 2 | Channel 3\] (Default in **bold**)
- Description: The ADC channel the pH sensor is connected

##### ADC Channel: EC

- Type: Select
- Options: \[Channel 0 | **Channel 1** | Channel 2 | Channel 3\] (Default in **bold**)
- Description: The ADC channel the EC sensor is connected

##### Temperature Compensation

##### Temperature Compensation: Measurement

- Type: Select Measurement
- Selections: Input, Function, Math, 
- Description: Select a measurement for temperature compensation

##### Temperature Compensation: Max Age

- Type: Integer
- Default Value: 120
- Description: The maximum age (seconds) of the measurement to use

##### pH Calibration Data

##### Cal data: V1 (internal)

- Type: Decimal
- Default Value: 1.5
- Description: Calibration data: Voltage

##### Cal data: pH1 (internal)

- Type: Decimal
- Default Value: 7.0
- Description: Calibration data: pH

##### Cal data: T1 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: Calibration data: Temperature

##### Cal data: V2 (internal)

- Type: Decimal
- Default Value: 2.032
- Description: Calibration data: Voltage

##### Cal data: pH2 (internal)

- Type: Decimal
- Default Value: 4.0
- Description: Calibration data: pH

##### Cal data: T2 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: Calibration data: Temperature

##### EC Calibration Data

##### EC cal data: V1 (internal)

- Type: Decimal
- Default Value: 0.232
- Description: EC calibration data: Voltage

##### EC cal data: EC1 (internal)

- Type: Decimal
- Default Value: 1413.0
- Description: EC calibration data: EC

##### EC cal data: T1 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: EC calibration data: EC

##### EC cal data: V2 (internal)

- Type: Decimal
- Default Value: 2.112
- Description: EC calibration data: Voltage

##### EC cal data: EC2 (internal)

- Type: Decimal
- Default Value: 12880.0
- Description: EC calibration data: EC

##### EC cal data: T2 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: EC calibration data: EC

#### Actions

##### pH Calibration Actions: Place your probe in a solution of known pH.
            Set the known pH value in the "Calibration buffer pH" field, and press "Calibrate pH, slot 1".
            Repeat with a second buffer, and press "Calibrate pH, slot 2".
            You don't need to change the values under "Custom Options".

##### Calibration buffer pH

- Type: Decimal
- Default Value: 7.0
- Description: This is the nominal pH of the calibration buffer, usually labelled on the bottle.

##### Calibrate pH, slot 1

- Type: Button
##### Calibrate pH, slot 2

- Type: Button
##### Clear pH Calibration Slots

- Type: Button
##### EC Calibration Actions: Place your probe in a solution of known EC.
            Set the known EC value in the "Calibration standard EC" field, and press "Calibrate EC, slot 1".
            Repeat with a second standard, and press "Calibrate EC, slot 2".
            You don't need to change the values under "Custom Options".

##### Calibration standard EC

- Type: Decimal
- Default Value: 1413.0
- Description: This is the nominal EC of the calibration standard, usually labelled on the bottle.

##### Calibrate EC, slot 1

- Type: Button
##### Calibrate EC, slot 2

- Type: Button
##### Clear pH Calibration Slots

- Type: Button
### Texas Instruments: ADS1115

- Manufacturer: Texas Instruments
- Measurements: Voltage (Analog-to-Digital Converter)
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython_ADS1x15
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [Adafruit_CircuitPython_ADS1x15](https://pypi.org/project/Adafruit_CircuitPython_ADS1x15)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Measurements to Average

- Type: Integer
- Default Value: 5
- Description: The number of times to measure each channel. An average of the measurements will be stored.

### Texas Instruments: ADS1256: Generic Analog pH/EC

- Manufacturer: Texas Instruments
- Measurements: Ion Concentration/Electrical Conductivity
- Interfaces: UART
- Libraries: wiringpi, kizniche/PiPyADC-py3
- Dependencies: [wiringpi](https://pypi.org/project/wiringpi), [pipyadc_py3](https://github.com/kizniche/PiPyADC-py3)

This input relies on an ADS1256 analog-to-digital converter (ADC) to measure pH and/or electrical conductivity (EC) from analog sensors. You can enable or disable either measurement if you want to only connect a pH sensor or an EC sensor by selecting which measurements you want to under Measurements Enabled. Select which channel each sensor is connected to on the ADC. There are default calibration values initially set for the Input. There are also functions to allow you to easily calibrate your sensors with calibration solutions. If you use the Calibrate Slot actions, these values will be calculated and will replace the currently-set values. You can use the Clear Calibration action to delete the database values and return to using the default values. If you delete the Input or create a new Input to use your ADC/sensors with, you will need to recalibrate in order to store new calibration data.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### ADC Channel: pH

- Type: Select
- Options: \[Not Connected | **Channel 0** | Channel 1 | Channel 2 | Channel 3 | Channel 4 | Channel 5 | Channel 6 | Channel 7\] (Default in **bold**)
- Description: The ADC channel the pH sensor is connected

##### ADC Channel: EC

- Type: Select
- Options: \[Not Connected | Channel 0 | **Channel 1** | Channel 2 | Channel 3 | Channel 4 | Channel 5 | Channel 6 | Channel 7\] (Default in **bold**)
- Description: The ADC channel the EC sensor is connected

##### Temperature Compensation

##### Temperature Compensation: Measurement

- Type: Select Measurement
- Selections: Input, Function, Math, 
- Description: Select a measurement for temperature compensation

##### Temperature Compensation: Max Age

- Type: Integer
- Default Value: 120
- Description: The maximum age (seconds) of the measurement to use

##### pH Calibration Data

##### Cal data: V1 (internal)

- Type: Decimal
- Default Value: 1.5
- Description: Calibration data: Voltage

##### Cal data: pH1 (internal)

- Type: Decimal
- Default Value: 7.0
- Description: Calibration data: pH

##### Cal data: T1 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: Calibration data: Temperature

##### Cal data: V2 (internal)

- Type: Decimal
- Default Value: 2.032
- Description: Calibration data: Voltage

##### Cal data: pH2 (internal)

- Type: Decimal
- Default Value: 4.0
- Description: Calibration data: pH

##### Cal data: T2 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: Calibration data: Temperature

##### EC Calibration Data

##### EC cal data: V1 (internal)

- Type: Decimal
- Default Value: 0.232
- Description: EC calibration data: Voltage

##### EC cal data: EC1 (internal)

- Type: Decimal
- Default Value: 1413.0
- Description: EC calibration data: EC

##### EC cal data: T1 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: EC calibration data: EC

##### EC cal data: V2 (internal)

- Type: Decimal
- Default Value: 2.112
- Description: EC calibration data: Voltage

##### EC cal data: EC2 (internal)

- Type: Decimal
- Default Value: 12880.0
- Description: EC calibration data: EC

##### EC cal data: T2 (internal)

- Type: Decimal
- Default Value: 25.0
- Description: EC calibration data: EC

##### Calibration

- Type: Select
- Description: Set the calibration method to perform during Input activation

#### Actions

##### pH Calibration Actions: Place your probe in a solution of known pH.
            Set the known pH value in the `Calibration buffer pH` field, and press `Calibrate pH, slot 1`.
            Repeat with a second buffer, and press `Calibrate pH, slot 2`.
            You don't need to change the values under `Custom Options`.

##### Calibration buffer pH

- Type: Decimal
- Default Value: 7.0
- Description: This is the nominal pH of the calibration buffer, usually labelled on the bottle.

##### Calibrate pH, slot 1

- Type: Button
##### Calibrate pH, slot 2

- Type: Button
##### Clear pH Calibration Slots

- Type: Button
##### EC Calibration Actions: Place your probe in a solution of known EC.
            Set the known EC value in the `Calibration standard EC` field, and press `Calibrate EC, slot 1`.
            Repeat with a second standard, and press `Calibrate EC, slot 2`.
            You don't need to change the values under `Custom Options`.

##### Calibration standard EC

- Type: Decimal
- Default Value: 1413.0
- Description: This is the nominal EC of the calibration standard, usually labelled on the bottle.

##### Calibrate EC, slot 1

- Type: Button
##### Calibrate EC, slot 2

- Type: Button
##### Clear EC Calibration Slots

- Type: Button
### Texas Instruments: ADS1256

- Manufacturer: Texas Instruments
- Measurements: Voltage (Waveshare, Analog-to-Digital Converter)
- Interfaces: UART
- Libraries: wiringpi, kizniche/PiPyADC-py3
- Dependencies: [wiringpi](https://pypi.org/project/wiringpi), [pipyadc_py3](https://github.com/kizniche/PiPyADC-py3)

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Calibration

- Type: Select
- Description: Set the calibration method to perform during Input activation

### Texas Instruments: ADS1x15

- Manufacturer: Texas Instruments
- Measurements: Voltage (Analog-to-Digital Converter)
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_ADS1x15 [DEPRECATED]
- Dependencies: [Adafruit-GPIO](https://pypi.org/project/Adafruit-GPIO), [Adafruit-ADS1x15](https://pypi.org/project/Adafruit-ADS1x15)

The Adafruit_ADS1x15 is deprecated. It's advised to use The Circuit Python ADS1x15 Input.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Measurements to Average

- Type: Integer
- Default Value: 5
- Description: The number of times to measure each channel. An average of the measurements will be stored.

### Texas Instruments: HDC1000

- Manufacturer: Texas Instruments
- Measurements: Humidity/Temperature
- Interfaces: I<sup>2</sup>C
- Libraries: fcntl/io
- Manufacturer URL: [Link](https://www.ti.com/product/HDC1000)
- Datasheet URL: [Link](https://www.ti.com/lit/ds/symlink/hdc1000.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Texas Instruments: INA219x

- Manufacturer: Texas Instruments
- Measurements: Electrical Current (DC)
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_CircuitPython
- Dependencies: [adafruit-circuitpython-ina219](https://pypi.org/project/adafruit-circuitpython-ina219), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus)
- Manufacturer URL: [Link](https://www.ti.com/product/INA219)
- Datasheet URL: [Link](https://www.ti.com/lit/gpn/ina219)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Measurements to Average

- Type: Integer
- Default Value: 5
- Description: The number of times to measure each channel. An average of the measurements will be stored.

##### Calibration Range

- Type: Select
- Options: \[**32V @ 2A max (default)** | 32V @ 1A max | 16V @ 400mA max | 16V @ 5A max\] (Default in **bold**)
- Description: Set the device calibration range

##### Bus Voltage Range

- Type: Select
- Options: \[(0x00) - 16V | **(0x01) - 32V (default)**\] (Default in **bold**)
- Description: Set the bus voltage range

##### Bus ADC Resolution

- Type: Select
- Options: \[(0x00) - 9 Bit / 1 Sample | (0x01) - 10 Bit / 1 Sample | (0x02) - 11 Bit / 1 Sample | **(0x03) - 12 Bit / 1 Sample (default)** | (0x09) - 12 Bit / 2 Samples | (0x0A) - 12 Bit / 4 Samples | (0x0B) - 12 Bit / 8 Samples | (0x0C) - 12 Bit / 16 Samples | (0x0D) - 12 Bit / 32 Samples | (0x0E) - 12 Bit / 64 Samples | (0x0F) - 12 Bit / 128 Samples\] (Default in **bold**)
- Description: Set the Bus ADC Resolution.

##### Shunt ADC Resolution

- Type: Select
- Options: \[(0x00) - 9 Bit / 1 Sample | (0x01) - 10 Bit / 1 Sample | (0x02) - 11 Bit / 1 Sample | **(0x03) - 12 Bit / 1 Sample (default)** | (0x09) - 12 Bit / 2 Samples | (0x0A) - 12 Bit / 4 Samples | (0x0B) - 12 Bit / 8 Samples | (0x0C) - 12 Bit / 16 Samples | (0x0D) - 12 Bit / 32 Samples | (0x0E) - 12 Bit / 64 Samples | (0x0F) - 12 Bit / 128 Samples\] (Default in **bold**)
- Description: Set the Shunt ADC Resolution.

### Texas Instruments: TMP006

- Manufacturer: Texas Instruments
- Measurements: Temperature (Object/Die)
- Interfaces: I<sup>2</sup>C
- Libraries: Adafruit_TMP
- Dependencies: [Adafruit-TMP](https://pypi.org/project/Adafruit-TMP)
- Datasheet URL: [Link](http://www.adafruit.com/datasheets/tmp006.pdf)
- Product URL: [Link](https://www.adafruit.com/product/1296)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Weather: OpenWeatherMap (City, Current)

- Manufacturer: Weather
- Measurements: Humidity/Temperature/Pressure/Wind
- Interfaces: Mycodo
- Additional URL: [Link](https://openweathermap.org)

Obtain a free API key at openweathermap.org. If the city you enter does not return measurements, try another city. Note: the free API subscription is limited to 60 calls per minute

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### API Key

- Type: Text
- Description: The API Key for this service's API

##### City

- Type: Text
- Description: The city to acquire the weather data

### Weather: OpenWeatherMap (Lat/Lon, Current/Future)

- Manufacturer: Weather
- Measurements: Humidity/Temperature/Pressure/Wind
- Interfaces: Mycodo
- Additional URL: [Link](https://openweathermap.org)

Obtain a free API key at openweathermap.org. Notes: The free API subscription is limited to 60 calls per minute. If a Day (Future) time is selected, Minimum and Maximum temperatures are available as measurements.

#### Options

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### API Key

- Type: Text
- Description: The API Key for this service's API

##### Latitude (decimal)

- Type: Decimal
- Default Value: 33.441792
- Description: The latitude to acquire weather data

##### Longitude (decimal)

- Type: Decimal
- Default Value: -94.037689
- Description: The longitude to acquire weather data

##### Time

- Type: Select
- Options: \[**Current (Present)** | 1 Day (Future) | 2 Day (Future) | 3 Day (Future) | 4 Day (Future) | 5 Day (Future) | 6 Day (Future) | 7 Day (Future) | 1 Hour (Future) | 2 Hours (Future) | 3 Hours (Future) | 4 Hours (Future) | 5 Hours (Future) | 6 Hours (Future) | 7 Hours (Future) | 8 Hours (Future) | 9 Hours (Future) | 10 Hours (Future) | 11 Hours (Future) | 12 Hours (Future) | 13 Hours (Future) | 14 Hours (Future) | 15 Hours (Future) | 16 Hours (Future) | 17 Hours (Future) | 18 Hours (Future) | 19 Hours (Future) | 20 Hours (Future) | 21 Hours (Future) | 22 Hours (Future) | 23 Hours (Future) | 24 Hours (Future) | 25 Hours (Future) | 26 Hours (Future) | 27 Hours (Future) | 28 Hours (Future) | 29 Hours (Future) | 30 Hours (Future) | 31 Hours (Future) | 32 Hours (Future) | 33 Hours (Future) | 34 Hours (Future) | 35 Hours (Future) | 36 Hours (Future) | 37 Hours (Future) | 38 Hours (Future) | 39 Hours (Future) | 40 Hours (Future) | 41 Hours (Future) | 42 Hours (Future) | 43 Hours (Future) | 44 Hours (Future) | 45 Hours (Future) | 46 Hours (Future) | 47 Hours (Future) | 48 Hours (Future)\] (Default in **bold**)
- Description: Select the time for the current or forecast weather

### Winsen: MH-Z16

- Manufacturer: Winsen
- Measurements: CO2
- Interfaces: UART, I<sup>2</sup>C
- Libraries: smbus2/serial
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.winsen-sensor.com/sensors/co2-sensor/mh-z16.html)
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/MH-Z16.pdf)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Winsen: MH-Z19

- Manufacturer: Winsen
- Measurements: CO2
- Interfaces: UART
- Libraries: serial
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/PDF/Infrared%20Gas%20Sensor/NDIR%20CO2%20SENSOR/MH-Z19%20CO2%20Ver1.0.pdf)

This is the version of the sensor that does not include the ability to conduct automatic baseline correction (ABC). See the B version of the sensor if you wish to use ABC.

#### Options

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Measurement Range

- Type: Select
- Options: \[0 - 1000 ppmv | 0 - 2000 ppmv | 0 - 3000 ppmv | **0 - 5000 ppmv**\] (Default in **bold**)
- Description: Set the measuring range of the sensor

#### Actions

##### Calibrate Zero Point

- Type: Button
##### Span Point (ppmv)

- Type: Integer
- Default Value: 1500
- Description: The ppmv concentration for a span point calibration

##### Calibrate Span Point

- Type: Button
### Winsen: MH-Z19B

- Manufacturer: Winsen
- Measurements: CO2
- Interfaces: UART
- Libraries: serial
- Manufacturer URL: [Link](https://www.winsen-sensor.com/sensors/co2-sensor/mh-z19b.html)
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/MH-Z19B.pdf)

This is the B version of the sensor that includes the ability to conduct automatic baseline correction (ABC).

#### Options

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Automatic Baseline Correction

- Type: Boolean
- Description: Enable automatic baseline correction (ABC)

##### Measurement Range

- Type: Select
- Options: \[0 - 1000 ppmv | 0 - 2000 ppmv | 0 - 3000 ppmv | **0 - 5000 ppmv** | 0 - 10000 ppmv\] (Default in **bold**)
- Description: Set the measuring range of the sensor

#### Actions

##### Calibrate Zero Point

- Type: Button
##### Span Point (ppmv)

- Type: Integer
- Default Value: 1500
- Description: The ppmv concentration for a span point calibration

##### Calibrate Span Point

- Type: Button
### Winsen: ZH03B

- Manufacturer: Winsen
- Measurements: Particulates
- Interfaces: UART
- Libraries: serial
- Manufacturer URL: [Link](https://www.winsen-sensor.com/sensors/dust-sensor/zh3b.html)
- Datasheet URL: [Link](https://www.winsen-sensor.com/d/files/ZH03B.pdf)

#### Options

##### UART Device

- Type: Text
- Description: The UART device location (e.g. /dev/ttyUSB1)

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Fan Off After Measure

- Type: Boolean
- Description: Turn the fan on only during the measurement

##### Fan On Duration

- Type: Decimal
- Default Value: 50.0
- Description: How long to turn the fan on (seconds) before acquiring measurements

##### Number of Measurements

- Type: Integer
- Default Value: 3
- Description: How many measurements to acquire. If more than 1 are acquired that are less than 1001, the average of the measurements will be stored.

### Xiaomi: Miflora

- Manufacturer: Xiaomi
- Measurements: EC/Light/Moisture/Temperature
- Interfaces: BT
- Libraries: miflora
- Dependencies: [libglib2.0-dev](https://packages.debian.org/buster/libglib2.0-dev), [miflora](https://pypi.org/project/miflora), [bluepy](https://pypi.org/project/bluepy)

#### Options

##### MAC (XX:XX:XX:XX:XX:XX)

- Type: Text
- Description: The MAC address of the Bluetooth device

##### BT Adapter (hci[X])

- Type: Integer
- Description: The adapter of the Bluetooth device

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

### Xiaomi: Mijia LYWSD03MMC (ATC and non-ATC modes)

- Manufacturer: Xiaomi
- Measurements: Battery/Humidity/Temperature
- Interfaces: BT
- Libraries: bluepy/bluez
- Dependencies: [bluez](https://packages.debian.org/buster/bluez), [bluetooth](https://packages.debian.org/buster/bluetooth), [libbluetooth-dev](https://packages.debian.org/buster/libbluetooth-dev), [bluepy](https://pypi.org/project/bluepy), [pybluez](https://pypi.org/project/pybluez)

More information about ATC mode can be found at https://github.com/JsBergbau/MiTemperature2

#### Options

##### MAC (XX:XX:XX:XX:XX:XX)

- Type: Text
- Description: The MAC address of the Bluetooth device

##### BT Adapter (hci[X])

- Type: Integer
- Description: The adapter of the Bluetooth device

##### Measurements Enabled

- Type: Multi-Select
- Description: The measurements to record

##### Period (seconds)

- Type: Decimal
- Description: The duration (seconds) between measurements or actions

##### Pre Output

- Type: Select
- Description: Turn the selected output on before taking every measurement

##### Pre Out Duration

- Type: Decimal
- Description: If a Pre Output is selected, set the duration (seconds) to turn the Pre Output on for before every measurement is acquired.

##### Pre During Measure

- Type: Boolean
- Description: Check to turn the output off after (opposed to before) the measurement is complete

##### Enable ATC Mode

- Type: Boolean
- Description: Enable sensor ATC mode

