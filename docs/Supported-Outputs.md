Supported Outputs are listed below.

## Built-In Outputs (System)

### MQTT Publish: On/Off

- Manufacturer: Mycodo
- Interfaces: Mycodo
- Output Types: On/Off
- Libraries: paho-mqtt
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)
- Additional URL: [Link](http://www.eclipse.org/paho/)

Publish "on" or "off" (or any other strings of your choosing) to an MQTT server.

#### Options

#### Channel Options

##### Hostname

- Type: Text
- Default Value: localhost
- Description: The hostname of the MQTT server

##### Port

- Type: Integer
- Default Value: 1883
- Description: The port of the MQTT server

##### Topic

- Type: Text
- Default Value: paho/test/single
- Description: The topic to publish with

##### Keep Alive

- Type: Integer
- Default Value: 60
- Description: The keepalive timeout value for the client. Set to 0 to disable.

##### Client ID

- Type: Text
- Default Value: mycodo_mqtt_client
- Description: Unique client ID for connecting to the MQTT server

##### On Payload

- Type: Text
- Default Value: on
- Description: The payload to send when turned on

##### Off Payload

- Type: Text
- Default Value: off
- Description: The payload to send when turned off

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Force Command

- Type: Boolean
- Description: Always send the command if instructed, regardless of the current state

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

##### Use Login

- Type: Boolean
- Description: Send login credentials

##### Username

- Type: Text
- Default Value: user
- Description: Username for connecting to the server

##### Password

- Type: Text
- Description: Password for connecting to the server. Leave blank to disable.

### MQTT Publish: Value

- Manufacturer: Mycodo
- Interfaces: Mycodo
- Output Types: Value
- Libraries: paho-mqtt
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)
- Additional URL: [Link](http://www.eclipse.org/paho/)

Publish a value to an MQTT server.

#### Options

#### Channel Options

##### Hostname

- Type: Text
- Default Value: localhost
- Description: The hostname of the MQTT server

##### Port

- Type: Integer
- Default Value: 1883
- Description: The port of the MQTT server

##### Topic

- Type: Text
- Default Value: paho/test/single
- Description: The topic to publish with

##### Keep Alive

- Type: Integer
- Default Value: 60
- Description: The keepalive timeout value for the client. Set to 0 to disable.

##### Client ID

- Type: Text
- Default Value: mycodo_mqtt_client
- Description: Unique client ID for connecting to the MQTT server

##### Off Value

- Type: Integer
- Description: The value to send when an Off command is given

##### Use Login

- Type: Boolean
- Description: Send login credentials

##### Username

- Type: Text
- Default Value: user
- Description: Username for connecting to the server

##### Password

- Type: Text
- Description: Password for connecting to the server.

## Built-In Outputs (Devices)

### DC Motor Controller: L298N

- Manufacturer: STMicroelectronics
- Interfaces: GPIO
- Output Types: Volume, On/Off
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Additional URL: [Link](https://www.electronicshub.org/raspberry-pi-l298n-interface-tutorial-control-dc-motor-l298n-raspberry-pi/)

The L298N can control 2 DC motors. If these motors control peristaltic pumps, set the Flow Rate and the output can can be instructed to dispense volumes accurately in addition to being turned on for durations.

#### Options

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Input Pin 1

- Type: Integer
- Description: The Input Pin 1 of the controller (BCM numbering)

##### Input Pin 2

- Type: Integer
- Description: The Input Pin 2 of the controller (BCM numbering)

##### Use Enable Pin

- Type: Boolean
- Default Value: True
- Description: Enable the use of the Enable Pin

##### Enable Pin

- Type: Integer
- Description: The Enable pin of the controller (BCM numbering)

##### Enable Pin Duty Cycle

- Type: Integer
- Default Value: 50
- Description: The duty cycle to apply to the Enable Pin (percent, 1 - 100)

##### Direction

- Type: Select
- Options: \[**Forward** | Backward\] (Default in **bold**)
- Description: The direction to turn the motor

##### Volume Rate (ml/min)

- Type: Decimal
- Default Value: 150.0
- Description: If a pump, the measured flow rate (ml/min) at the set Duty Cycle

### Digital Potentiometer: DS3502

- Manufacturer: Maxim Integrated
- Interfaces: I<sup>2</sup>C
- Output Types: Value
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [adafruit-circuitpython-ds3502](https://pypi.org/project/adafruit-circuitpython-ds3502)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/analog/data-converters/digital-potentiometers/DS3502.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS3502.pdf)
- Product URL: [Link](https://www.adafruit.com/product/4286)

The DS3502 can generate a 0 - 10k Ohm resistance with 7-bit precision. This equates to 128 possible steps. A value, in Ohms, is passed to this output controller and the step value is calculated and passed to the device. Select whether to round up or down to the nearest step.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Round Step

- Type: Select
- Options: \[**Up** | Down\] (Default in **bold**)
- Description: Round direction to the nearest step value

### Digital-to-Analog Converter: MCP4728

- Manufacturer: MICROCHIP
- Interfaces: I<sup>2</sup>C
- Output Types: Value
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-mcp4728](https://pypi.org/project/adafruit-circuitpython-mcp4728)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/en541737)
- Datasheet URL: [Link](https://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf)
- Product URL: [Link](https://www.adafruit.com/product/4470)

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### VREF (volts)

- Type: Decimal
- Default Value: 4.096
- Description: Set the VREF voltage

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### VREF

- Type: Select
- Options: \[**Internal** | VDD\] (Default in **bold**)
- Description: Select the channel VREF

##### Gain

- Type: Select
- Options: \[**1X** | 2X\] (Default in **bold**)
- Description: Select the channel Gain

##### Start State

- Type: Select
- Options: \[**Previously-Saved State** | Specified Value\] (Default in **bold**)
- Description: Select the channel start state

##### Start Value (volts)

- Type: Decimal
- Description: If Specified Value is selected, set the start state value

##### Shutdown State

- Type: Select
- Options: \[**Previously-Saved Value** | Specified Value\] (Default in **bold**)
- Description: Select the channel shutdown state

##### Shutdown Value (volts)

- Type: Decimal
- Description: If Specified Value is selected, set the shutdown state value

### GPIO: On/Off

- Interfaces: GPIO
- Output Types: On/Off
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

The specified GPIO pin will be set HIGH (3.3 volts) or LOW (0 volts) when turned on or off, depending on the On State option.

#### Options

#### Channel Options

##### GPIO Pin (BCM)

- Type: Integer
- Description: The pin to control the state of

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### On State

- Type: Select
- Options: \[**HIGH** | LOW\] (Default in **bold**)
- Description: The state of the GPIO that corresponds to an On state

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### GPIO: PWM

- Interfaces: GPIO
- Output Types: PWM
- Libraries: pigpio
- Dependencies: pigpio

See the PWM section of the manual for PWM information and determining which pins may be used for each library option.

#### Options

#### Channel Options

##### GPIO Pin (BCM)

- Type: Integer
- Description: The pin to control the state of

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Startup Value

- Type: Decimal
- Description: The value when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Shutdown Value

- Type: Decimal
- Description: The value when Mycodo shuts down

##### Library

- Type: Select
- Options: \[**Any Pin, <= 40 kHz** | Hardware Pin, <= 30 MHz\] (Default in **bold**)
- Description: Which method to produce the PWM signal (hardware pins can produce higher frequencies)

##### Frequency (Hertz)

- Type: Integer
- Default Value: 22000
- Description: The Herts to output the PWM signal (0 - 70,000)

##### Invert Signal

- Type: Boolean
- Description: Invert the PWM signal

##### Invert Stored Signal

- Type: Boolean
- Description: Invert the value that is saved to the measurement database

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### Grove I2C Motor Driver (Board v1.3) (Test Module 01)

- Manufacturer: Grove
- Interfaces: I<sup>2</sup>C
- Output Types: Volume, On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://wiki.seeedstudio.com/Grove-I2C_Motor_Driver_V1.3)

Controls the Grove I2C Motor Driver Board (v1.3). Both motors will turn at the same time. This output can also dispense volumes of fluid if the motors are attached to peristaltic pumps.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Motor Speed (0 - 100)

- Type: Integer
- Default Value: 100
- Description: The motor output that determines the speed

##### Flow Rate Method

- Type: Select
- Options: \[**Fastest Flow Rate** | Specify Flow Rate\] (Default in **bold**)
- Description: The flow rate to use when pumping a volume

##### Desired Flow Rate (ml/min)

- Type: Decimal
- Default Value: 10.0
- Description: Desired flow rate in ml/minute when Specify Flow Rate set

##### Fastest Rate (ml/min)

- Type: Decimal
- Default Value: 100.0
- Description: The fastest rate that the pump can dispense (ml/min)

### Grove I2C Motor Driver (TB6612FNG, Board v1.0)

- Manufacturer: Grove
- Interfaces: I<sup>2</sup>C
- Output Types: Volume, On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://wiki.seeedstudio.com/Grove-I2C_Motor_Driver-TB6612FNG)

Controls the Grove I2C Motor Driver Board (v1.3). Both motors will turn at the same time. This output can also dispense volumes of fluid if the motors are attached to peristaltic pumps.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Motor Speed (0 - 255)

- Type: Integer
- Default Value: 255
- Description: The motor output that determines the speed

##### Flow Rate Method

- Type: Select
- Options: \[**Fastest Flow Rate** | Specify Flow Rate\] (Default in **bold**)
- Description: The flow rate to use when pumping a volume

##### Desired Flow Rate (ml/min)

- Type: Decimal
- Default Value: 10.0
- Description: Desired flow rate in ml/minute when Specify Flow Rate set

##### Fastest Rate (ml/min)

- Type: Decimal
- Default Value: 100.0
- Description: The fastest rate that the pump can dispense (ml/min)

##### Minimum On (sec/min)

- Type: Decimal
- Default Value: 1.0
- Description: The minimum duration (seconds) the pump turns on for every 60 second period (only used for Specify Flow Rate mode).

#### Actions

##### New I2C Address

- Type: Text
- Default Value: 0x14
- Description: The new I2C to set the sensor to

##### Set I2C Address

- Type: Button
### Grove Multichannel Relay (4- or 8-Channel board)

- Manufacturer: Grove
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.seeedstudio.com/Grove-4-Channel-SPDT-Relay-p-3119.html)
- Datasheet URL: [Link](http://wiki.seeedstudio.com/Grove-4-Channel_SPDT_Relay/)
- Product URL: [Link](https://www.seeedstudio.com/Grove-4-Channel-SPDT-Relay-p-3119.html)

Controls the 4 or 8 channel Grove multichannel relay board.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Startup State

- Type: Select
- Description: Set the state of the relay when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state of the relay when Mycodo shuts down

##### On State

- Type: Select
- Options: \[**HIGH** | LOW\] (Default in **bold**)
- Description: The state of the GPIO that corresponds to an On state

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### I/O Expander: MCP23017 (16 Channels): On/Off

- Manufacturer: MICROCHIP
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [adafruit-extended-bus](https://pypi.org/project/adafruit-extended-bus), [adafruit-circuitpython-mcp230xx](https://pypi.org/project/adafruit-circuitpython-mcp230xx)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/MCP23017)
- Datasheet URL: [Link](https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf)
- Product URL: [Link](https://www.amazon.com/Waveshare-MCP23017-Expansion-Interface-Expands/dp/B07P2H1NZG)

Controls the 16 channels of the MCP23017.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Startup State

- Type: Select
- Description: Set the state of the GPIO when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state of the GPIO when Mycodo shuts down

##### On State

- Type: Select
- Options: \[**HIGH** | LOW\] (Default in **bold**)
- Description: The state of the GPIO that corresponds to an On state

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### I/O Expander: PCF8574 (8 Channels): On/Off

- Manufacturer: Texas Instruments
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.ti.com/product/PCF8574)
- Datasheet URL: [Link](https://www.ti.com/lit/ds/symlink/pcf8574.pdf)
- Product URL: [Link](https://www.amazon.com/gp/product/B07JGSNWFF)

Controls the 8 channels of the PCF8574.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Startup State

- Type: Select
- Description: Set the state of the GPIO when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state of the GPIO when Mycodo shuts down

##### On State

- Type: Select
- Options: \[**HIGH** | LOW\] (Default in **bold**)
- Description: The state of the GPIO that corresponds to an On state

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### KP303 Kasa Smart WiFi Power Strip

- Manufacturer: TP-Link
- Interfaces: Mycodo
- Output Types: On/Off
- Dependencies: [python-kasa](https://pypi.org/project/python-kasa)
- Manufacturer URL: [Link](https://www.tp-link.com/au/home-networking/smart-plug/kp303/)

This output controls the 3 outlets of the Kasa KP303 Smart WiFi Power Strip.

#### Options

##### Host

- Type: Text
- Default Value: 192.168.0.50
- Description: Host address or IP

##### Status Update (Sec)

- Type: Integer
- Default Value: 60
- Description: The period (seconds) between checking if connected and output states.

#### Channel Options

##### Name

- Type: Text
- Default Value: Outlet Name
- Description: A name to distinguish this from others

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Force Command

- Type: Boolean
- Description: Always send the command if instructed, regardless of the current state

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### LED Controller: PCA9685 (16 channels): PWM

- Manufacturer: NXP Semiconductors
- Interfaces: I<sup>2</sup>C
- Output Types: PWM
- Libraries: adafruit-pca9685
- Dependencies: [adafruit-pca9685](https://pypi.org/project/adafruit-pca9685)
- Manufacturer URL: [Link](https://www.nxp.com/products/power-management/lighting-driver-and-controller-ics/ic-led-controllers/16-channel-12-bit-pwm-fm-plus-ic-bus-led-controller:PCA9685)
- Datasheet URL: [Link](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf)
- Product URL: [Link](https://www.adafruit.com/product/815)

The PCA9685 can output a PWM signal to 16 channels at a frequency between 40 and 1600 Hz.

#### Options

##### I<sup>2</sup>C Address

- Type: Text
- Description: The I2C address of the device

##### I<sup>2</sup>C Bus

- Type: Integer
- Description: The I2C bus the device is connected to

##### Frequency (Hertz)

- Type: Integer
- Default Value: 1600
- Description: The Herts to output the PWM signal (40 - 1600)

#### Channel Options

##### Name

- Type: Text
- Description: A name to distinguish this from others

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Startup Value

- Type: Decimal
- Description: The value when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Shutdown Value

- Type: Decimal
- Description: The value when Mycodo shuts down

##### Invert Signal

- Type: Boolean
- Description: Invert the PWM signal

##### Invert Stored Signal

- Type: Boolean
- Description: Invert the value that is saved to the measurement database

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### Peristaltic Pump: Atlas Scientific

- Manufacturer: Atlas Scientific
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Output Types: Volume, On/Off
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://atlas-scientific.com/peristaltic/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO_PMP_Datasheet.pdf)
- Product URL: [Link](https://atlas-scientific.com/peristaltic/ezo-pmp/)

Atlas Scientific peristaltic pumps can be set to dispense at their maximum rate or a rate can be specified. Their minimum flow rate is 0.5 ml/min and their maximum is 105 ml/min.

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

#### Channel Options

##### Flow Rate Method

- Type: Select
- Options: \[**Fastest Flow Rate** | Specify Flow Rate\] (Default in **bold**)
- Description: The flow rate to use when pumping a volume

##### Desired Flow Rate (ml/min)

- Type: Decimal
- Default Value: 10.0
- Description: Desired flow rate in ml/minute when Specify Flow Rate set

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

#### Actions

##### Calibration: a calibration can be performed to increase the accuracy of the pump. It's a good idea to clear the calibration before calibrating. First, remove all air from the line by pumping the fluid you would like to calibrate to through the pump hose. Next, press Dispense Amount and the pump will be instructed to dispense 10 ml (unless you changed the default value). Measure how much fluid was actually dispensed, enter this value in the Actual Volume Dispensed (ml) field, and press Calibrate to Dispensed Amount. Now any further pump volumes dispensed should be accurate.

##### Clear Calibration

- Type: Button
##### Volume to Dispense (ml)

- Type: Decimal
- Default Value: 10.0
- Description: The volume (ml) that is instructed to be dispensed

##### Dispense Amount

- Type: Button
##### Actual Volume Dispensed (ml)

- Type: Decimal
- Default Value: 10.0
- Description: The actual volume (ml) that was dispensed

##### Calibrate to Dispensed Amount

- Type: Button
##### The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.

##### New I2C Address

- Type: Text
- Default Value: 0x67
- Description: The new I2C to set the device to

##### Set I2C Address

- Type: Button
### Peristaltic Pump: Generic

- Interfaces: GPIO
- Output Types: Volume, On/Off
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

This output turns a GPIO pin HIGH and LOW to control power to a generic peristaltic pump. The peristaltic pump can then be turned on for a duration or, after determining the pump's maximum flow rate, instructed to dispense a specific volume at the maximum rate or at a specified rate.

#### Options

#### Channel Options

##### GPIO Pin (BCM)

- Type: Integer
- Description: The pin to control the state of

##### On State

- Type: Select
- Options: \[**HIGH** | LOW\] (Default in **bold**)
- Description: The state of the GPIO that corresponds to an On state

##### Fastest Rate (ml/min)

- Type: Decimal
- Default Value: 150.0
- Description: The fastest rate that the pump can dispense (ml/min)

##### Minimum On (sec/min)

- Type: Decimal
- Default Value: 1.0
- Description: The minimum duration (seconds) the pump should be turned on for every 60 second period

##### Flow Rate Method

- Type: Select
- Options: \[**Fastest Flow Rate** | Specify Flow Rate\] (Default in **bold**)
- Description: The flow rate to use when pumping a volume

##### Desired Flow Rate (ml/min)

- Type: Decimal
- Default Value: 10.0
- Description: Desired flow rate in ml/minute when Specify Flow Rate set

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### Python Code: On/Off

- Interfaces: Python
- Output Types: On/Off

Python 3 code will be executed when this output is turned on or off.

#### Options

#### Channel Options

##### On Command

- Description: Python code to execute when the output is instructed to turn on

##### Off Command

- Description: Python code to execute when the output is instructed to turn off

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Force Command

- Type: Boolean
- Description: Always send the command if instructed, regardless of the current state

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### Python Code: PWM

- Interfaces: Python
- Output Types: PWM

Python 3 code will be executed when this output is turned on or off. The "duty_cycle" object is a float value that represents the duty cycle that has been set.

#### Options

#### Channel Options

##### Bash Command

- Description: Command to execute to set the PWM duty cycle (%)

##### User

- Type: Text
- Default Value: mycodo
- Description: The user to execute the command

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Startup Value

- Type: Decimal
- Description: The value when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Shutdown Value

- Type: Decimal
- Description: The value when Mycodo shuts down

##### Invert Signal

- Type: Boolean
- Description: Invert the PWM signal

##### Invert Stored Signal

- Type: Boolean
- Description: Invert the value that is saved to the measurement database

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Force Command

- Type: Boolean
- Description: Always send the command if instructed, regardless of the current state

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### Shell Script: On/Off

- Interfaces: Shell
- Output Types: On/Off
- Libraries: subprocess.Popen

Commands will be executed in the Linux shell by the specified user when this output is turned on or off.

#### Options

#### Channel Options

##### On Command

- Type: Text
- Default Value: /home/pi/script_on_off.sh on
- Description: Command to execute when the output is instructed to turn on

##### Off Command

- Type: Text
- Default Value: /home/pi/script_on_off.sh off
- Description: Command to execute when the output is instructed to turn off

##### User

- Type: Text
- Default Value: mycodo
- Description: The user to execute the command

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Force Command

- Type: Boolean
- Description: Always send the command if instructed, regardless of the current state

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### Shell Script: PWM

- Interfaces: Shell
- Output Types: PWM
- Libraries: subprocess.Popen

Commands will be executed in the Linux shell by the specified user when the duty cycle is set for this output. The string "((duty_cycle))" in the command will be replaced with the duty cycle being set prior to execution.

#### Options

#### Channel Options

##### Bash Command

- Type: Text
- Default Value: /home/pi/script_pwm.sh ((duty_cycle))
- Description: Command to execute to set the PWM duty cycle (%)

##### User

- Type: Text
- Default Value: mycodo
- Description: The user to execute the command

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Startup Value

- Type: Decimal
- Description: The value when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Shutdown Value

- Type: Decimal
- Description: The value when Mycodo shuts down

##### Invert Signal

- Type: Boolean
- Description: Invert the PWM signal

##### Invert Stored Signal

- Type: Boolean
- Description: Invert the value that is saved to the measurement database

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Force Command

- Type: Boolean
- Description: Always send the commad if instructed, regardless of the current state

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

### Spacer

- Interfaces: Mycodo

A spacer to organize Outputs.

#### Options

##### Color

- Type: Text
- Default Value: #000000
- Description: The color of the name text

### Stepper Motor: Bipolar, Generic

- Interfaces: GPIO
- Output Types: Value
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Manufacturer URLs: [Link 1](https://www.ti.com/product/DRV8825), [Link 2](https://www.allegromicro.com/en/products/motor-drivers/brush-dc-motor-drivers/a4988)
- Datasheet URLs: [Link 1](https://www.ti.com/lit/ds/symlink/drv8825.pdf), [Link 2](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.ashx)
- Product URLs: [Link 1](https://www.pololu.com/product/2133), [Link 2](https://www.pololu.com/product/1182)

This is a generic module for bipolar stepper motor drivers such as the DRV8825, A4988, and others. The value passed to the output is the number of steps. A positive value turns clockwise and a negative value turns counter-clockwise.

#### Options

#### Channel Options

##### If the Direction or Enable pins are not used, make sure you pull the appropriate pins on your driver high or low to set the proper direction and enable the stepper motor to be energized. Note: For Enable Mode, always having the motor energized will use more energy and produce more heat.

##### Step Pin

- Type: Integer
- Description: The Step pin of the controller (BCM numbering)

##### Full Step Delay

- Type: Decimal
- Default Value: 0.005
- Description: The Full Step Delay of the controller

##### Direction Pin

- Type: Integer
- Description: The Direction pin of the controller (BCM numbering). Set to None to disable.

##### Enable Pin

- Type: Integer
- Description: The Enable pin of the controller (BCM numbering). Set to None to disable.

##### Enable Mode

- Type: Select
- Options: \[**Only When Turning** | Always\] (Default in **bold**)
- Description: Choose when to pull the enable pin high to energize the motor.

##### Enable at Shutdown

- Type: Select
- Options: \[Enable | **Disable**\] (Default in **bold**)
- Description: Choose whether the enable pin in pulled high (Enable) or low (Disable) when Mycodo shuts down.

##### If using a Step Resolution other than Full, and all three Mode Pins are set, they will be set high (1) or how (0) according to the values in parentheses to the right of the selected Step Resolution, e.g. (Mode Pin 1, Mode Pin 2, Mode Pin 3).

##### Step Resolution

- Type: Select
- Options: \[**Full (modes 0, 0, 0)** | Half (modes 1, 0, 0) | 1/4 (modes 0, 1, 0) | 1/8 (modes 1, 1, 0) | 1/16 (modes 0, 0, 1) | 1/32 (modes 1, 0, 1)\] (Default in **bold**)
- Description: The Step Resolution of the controller

##### Mode Pin 1

- Type: Integer
- Description: The Mode Pin 1 of the controller (BCM numbering). Set to None to disable.

##### Mode Pin 2

- Type: Integer
- Description: The Mode Pin 2 of the controller (BCM numbering). Set to None to disable.

##### Mode Pin 3

- Type: Integer
- Description: The Mode Pin 3 of the controller (BCM numbering). Set to None to disable.

### Stepper Motor: Unipolar, ULN2003

- Manufacturer: STMicroelectronics
- Interfaces: GPIO
- Output Types: Value
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO), [rpimotorlib](https://pypi.org/project/rpimotorlib)
- Manufacturer URL: [Link](https://www.ti.com/product/ULN2003A)
- Datasheet URLs: [Link 1](https://www.electronicoscaldas.com/datasheet/ULN2003A-PCB.pdf), [Link 2](https://www.ti.com/lit/ds/symlink/uln2003a.pdf?ts=1617254568263&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FULN2003A)

This is a module for the ULN2003 driver.

#### Options

#### Channel Options

##### Notes about connecting the ULN2003...

##### Pin IN1

- Type: Integer
- Default Value: 18
- Description: The pin (BCM numbering) connected to IN1 of the ULN2003

##### Pin IN2

- Type: Integer
- Default Value: 23
- Description: The pin (BCM numbering) connected to IN2 of the ULN2003

##### Pin IN3

- Type: Integer
- Default Value: 24
- Description: The pin (BCM numbering) connected to IN3 of the ULN2003

##### Pin IN4

- Type: Integer
- Default Value: 25
- Description: The pin (BCM numbering) connected to IN4 of the ULN2003

##### Step Delay

- Type: Decimal
- Default Value: 0.001
- Description: The Step Delay of the controller

##### Notes about step resolution...

##### Step Resolution

- Type: Select
- Options: \[**Full** | Half | Wave\] (Default in **bold**)
- Description: The Step Resolution of the controller

### Wireless: 315/433 MHz

- Interfaces: GPIO
- Output Types: On/Off
- Libraries: rpi-rf
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO), [rpi_rf](https://pypi.org/project/rpi_rf)

This output uses a 315 or 433 MHz transmitter to turn wireless power outlets on or off. Run ~/Mycodo/mycodo/devices/wireless_rpi_rf.py with a receiver to discover the codes produced from your remote.

#### Options

#### Channel Options

##### GPIO Pin (BCM)

- Type: Integer
- Description: The pin to control the state of

##### On Command

- Type: Text
- Default Value: 22559
- Description: Command to execute when the output is instructed to turn on

##### Off Command

- Type: Text
- Default Value: 22558
- Description: Command to execute when the output is instructed to turn off

##### Protocol

- Type: Select
- Options: \[**1** | 2 | 3 | 4 | 5\] (Default in **bold**)
- Description: Wireless protocol

##### Pulse Length

- Type: Integer
- Default Value: 189
- Description: Wireless pulse length

##### Startup State

- Type: Select
- Description: Set the state when Mycodo starts

##### Shutdown State

- Type: Select
- Description: Set the state when Mycodo shuts down

##### Trigger Functions at Startup

- Type: Boolean
- Description: Whether to trigger functions when the output switches at startup

##### Force Command

- Type: Boolean
- Description: Always send the commad if instructed, regardless of the current state

##### Current (Amps)

- Type: Decimal
- Description: The current draw of the device being controlled

