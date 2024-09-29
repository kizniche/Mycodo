## Built-In Outputs (System)

### On/Off: MQTT Publish

- Manufacturer: Mycodo
- Interfaces: IP
- Output Types: On/Off
- Libraries: paho-mqtt
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)
- Additional URL: [Link](http://www.eclipse.org/paho/)

Publish "on" or "off" (or any other strings of your choosing) to an MQTT server.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Hostname</td><td>Text
- Default Value: localhost</td><td>The hostname of the MQTT server</td></tr><tr><td>Port</td><td>Integer
- Default Value: 1883</td><td>The port of the MQTT server</td></tr><tr><td>Topic</td><td>Text
- Default Value: paho/test/single</td><td>The topic to publish with</td></tr><tr><td>Keep Alive</td><td>Integer
- Default Value: 60</td><td>The keepalive timeout value for the client. Set to 0 to disable.</td></tr><tr><td>Client ID</td><td>Text
- Default Value: client_6GggcCon</td><td>Unique client ID for connecting to the MQTT server</td></tr><tr><td>On Payload</td><td>Text
- Default Value: on</td><td>The payload to send when turned on</td></tr><tr><td>Off Payload</td><td>Text
- Default Value: off</td><td>The payload to send when turned off</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr><tr><td>Use Login</td><td>Boolean</td><td>Send login credentials</td></tr><tr><td>Username</td><td>Text
- Default Value: user</td><td>Username for connecting to the server</td></tr><tr><td>Password</td><td>Text</td><td>Password for connecting to the server. Leave blank to disable.</td></tr><tr><td>Use Websockets</td><td>Boolean</td><td>Use websockets to connect to the server.</td></tr></tbody></table>

### PWM: MQTT Publish

- Manufacturer: Mycodo
- Output Types: PWM
- Libraries: paho-mqtt
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)
- Additional URL: [Link](http://www.eclipse.org/paho/)

Publish a PWM value to an MQTT server.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Hostname</td><td>Text
- Default Value: localhost</td><td>The hostname of the MQTT server</td></tr><tr><td>Port</td><td>Integer
- Default Value: 1883</td><td>The port of the MQTT server</td></tr><tr><td>Topic</td><td>Text
- Default Value: paho/test/single</td><td>The topic to publish with</td></tr><tr><td>Keep Alive</td><td>Integer
- Default Value: 60</td><td>The keepalive timeout value for the client. Set to 0 to disable.</td></tr><tr><td>Client ID</td><td>Text
- Default Value: client_tO6tBFpx</td><td>Unique client ID for connecting to the MQTT server</td></tr><tr><td>Use Login</td><td>Boolean</td><td>Send login credentials</td></tr><tr><td>Username</td><td>Text
- Default Value: user</td><td>Username for connecting to the server</td></tr><tr><td>Password</td><td>Text</td><td>Password for connecting to the server.</td></tr><tr><td>Use Websockets</td><td>Boolean</td><td>Use websockets to connect to the server.</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Startup Value</td><td>Decimal</td><td>The value when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Shutdown Value</td><td>Decimal</td><td>The value when Mycodo shuts down</td></tr><tr><td>Invert Signal</td><td>Boolean</td><td>Invert the PWM signal</td></tr><tr><td>Invert Stored Signal</td><td>Boolean</td><td>Invert the value that is saved to the measurement database</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Set the Duty Cycle.</td></tr><tr><td>Duty Cycle</td><td>Decimal</td><td>The duty cycle to set</td></tr><tr><td>Set Duty Cycle</td><td>Button</td><td></td></tr></tbody></table>

### Value: MQTT Publish

- Manufacturer: Mycodo
- Output Types: Value
- Libraries: paho-mqtt
- Dependencies: [paho-mqtt](https://pypi.org/project/paho-mqtt)
- Additional URL: [Link](http://www.eclipse.org/paho/)

Publish a value to an MQTT server.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Hostname</td><td>Text
- Default Value: localhost</td><td>The hostname of the MQTT server</td></tr><tr><td>Port</td><td>Integer
- Default Value: 1883</td><td>The port of the MQTT server</td></tr><tr><td>Topic</td><td>Text
- Default Value: paho/test/single</td><td>The topic to publish with</td></tr><tr><td>Keep Alive</td><td>Integer
- Default Value: 60</td><td>The keepalive timeout value for the client. Set to 0 to disable.</td></tr><tr><td>Client ID</td><td>Text
- Default Value: client_4ccOuIPc</td><td>Unique client ID for connecting to the MQTT server</td></tr><tr><td>Off Value</td><td>Integer</td><td>The value to send when an Off command is given</td></tr><tr><td>Use Login</td><td>Boolean</td><td>Send login credentials</td></tr><tr><td>Username</td><td>Text
- Default Value: user</td><td>Username for connecting to the server</td></tr><tr><td>Password</td><td>Text</td><td>Password for connecting to the server.</td></tr><tr><td>Use Websockets</td><td>Boolean</td><td>Use websockets to connect to the server.</td></tr></tbody></table>

## Built-In Outputs (Devices)

### Digital Potentiometer: DS3502

- Manufacturer: Maxim Integrated
- Interfaces: I<sup>2</sup>C
- Output Types: Value
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit_Extended_Bus](https://pypi.org/project/Adafruit_Extended_Bus), [adafruit-circuitpython-ds3502](https://pypi.org/project/adafruit-circuitpython-ds3502)
- Manufacturer URL: [Link](https://www.maximintegrated.com/en/products/analog/data-converters/digital-potentiometers/DS3502.html)
- Datasheet URL: [Link](https://datasheets.maximintegrated.com/en/ds/DS3502.pdf)
- Product URL: [Link](https://www.adafruit.com/product/4286)

The DS3502 can generate a 0 - 10k Ohm resistance with 7-bit precision. This equates to 128 possible steps. A value, in Ohms, is passed to this output controller and the step value is calculated and passed to the device. Select whether to round up or down to the nearest step.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td>Round Step</td><td>Select(Options: [<strong>Up</strong> | Down] (Default in <strong>bold</strong>)</td><td>Round direction to the nearest step value</td></tr></tbody></table>

### Digital-to-Analog Converter: MCP4728

- Manufacturer: MICROCHIP
- Interfaces: I<sup>2</sup>C
- Output Types: Value
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-mcp4728](https://pypi.org/project/adafruit-circuitpython-mcp4728)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/en541737)
- Datasheet URL: [Link](https://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf)
- Product URL: [Link](https://www.adafruit.com/product/4470)
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td>VREF (volts)</td><td>Decimal
- Default Value: 4.096</td><td>Set the VREF voltage</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>VREF</td><td>Select(Options: [<strong>Internal</strong> | VDD] (Default in <strong>bold</strong>)</td><td>Select the channel VREF</td></tr><tr><td>Gain</td><td>Select(Options: [<strong>1X</strong> | 2X] (Default in <strong>bold</strong>)</td><td>Select the channel Gain</td></tr><tr><td>Start State</td><td>Select(Options: [<strong>Previously-Saved State</strong> | Specified Value] (Default in <strong>bold</strong>)</td><td>Select the channel start state</td></tr><tr><td>Start Value (volts)</td><td>Decimal</td><td>If Specified Value is selected, set the start state value</td></tr><tr><td>Shutdown State</td><td>Select(Options: [<strong>Previously-Saved Value</strong> | Specified Value] (Default in <strong>bold</strong>)</td><td>Select the channel shutdown state</td></tr><tr><td>Shutdown Value (volts)</td><td>Decimal</td><td>If Specified Value is selected, set the shutdown state value</td></tr></tbody></table>

### Motor: Stepper Motor, Bipolar (Generic) (Pi <= 4)

- Interfaces: GPIO
- Output Types: Value
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Manufacturer URLs: [Link 1](https://www.ti.com/product/DRV8825), [Link 2](https://www.allegromicro.com/en/products/motor-drivers/brush-dc-motor-drivers/a4988)
- Datasheet URLs: [Link 1](https://www.ti.com/lit/ds/symlink/drv8825.pdf), [Link 2](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.ashx)
- Product URLs: [Link 1](https://www.pololu.com/product/2133), [Link 2](https://www.pololu.com/product/1182)

This is a generic module for bipolar stepper motor drivers such as the DRV8825, A4988, and others. The value passed to the output is the number of steps. A positive value turns clockwise and a negative value turns counter-clockwise.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td colspan="3">If the Direction or Enable pins are not used, make sure you pull the appropriate pins on your driver high or low to set the proper direction and enable the stepper motor to be energized. Note: For Enable Mode, always having the motor energized will use more energy and produce more heat.</td></tr><tr><td>Step Pin</td><td>Integer</td><td>The Step pin of the controller (BCM numbering)</td></tr><tr><td>Full Step Delay</td><td>Decimal
- Default Value: 0.005</td><td>The Full Step Delay of the controller</td></tr><tr><td>Direction Pin</td><td>Integer</td><td>The Direction pin of the controller (BCM numbering). Set to None to disable.</td></tr><tr><td>Enable Pin</td><td>Integer</td><td>The Enable pin of the controller (BCM numbering). Set to None to disable.</td></tr><tr><td>Enable Mode</td><td>Select(Options: [<strong>Only When Turning</strong> | Always] (Default in <strong>bold</strong>)</td><td>Choose when to pull the enable pin high to energize the motor.</td></tr><tr><td>Enable at Shutdown</td><td>Select(Options: [Enable | <strong>Disable</strong>] (Default in <strong>bold</strong>)</td><td>Choose whether the enable pin in pulled high (Enable) or low (Disable) when Mycodo shuts down.</td></tr><tr><td colspan="3">If using a Step Resolution other than Full, and all three Mode Pins are set, they will be set high (1) or how (0) according to the values in parentheses to the right of the selected Step Resolution, e.g. (Mode Pin 1, Mode Pin 2, Mode Pin 3).</td></tr><tr><td>Step Resolution</td><td>Select(Options: [<strong>Full (modes 0, 0, 0)</strong> | Half (modes 1, 0, 0) | 1/4 (modes 0, 1, 0) | 1/8 (modes 1, 1, 0) | 1/16 (modes 0, 0, 1) | 1/32 (modes 1, 0, 1)] (Default in <strong>bold</strong>)</td><td>The Step Resolution of the controller</td></tr><tr><td>Mode Pin 1</td><td>Integer</td><td>The Mode Pin 1 of the controller (BCM numbering). Set to None to disable.</td></tr><tr><td>Mode Pin 2</td><td>Integer</td><td>The Mode Pin 2 of the controller (BCM numbering). Set to None to disable.</td></tr><tr><td>Mode Pin 3</td><td>Integer</td><td>The Mode Pin 3 of the controller (BCM numbering). Set to None to disable.</td></tr></tbody></table>

### Motor: ULN2003 Stepper Motor, Unipolar (Pi <= 4)

- Manufacturer: STMicroelectronics
- Interfaces: GPIO
- Output Types: Value
- Libraries: RPi.GPIO, rpimotorlib
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO), [rpimotorlib](https://pypi.org/project/rpimotorlib)
- Manufacturer URL: [Link](https://www.ti.com/product/ULN2003A)
- Datasheet URLs: [Link 1](https://www.electronicoscaldas.com/datasheet/ULN2003A-PCB.pdf), [Link 2](https://www.ti.com/lit/ds/symlink/uln2003a.pdf?ts=1617254568263&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FULN2003A)

This is a module for the ULN2003 driver.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td colspan="3">Notes about connecting the ULN2003...</td></tr><tr><td>Pin IN1</td><td>Integer
- Default Value: 18</td><td>The pin (BCM numbering) connected to IN1 of the ULN2003</td></tr><tr><td>Pin IN2</td><td>Integer
- Default Value: 23</td><td>The pin (BCM numbering) connected to IN2 of the ULN2003</td></tr><tr><td>Pin IN3</td><td>Integer
- Default Value: 24</td><td>The pin (BCM numbering) connected to IN3 of the ULN2003</td></tr><tr><td>Pin IN4</td><td>Integer
- Default Value: 25</td><td>The pin (BCM numbering) connected to IN4 of the ULN2003</td></tr><tr><td>Step Delay</td><td>Decimal
- Default Value: 0.001</td><td>The Step Delay of the controller</td></tr><tr><td colspan="3">Notes about step resolution...</td></tr><tr><td>Step Resolution</td><td>Select(Options: [<strong>Full</strong> | Half | Wave] (Default in <strong>bold</strong>)</td><td>The Step Resolution of the controller</td></tr></tbody></table>

### On/Off: Grove Multichannel Relay (4- or 8-Channel board)

- Manufacturer: Grove
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.seeedstudio.com/Grove-4-Channel-SPDT-Relay-p-3119.html)
- Datasheet URL: [Link](http://wiki.seeedstudio.com/Grove-4-Channel_SPDT_Relay/)
- Product URL: [Link](https://www.seeedstudio.com/Grove-4-Channel-SPDT-Relay-p-3119.html)

Controls the 4 or 8 channel Grove multichannel relay board.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state of the relay when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state of the relay when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Kasa HS300 6-Outlet WiFi Power Strip (old library, deprecated)

- Manufacturer: TP-Link
- Interfaces: IP
- Output Types: On/Off
- Dependencies: [python-kasa](https://pypi.org/project/python-kasa)
- Manufacturer URL: [Link](https://www.kasasmart.com/us/products/smart-plugs/kasa-smart-wi-fi-power-strip-hs300)

This output controls the 6 outlets of the Kasa HS300 Smart WiFi Power Strip. This module uses an outdated python library and is deprecated. Do not use it. You will break the current Kasa modules if you do not delete this deprecated Output.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Host</td><td>Text
- Default Value: 192.168.0.50</td><td>Host or IP address</td></tr><tr><td>Status Update (Seconds)</td><td>Integer
- Default Value: 60</td><td>The period between checking if connected and output states.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text
- Default Value: Outlet Name</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Kasa HS300 6-Outlet WiFi Power Strip

- Manufacturer: TP-Link
- Interfaces: IP
- Output Types: On/Off
- Dependencies: [python-kasa](https://pypi.org/project/python-kasa), [aio_msgpack_rpc](https://pypi.org/project/aio_msgpack_rpc)
- Manufacturer URL: [Link](https://www.kasasmart.com/us/products/smart-plugs/kasa-smart-wi-fi-power-strip-hs300)

This output controls the 6 outlets of the Kasa HS300 Smart WiFi Power Strip. This is a variant that uses the latest python-kasa library. Note: if you see errors in the daemon log about the server starting, try changing the Asyncio RPC Port to another port.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Host</td><td>Text
- Default Value: 0.0.0.0</td><td>Host or IP address</td></tr><tr><td>Status Update (Seconds)</td><td>Integer
- Default Value: 300</td><td>The period between checking if connected and output states. 0 disables.</td></tr><tr><td>Asyncio RPC Port</td><td>Integer
- Default Value: 18308</td><td>The port to start the asyncio RPC server. Must be unique from other Kasa Outputs.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text
- Default Value: Outlet Name</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Kasa KP303 3-Outlet WiFi Power Strip (old library, deprecated)

- Manufacturer: TP-Link
- Interfaces: IP
- Output Types: On/Off
- Dependencies: [python-kasa](https://pypi.org/project/python-kasa)
- Manufacturer URL: [Link](https://www.tp-link.com/au/home-networking/smart-plug/kp303/)

This output controls the 3 outlets of the Kasa KP303 Smart WiFi Power Strip. This module uses an outdated python library and is deprecated. Do not use it. You will break the current Kasa modules if you do not delete this deprecated Output.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Host</td><td>Text
- Default Value: 192.168.0.50</td><td>Host or IP address</td></tr><tr><td>Status Update (Seconds)</td><td>Integer
- Default Value: 60</td><td>The period between checking if connected and output states.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text
- Default Value: Outlet Name</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Kasa KP303 3-Outlet WiFi Power Strip

- Manufacturer: TP-Link
- Interfaces: IP
- Output Types: On/Off
- Dependencies: [python-kasa](https://pypi.org/project/python-kasa), [aio_msgpack_rpc](https://pypi.org/project/aio_msgpack_rpc)
- Manufacturer URL: [Link](https://www.tp-link.com/au/home-networking/smart-plug/kp303/)

This output controls the 3 outlets of the Kasa KP303 Smart WiFi Power Strip. This is a variant that uses the latest python-kasa library. Note: if you see errors in the daemon log about the server starting, try changing the Asyncio RPC Port to another port.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Host</td><td>Text
- Default Value: 0.0.0.0</td><td>Host or IP address</td></tr><tr><td>Status Update (Seconds)</td><td>Integer
- Default Value: 300</td><td>The period between checking if connected and output states. 0 disables.</td></tr><tr><td>Asyncio RPC Port</td><td>Integer
- Default Value: 18575</td><td>The port to start the asyncio RPC server. Must be unique from other Kasa Outputs.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text
- Default Value: Outlet Name</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Kasa WiFi Power Plug

- Manufacturer: TP-Link
- Interfaces: IP
- Output Types: On/Off
- Dependencies: [python-kasa](https://pypi.org/project/python-kasa), [aio_msgpack_rpc](https://pypi.org/project/aio_msgpack_rpc)
- Manufacturer URL: [Link](https://www.kasasmart.com/us/products/smart-plugs/kasa-smart-plug-slim-energy-monitoring-kp115)

This output controls Kasa WiFi Power Plugs, including the KP105, KP115, KP125, KP401, HS100, HS103, HS105, HS107, and HS110. Note: if you see errors in the daemon log about the server starting, try changing the Asyncio RPC Port to another port.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Host</td><td>Text
- Default Value: 0.0.0.0</td><td>Host or IP address</td></tr><tr><td>Status Update (Seconds)</td><td>Integer
- Default Value: 300</td><td>The period between checking if connected and output states. 0 disables.</td></tr><tr><td>Asyncio RPC Port</td><td>Integer
- Default Value: 18331</td><td>The port to start the asyncio RPC server. Must be unique from other Kasa Outputs.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Kasa WiFi RGB Light Bulb

- Manufacturer: TP-Link
- Interfaces: IP
- Output Types: On/Off
- Dependencies: [python-kasa](https://pypi.org/project/python-kasa), [aio_msgpack_rpc](https://pypi.org/project/aio_msgpack_rpc)
- Manufacturer URL: [Link](https://www.kasasmart.com/us/products/smart-lighting/kasa-smart-light-bulb-multicolor-kl125)

This output controls the the Kasa WiFi Light Bulbs, including the KL125, KL130, and KL135. Note: if you see errors in the daemon log about the server starting, try changing the Asyncio RPC Port to another port.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Host</td><td>Text
- Default Value: 0.0.0.0</td><td>Host or IP address</td></tr><tr><td>Status Update (Seconds)</td><td>Integer
- Default Value: 300</td><td>The period between checking if connected and output states. 0 disables.</td></tr><tr><td>Asyncio RPC Port</td><td>Integer
- Default Value: 18299</td><td>The port to start the asyncio RPC server. Must be unique from other Kasa Outputs.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr><tr><td colspan="3">Commands</td></tr><tr><td>Transition (Milliseconds)</td><td>Integer
- Default Value: 0</td><td>The hsv transition period</td></tr><tr><td>Brightness (Percent)</td><td>Integer</td><td>The brightness to set, in percent (0 - 100)</td></tr><tr><td>Set</td><td>Button</td><td></td></tr><tr><td>Transition (Milliseconds)</td><td>Integer
- Default Value: 0</td><td>The hsv transition period</td></tr><tr><td>Hue (Degree)</td><td>Integer</td><td>The hue to set, in degrees (0 - 360)</td></tr><tr><td>Set</td><td>Button</td><td></td></tr><tr><td>Transition (Milliseconds)</td><td>Integer
- Default Value: 0</td><td>The hsv transition period</td></tr><tr><td>Saturation (Percent)</td><td>Integer</td><td>The saturation to set, in percent (0 - 100)</td></tr><tr><td>Set</td><td>Button</td><td></td></tr><tr><td>Transition (Milliseconds)</td><td>Integer
- Default Value: 0</td><td>The hsv transition period</td></tr><tr><td>Color Temperature (Kelvin)</td><td>Integer</td><td>The color temperature to set, in degrees Kelvin</td></tr><tr><td>Set</td><td>Button</td><td></td></tr><tr><td>Transition (Milliseconds)</td><td>Integer
- Default Value: 0</td><td>The hsv transition period</td></tr><tr><td>HSV</td><td>Text
- Default Value: 220, 20, 45</td><td>The hue, saturation, brightness to set, e.g. "200, 20, 50"</td></tr><tr><td>Set</td><td>Button</td><td></td></tr><tr><td>Transition (Milliseconds)</td><td>Integer
- Default Value: 1000</td><td>The transition period</td></tr><tr><td>On</td><td>Button</td><td></td></tr><tr><td>Transition (Milliseconds)</td><td>Integer
- Default Value: 1000</td><td>The transition period</td></tr><tr><td>Off</td><td>Button</td><td></td></tr></tbody></table>

### On/Off: MCP23017 16-Channel I/O Expander

- Manufacturer: MICROCHIP
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-mcp230xx](https://pypi.org/project/adafruit-circuitpython-mcp230xx)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/MCP23017)
- Datasheet URL: [Link](https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf)
- Product URL: [Link](https://www.amazon.com/Waveshare-MCP23017-Expansion-Interface-Expands/dp/B07P2H1NZG)

Controls the 16 channels of the MCP23017.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state of the GPIO when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state of the GPIO when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Neopixel (WS2812) RGB Strip with Raspberry Pi

- Manufacturer: Worldsemi
- Interfaces: GPIO
- Output Types: On/Off
- Dependencies: Output Variant 1: [adafruit-circuitpython-neopixel](https://pypi.org/project/adafruit-circuitpython-neopixel); Output Variant 2: [adafruit-circuitpython-neopixel-spi](https://pypi.org/project/adafruit-circuitpython-neopixel-spi)

Control the LEDs of a neopixel light strip. USE WITH CAUTION: This library uses the Hardware-PWM0 bus. Only GPIO pins 12 or 18 will work. If you use one of these pins for a NeoPixel strip, you can not use the other for Hardware-PWM control of another output or there will be conflicts that can cause the Mycodo Daemon to crash and the Pi to become unresponsive. If you need to control another PWM output like a servo, fan, or dimmable grow lights, you will need to use the Software-PWM by setting the Output PWM: Raspberry Pi GPIO and set the "Library" field to "Any Pin, <=40kHz". If you select the "Hardware Pin, <=30MHz" option, it will cause conflicts. This output is best used with Actions to control individual LED color and brightness.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Data Pin</td><td>Integer
- Default Value: 18</td><td>Enter the GPIO Pin connected to your device data wire (BCM numbering).</td></tr><tr><td>Number of LEDs</td><td>Integer
- Default Value: 1</td><td>How many LEDs in the string?</td></tr><tr><td>On Mode</td><td>Select(Options: [<strong>Single Color</strong> | Rainbow] (Default in <strong>bold</strong>)</td><td>The color mode when turned on</td></tr><tr><td>Single Color</td><td>Text
- Default Value: 30, 30, 30</td><td>The Color when turning on in Single Color Mode, RGB format (red, green, blue), 0 - 255 each.</td></tr><tr><td>Rainbow Speed (Seconds)</td><td>Decimal
- Default Value: 0.01</td><td>The speed to change colors in Rainbow Mode</td></tr><tr><td>Rainbow Brightness</td><td>Integer
- Default Value: 20</td><td>The maximum brightness of LEDs in Rainbow Mode (1 - 255)</td></tr><tr><td>Rainbow Mode</td><td>Select(Options: [All LEDs change at once | <strong>One LED Changes at a time</strong>] (Default in <strong>bold</strong>)</td><td>How the rainbow is displayed</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td colspan="3">Commands</td></tr><tr><td>LED Position</td><td>Integer</td><td>Which LED in the strip to change</td></tr><tr><td>RGB Color</td><td>Text
- Default Value: 10, 0, 0</td><td>The color (e.g 10, 0, 0)</td></tr><tr><td>Set</td><td>Button</td><td></td></tr></tbody></table>

### On/Off: PCF8574 8-Channel I/O Expander

- Manufacturer: Texas Instruments
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.ti.com/product/PCF8574)
- Datasheet URL: [Link](https://www.ti.com/lit/ds/symlink/pcf8574.pdf)
- Product URL: [Link](https://www.amazon.com/gp/product/B07JGSNWFF)

Controls the 8 channels of the PCF8574.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state of the GPIO when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state of the GPIO when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: PCF8575 16-Channel I/O Expander

- Manufacturer: Texas Instruments
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.ti.com/product/PCF8575)
- Datasheet URL: [Link](https://www.ti.com/lit/ds/symlink/pcf8575.pdf)
- Product URL: [Link](https://www.amazon.com/gp/product/B07JGSNWFF)

Controls the 16 channels of the PCF8575.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state of the GPIO when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state of the GPIO when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Python Code

- Interfaces: Python
- Output Types: On/Off
- Dependencies: [pylint](https://pypi.org/project/pylint)

Python 3 code will be executed when this output is turned on or off.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Analyze Python Code with Pylint</td><td>Boolean
- Default Value: True</td><td>Analyze your Python code with pylint when saving</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>On Command</td></td><td>Python code to execute when the output is instructed to turn on</td></tr><tr><td>Off Command</td></td><td>Python code to execute when the output is instructed to turn off</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Raspberry Pi GPIO (Pi 5)

- Interfaces: GPIO
- Output Types: On/Off
- Libraries: pinctrl

The specified GPIO pin will be set HIGH (3.3 volts) or LOW (0 volts) when turned on or off, depending on the On State option.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Pin: GPIO (BCM)</td><td>Integer</td><td>The pin to control the state of</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Raspberry Pi GPIO (Pi <= 4)

- Interfaces: GPIO
- Output Types: On/Off
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

The specified GPIO pin will be set HIGH (3.3 volts) or LOW (0 volts) when turned on or off, depending on the On State option.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Pin: GPIO (BCM)</td><td>Integer</td><td>The pin to control the state of</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Sequent Microsystems 8-Relay HAT for Raspberry Pi

- Manufacturer: Sequent Microsystems
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://sequentmicrosystems.com)
- Datasheet URL: [Link](https://cdn.shopify.com/s/files/1/0534/4392/0067/files/8-RELAYS-UsersGuide.pdf?v=1642820552)
- Product URL: [Link](https://sequentmicrosystems.com/products/8-relays-stackable-card-for-raspberry-pi)

Controls the 8 relays of the 8-relay HAT made by Sequent Microsystems. 8 of these boards can be used simultaneously, allowing 64 relays to be controlled.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td>Board Stack Number</td><td>Select</td><td>Select the board stack number when multiple boards are used</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state of the GPIO when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state of the GPIO when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Shell Script

- Output Types: On/Off
- Libraries: subprocess.Popen

Commands will be executed in the Linux shell by the specified user when this output is turned on or off.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>On Command</td><td>Text
- Default Value: /home/pi/script_on_off.sh on</td><td>Command to execute when the output is instructed to turn on</td></tr><tr><td>Off Command</td><td>Text
- Default Value: /home/pi/script_on_off.sh off</td><td>Command to execute when the output is instructed to turn off</td></tr><tr><td>User</td><td>Text
- Default Value: mycodo</td><td>The user to execute the command</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Sparkfun Relay Board (4 Relays)

- Manufacturer: Sparkfun
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: sparkfun-qwiic-relay
- Dependencies: [sparkfun-qwiic-relay](https://pypi.org/project/sparkfun-qwiic-relay)
- Manufacturer URL: [Link](https://www.sparkfun.com)
- Product URLs: [Link 1](https://www.sparkfun.com/products/16833), [Link 2](https://www.sparkfun.com/products/16566)

Controls the 4 relays of the relay module.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state of the GPIO when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state of the GPIO when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: Wireless 315/433 MHz (Pi <= 4)

- Interfaces: GPIO
- Output Types: On/Off
- Libraries: rpi-rf
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO), [rpi_rf](https://pypi.org/project/rpi_rf)

This output uses a 315 or 433 MHz transmitter to turn wireless power outlets on or off. Run /opt/Mycodo/mycodo/devices/wireless_rpi_rf.py with a receiver to discover the codes produced from your remote.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Pin: GPIO (BCM)</td><td>Integer</td><td>The pin to control the state of</td></tr><tr><td>On Command</td><td>Text
- Default Value: 22559</td><td>Command to execute when the output is instructed to turn on</td></tr><tr><td>Off Command</td><td>Text
- Default Value: 22558</td><td>Command to execute when the output is instructed to turn off</td></tr><tr><td>Protocol</td><td>Select(Options: [<strong>1</strong> | 2 | 3 | 4 | 5] (Default in <strong>bold</strong>)</td><td></td></tr><tr><td>Pulse Length</td><td>Integer
- Default Value: 189</td><td></td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### On/Off: XL9535 16-Channel I/O Expander

- Manufacturer: Texas Instruments
- Interfaces: I<sup>2</sup>C
- Output Types: On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link]()
- Datasheet URL: [Link]()
- Product URL: [Link]()

Controls the 16 channels of the XL9535.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state of the GPIO when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state of the GPIO when Mycodo shuts down</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### PWM: PCA9685 16-Channel LED Controller

- Manufacturer: NXP Semiconductors
- Interfaces: I<sup>2</sup>C
- Output Types: PWM
- Libraries: adafruit-pca9685
- Dependencies: [adafruit-pca9685](https://pypi.org/project/adafruit-pca9685)
- Manufacturer URL: [Link](https://www.nxp.com/products/power-management/lighting-driver-and-controller-ics/ic-led-controllers/16-channel-12-bit-pwm-fm-plus-ic-bus-led-controller:PCA9685)
- Datasheet URL: [Link](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf)
- Product URL: [Link](https://www.adafruit.com/product/815)

The PCA9685 can output a PWM signal to 16 channels at a frequency between 40 and 1600 Hz.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td>Frequency (Hertz)</td><td>Integer
- Default Value: 1600</td><td>The Herts to output the PWM signal (40 - 1600)</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Startup Value</td><td>Decimal</td><td>The value when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Shutdown Value</td><td>Decimal</td><td>The value when Mycodo shuts down</td></tr><tr><td>Invert Signal</td><td>Boolean</td><td>Invert the PWM signal</td></tr><tr><td>Invert Stored Signal</td><td>Boolean</td><td>Invert the value that is saved to the measurement database</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### PWM: Python 3 Code

- Interfaces: Python
- Output Types: PWM
- Dependencies: [pylint](https://pypi.org/project/pylint)

Python 3 code will be executed when this output is turned on or off. The "duty_cycle" object is a float value that represents the duty cycle that has been set.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Analyze Python Code with Pylint</td><td>Boolean
- Default Value: True</td><td>Analyze your Python code with pylint when saving</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Python 3 Code</td></td><td>Python code to execute to set the PWM duty cycle (%)</td></tr><tr><td>User</td><td>Text
- Default Value: mycodo</td><td>The user to execute the command</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Startup Value</td><td>Decimal</td><td>The value when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Shutdown Value</td><td>Decimal</td><td>The value when Mycodo shuts down</td></tr><tr><td>Invert Signal</td><td>Boolean</td><td>Invert the PWM signal</td></tr><tr><td>Invert Stored Signal</td><td>Boolean</td><td>Invert the value that is saved to the measurement database</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Set the Duty Cycle.</td></tr><tr><td>Duty Cycle</td><td>Decimal</td><td>The duty cycle to set</td></tr><tr><td>Set Duty Cycle</td><td>Button</td><td></td></tr></tbody></table>

### PWM: Raspberry Pi GPIO (Pi <= 4)

- Interfaces: GPIO
- Output Types: PWM
- Libraries: pigpio
- Dependencies: pigpio, [pigpio](https://pypi.org/project/pigpio)

See the PWM section of the manual for PWM information and determining which pins may be used for each library option.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Pin: GPIO (BCM)</td><td>Integer</td><td>The pin to control the state of</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Startup Value</td><td>Decimal</td><td>The value when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Shutdown Value</td><td>Decimal</td><td>The value when Mycodo shuts down</td></tr><tr><td>Library</td><td>Select(Options: [<strong>Any Pin, <= 40 kHz</strong> | Hardware Pin, <= 30 MHz] (Default in <strong>bold</strong>)</td><td>Which method to produce the PWM signal (hardware pins can produce higher frequencies)</td></tr><tr><td>Frequency (Hertz)</td><td>Integer
- Default Value: 22000</td><td>The Herts to output the PWM signal (0 - 70,000)</td></tr><tr><td>Invert Signal</td><td>Boolean</td><td>Invert the PWM signal</td></tr><tr><td>Invert Stored Signal</td><td>Boolean</td><td>Invert the value that is saved to the measurement database</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Set the Duty Cycle.</td></tr><tr><td>Duty Cycle</td><td>Decimal</td><td>The duty cycle to set</td></tr><tr><td>Set Duty Cycle</td><td>Button</td><td></td></tr></tbody></table>

### PWM: Shell Script

- Interfaces: Shell
- Output Types: PWM
- Libraries: subprocess.Popen

Commands will be executed in the Linux shell by the specified user when the duty cycle is set for this output. The string "((duty_cycle))" in the command will be replaced with the duty cycle being set prior to execution.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Bash Command</td><td>Text
- Default Value: /home/pi/script_pwm.sh ((duty_cycle))</td><td>Command to execute to set the PWM duty cycle (%)</td></tr><tr><td>User</td><td>Text
- Default Value: mycodo</td><td>The user to execute the command</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Startup Value</td><td>Decimal</td><td>The value when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Shutdown Value</td><td>Decimal</td><td>The value when Mycodo shuts down</td></tr><tr><td>Invert Signal</td><td>Boolean</td><td>Invert the PWM signal</td></tr><tr><td>Invert Stored Signal</td><td>Boolean</td><td>Invert the value that is saved to the measurement database</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### Peristaltic Pump: Atlas Scientific

- Manufacturer: Atlas Scientific
- Interfaces: I<sup>2</sup>C, UART, FTDI
- Output Types: Volume, On/Off
- Dependencies: [pylibftdi](https://pypi.org/project/pylibftdi)
- Manufacturer URL: [Link](https://atlas-scientific.com/peristaltic/)
- Datasheet URL: [Link](https://www.atlas-scientific.com/files/EZO_PMP_Datasheet.pdf)
- Product URL: [Link](https://atlas-scientific.com/peristaltic/ezo-pmp/)

Atlas Scientific peristaltic pumps can be set to dispense at their maximum rate or a rate can be specified. Their minimum flow rate is 0.5 ml/min and their maximum is 105 ml/min.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td>FTDI Device</td><td>Text</td><td>The FTDI device connected to the input/output/etc.</td></tr><tr><td>UART Device</td><td>Text</td><td>The UART device location (e.g. /dev/ttyUSB1)</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Flow Rate Method</td><td>Select(Options: [<strong>Fastest Flow Rate</strong> | Specify Flow Rate] (Default in <strong>bold</strong>)</td><td>The flow rate to use when pumping a volume</td></tr><tr><td>Desired Flow Rate (ml/min)</td><td>Decimal
- Default Value: 10.0</td><td>Desired flow rate in ml/minute when Specify Flow Rate set</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Calibration: a calibration can be performed to increase the accuracy of the pump. It's a good idea to clear the calibration before calibrating. First, remove all air from the line by pumping the fluid you would like to calibrate to through the pump hose. Next, press Dispense Amount and the pump will be instructed to dispense 10 ml (unless you changed the default value). Measure how much fluid was actually dispensed, enter this value in the Actual Volume Dispensed (ml) field, and press Calibrate to Dispensed Amount. Now any further pump volumes dispensed should be accurate.</td></tr><tr><td>Clear Calibration</td><td>Button</td><td></td></tr><tr><td>Volume to Dispense (ml)</td><td>Decimal
- Default Value: 10.0</td><td>The volume (ml) that is instructed to be dispensed</td></tr><tr><td>Dispense Amount</td><td>Button</td><td></td></tr><tr><td>Actual Volume Dispensed (ml)</td><td>Decimal
- Default Value: 10.0</td><td>The actual volume (ml) that was dispensed</td></tr><tr><td>Calibrate to Dispensed Amount</td><td>Button</td><td></td></tr><tr><td colspan="3">The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address.</td></tr><tr><td>New I2C Address</td><td>Text
- Default Value: 0x67</td><td>The new I2C to set the device to</td></tr><tr><td>Set I2C Address</td><td>Button</td><td></td></tr></tbody></table>

### Peristaltic Pump: Grove I2C Motor Driver (Board v1.3)

- Manufacturer: Grove
- Interfaces: I<sup>2</sup>C
- Output Types: Volume, On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://wiki.seeedstudio.com/Grove-I2C_Motor_Driver_V1.3)

Controls the Grove I2C Motor Driver Board (v1.3). Both motors will turn at the same time. This output can also dispense volumes of fluid if the motors are attached to peristaltic pumps.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Motor Speed (0 - 100)</td><td>Integer
- Default Value: 100</td><td>The motor output that determines the speed</td></tr><tr><td>Flow Rate Method</td><td>Select(Options: [<strong>Fastest Flow Rate</strong> | Specify Flow Rate] (Default in <strong>bold</strong>)</td><td>The flow rate to use when pumping a volume</td></tr><tr><td>Desired Flow Rate (ml/min)</td><td>Decimal
- Default Value: 10.0</td><td>Desired flow rate in ml/minute when Specify Flow Rate set</td></tr><tr><td>Fastest Rate (ml/min)</td><td>Decimal
- Default Value: 100.0</td><td>The fastest rate that the pump can dispense (ml/min)</td></tr></tbody></table>

### Peristaltic Pump: Grove I2C Motor Driver (TB6612FNG, Board v1.0)

- Manufacturer: Grove
- Interfaces: I<sup>2</sup>C
- Output Types: Volume, On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://wiki.seeedstudio.com/Grove-I2C_Motor_Driver-TB6612FNG)

Controls the Grove I2C Motor Driver Board (v1.3). Both motors will turn at the same time. This output can also dispense volumes of fluid if the motors are attached to peristaltic pumps.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Motor Speed (0 - 255)</td><td>Integer
- Default Value: 255</td><td>The motor output that determines the speed</td></tr><tr><td>Flow Rate Method</td><td>Select(Options: [<strong>Fastest Flow Rate</strong> | Specify Flow Rate] (Default in <strong>bold</strong>)</td><td>The flow rate to use when pumping a volume</td></tr><tr><td>Desired Flow Rate (ml/min)</td><td>Decimal
- Default Value: 10.0</td><td>Desired flow rate in ml/minute when Specify Flow Rate set</td></tr><tr><td>Fastest Rate (ml/min)</td><td>Decimal
- Default Value: 100.0</td><td>The fastest rate that the pump can dispense (ml/min)</td></tr><tr><td>Minimum On (Seconds)</td><td>Decimal
- Default Value: 1.0</td><td>The minimum duration the pump turns on for every 60 second period (only used for Specify Flow Rate mode).</td></tr><tr><td colspan="3">Commands</td></tr><tr><td>New I2C Address</td><td>Text
- Default Value: 0x14</td><td>The new I2C to set the sensor to</td></tr><tr><td>Set I2C Address</td><td>Button</td><td></td></tr></tbody></table>

### Peristaltic Pump: L298N DC Motor Controller (Pi <= 4)

- Manufacturer: STMicroelectronics
- Interfaces: GPIO
- Output Types: Volume, On/Off
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
- Additional URL: [Link](https://www.electronicshub.org/raspberry-pi-l298n-interface-tutorial-control-dc-motor-l298n-raspberry-pi/)

The L298N can control 2 DC motors, both speed and direction. If these motors control peristaltic pumps, set the Flow Rate and the output can can be instructed to dispense volumes accurately in addition to being turned on for durations.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>Input Pin 1</td><td>Integer</td><td>The Input Pin 1 of the controller (BCM numbering)</td></tr><tr><td>Input Pin 2</td><td>Integer</td><td>The Input Pin 2 of the controller (BCM numbering)</td></tr><tr><td>Use Enable Pin</td><td>Boolean
- Default Value: True</td><td>Enable the use of the Enable Pin</td></tr><tr><td>Enable Pin</td><td>Integer</td><td>The Enable pin of the controller (BCM numbering)</td></tr><tr><td>Enable Pin Duty Cycle</td><td>Integer
- Default Value: 50</td><td>The duty cycle to apply to the Enable Pin (percent, 1 - 100)</td></tr><tr><td>Direction</td><td>Select(Options: [<strong>Forward</strong> | Backward] (Default in <strong>bold</strong>)</td><td>The direction to turn the motor</td></tr><tr><td>Volume Rate (ml/min)</td><td>Decimal
- Default Value: 150.0</td><td>If a pump, the measured flow rate (ml/min) at the set Duty Cycle</td></tr></tbody></table>

### Peristaltic Pump: MCP23017 16-Channel I/O Expander

- Manufacturer: MICROCHIP
- Interfaces: I<sup>2</sup>C
- Output Types: Volume, On/Off
- Dependencies: [pyusb](https://pypi.org/project/pyusb), [Adafruit-extended-bus](https://pypi.org/project/Adafruit-extended-bus), [adafruit-circuitpython-mcp230xx](https://pypi.org/project/adafruit-circuitpython-mcp230xx)
- Manufacturer URL: [Link](https://www.microchip.com/wwwproducts/en/MCP23017)
- Datasheet URL: [Link](https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf)
- Product URL: [Link](https://www.amazon.com/Waveshare-MCP23017-Expansion-Interface-Expands/dp/B07P2H1NZG)

Controls the 16 channels of the MCP23017 with a relay and peristaltic pump connected to each channel.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Name</td><td>Text</td><td>A name to distinguish this from others</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the output channel that corresponds to the pump being on</td></tr><tr><td>Fastest Rate (ml/min)</td><td>Decimal
- Default Value: 150.0</td><td>The fastest rate that the pump can dispense (ml/min)</td></tr><tr><td>Minimum On (Seconds)</td><td>Decimal
- Default Value: 1.0</td><td>The minimum duration the pump should be turned on for every 60 second period</td></tr><tr><td>Flow Rate Method</td><td>Select(Options: [<strong>Fastest Flow Rate</strong> | Specify Flow Rate] (Default in <strong>bold</strong>)</td><td>The flow rate to use when pumping a volume</td></tr><tr><td>Desired Flow Rate (ml/min)</td><td>Decimal
- Default Value: 10.0</td><td>Desired flow rate in ml/minute when Specify Flow Rate set</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### Peristaltic Pump: PCF8574 8-Channel I/O Expander

- Manufacturer: Texas Instruments
- Interfaces: I<sup>2</sup>C
- Output Types: Volume, On/Off
- Libraries: smbus2
- Dependencies: [smbus2](https://pypi.org/project/smbus2)
- Manufacturer URL: [Link](https://www.ti.com/product/PCF8574)
- Datasheet URL: [Link](https://www.ti.com/lit/ds/symlink/pcf8574.pdf)
- Product URL: [Link](https://www.amazon.com/gp/product/B07JGSNWFF)

Controls the 8 channels of the PCF8574 with a relay and peristaltic pump connected to each channel.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the output channel that corresponds to the pump being on</td></tr><tr><td>Fastest Rate (ml/min)</td><td>Decimal
- Default Value: 150.0</td><td>The fastest rate that the pump can dispense (ml/min)</td></tr><tr><td>Minimum On (Seconds)</td><td>Decimal
- Default Value: 1.0</td><td>The minimum duration the pump should be turned on for every 60 second period</td></tr><tr><td>Flow Rate Method</td><td>Select(Options: [<strong>Fastest Flow Rate</strong> | Specify Flow Rate] (Default in <strong>bold</strong>)</td><td>The flow rate to use when pumping a volume</td></tr><tr><td>Desired Flow Rate (ml/min)</td><td>Decimal
- Default Value: 10.0</td><td>Desired flow rate in ml/minute when Specify Flow Rate set</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### Peristaltic Pump: Raspberry Pi GPIO (Pi <= 4)

- Interfaces: GPIO
- Output Types: Volume, On/Off
- Libraries: RPi.GPIO
- Dependencies: [RPi.GPIO](https://pypi.org/project/RPi.GPIO)

This output turns a GPIO pin HIGH and LOW to control power to a generic peristaltic pump. The peristaltic pump can then be turned on for a duration or, after determining the pump's maximum flow rate, instructed to dispense a specific volume at the maximum rate or at a specified rate.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td colspan="3">Channel Options</td></tr><tr><td>Pin: GPIO (BCM)</td><td>Integer</td><td>The pin to control the state of</td></tr><tr><td>On State</td><td>Select(Options: [<strong>HIGH</strong> | LOW] (Default in <strong>bold</strong>)</td><td>The state of the GPIO that corresponds to an On state</td></tr><tr><td>Fastest Rate (ml/min)</td><td>Decimal
- Default Value: 150.0</td><td>The fastest rate that the pump can dispense (ml/min)</td></tr><tr><td>Minimum On (Seconds)</td><td>Decimal
- Default Value: 1.0</td><td>The minimum duration the pump should be turned on for every 60 second period</td></tr><tr><td>Flow Rate Method</td><td>Select(Options: [<strong>Fastest Flow Rate</strong> | Specify Flow Rate] (Default in <strong>bold</strong>)</td><td>The flow rate to use when pumping a volume</td></tr><tr><td>Desired Flow Rate (ml/min)</td><td>Decimal
- Default Value: 10.0</td><td>Desired flow rate in ml/minute when Specify Flow Rate set</td></tr><tr><td>Current (Amps)</td><td>Decimal</td><td>The current draw of the device being controlled</td></tr></tbody></table>

### Remote Mycodo Output: On/Off

- Interfaces: API
- Output Types: On/Off
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)

This Output allows remote control of another Mycodo On/Off Output over a network using the API.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Remote Mycodo Host</td><td>Text</td><td>The host or IP address of the remote Mycodo</td></tr><tr><td>Remote Mycodo API Key</td><td>Text</td><td>The API key of the remote Mycodo</td></tr><tr><td>State Query Period (Seconds)</td><td>Integer
- Default Value: 120</td><td>How often to query the state of the output</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Remote Mycodo Output</td></td><td>The Remote Mycodo Output to control</td></tr><tr><td>Startup State</td><td>Select(Options: [<strong>Do Nothing</strong> | Off | On] (Default in <strong>bold</strong>)</td><td>Set the state when Mycodo starts</td></tr><tr><td>Shutdown State</td><td>Select(Options: [<strong>Do Nothing</strong> | Off | On] (Default in <strong>bold</strong>)</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Force Command</td><td>Boolean</td><td>Always send the command if instructed, regardless of the current state</td></tr><tr><td>Trigger Functions at Startup</td><td>Boolean</td><td>Whether to trigger functions when the output switches at startup</td></tr></tbody></table>

### Remote Mycodo Output: PWM

- Interfaces: API
- Output Types: PWM
- Libraries: requests
- Dependencies: [requests](https://pypi.org/project/requests)

This Output allows remote control of another Mycodo PWM Output over a network using the API.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Remote Mycodo Host</td><td>Text</td><td>The host or IP address of the remote Mycodo</td></tr><tr><td>Remote Mycodo API Key</td><td>Text</td><td>The API key of the remote Mycodo</td></tr><tr><td>State Query Period (Seconds)</td><td>Integer
- Default Value: 120</td><td>How often to query the state of the output</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Remote Mycodo Output</td></td><td>The Remote Mycodo Output to control</td></tr><tr><td>Startup State</td><td>Select</td><td>Set the state when Mycodo starts</td></tr><tr><td>Start Duty Cycle</td><td>Decimal</td><td>The duty cycle to set at startup, if enabled</td></tr><tr><td>Shutdown State</td><td>Select</td><td>Set the state when Mycodo shuts down</td></tr><tr><td>Shutdown Duty Cycle</td><td>Decimal</td><td>The duty cycle to set at shutdown, if enabled</td></tr><tr><td>Invert Signal</td><td>Boolean</td><td>Invert the PWM signal</td></tr><tr><td>Invert Stored Signal</td><td>Boolean</td><td>Invert the value that is saved to the measurement database</td></tr><tr><td colspan="3">Commands</td></tr><tr><td colspan="3">Set the Duty Cycle.</td></tr><tr><td>Duty Cycle</td><td>Decimal</td><td>The duty cycle to set</td></tr><tr><td>Set Duty Cycle</td><td>Button</td><td></td></tr></tbody></table>

### Spacer


A spacer to organize Outputs.
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>Color</td><td>Text
- Default Value: #000000</td><td>The color of the name text</td></tr></tbody></table>

### Value: GP8XXX (8413, 8403) 2-Channel DAC: 0-10 VDC

- Manufacturer: DFRobot
- Interfaces: I<sup>2</sup>C
- Output Types: Value
- Libraries: GP8XXX-IIC
- Dependencies: [smbus2](https://pypi.org/project/smbus2), [GP8XXX-IIC](https://pypi.org/project/GP8XXX-IIC)
- Datasheet URLs: [Link 1](https://wiki.dfrobot.com/SKU_DFR0971_2_Channel_I2C_0_10V_DAC_Module), [Link 2](https://wiki.dfrobot.com/SKU_DFR1073_2_Channel_15bit_I2C_to_0-10V_DAC)
- Product URLs: [Link 1](https://www.dfrobot.com/product-2613.html), [Link 2](https://www.dfrobot.com/product-2756.html)

Output 0 to 10 VDC signal.                GP8403: 12bit DAC Dual Channel I2C to 0-5V/0-10V |                GP8413: 15bit DAC Dual Channel I2C to 0-10V
<table><thead><tr class="header"><th>Option</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>I<sup>2</sup>C Address</td><td>Text</td><td>The address of the I<sup>2</sup>C device.</td></tr><tr><td>I<sup>2</sup>C Bus</td><td>Integer</td><td>The Bus the I<sup>2</sup>C device is connected.</td></tr><tr><td>Device</td><td>Select(Options: [<strong>GP8403 12-bit</strong> | GP8413 15-bit] (Default in <strong>bold</strong>)</td><td>Select your GP8XXX device</td></tr><tr><td colspan="3">Channel Options</td></tr><tr><td>Start State</td><td>Select(Options: [Previously-Saved State | <strong>Specified Value</strong>] (Default in <strong>bold</strong>)</td><td>Select the channel start state</td></tr><tr><td>Start Value (volts)</td><td>Decimal</td><td>If Specified Value is selected, set the start state value</td></tr><tr><td>Shutdown State</td><td>Select(Options: [Previously-Saved Value | <strong>Specified Value</strong>] (Default in <strong>bold</strong>)</td><td>Select the channel shutdown state</td></tr><tr><td>Shutdown Value (volts)</td><td>Decimal</td><td>If Specified Value is selected, set the shutdown state value</td></tr><tr><td>Off Value (volts)</td><td>Decimal</td><td>If Specified Value to apply when turned off</td></tr></tbody></table>

