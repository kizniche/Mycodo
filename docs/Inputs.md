Page\: `Setup -> Input`

For a full list of supported Inputs, see [Supported Input Devices](Supported-Inputs.md).

Inputs, such as sensors, ADC signals, or even a response from a command, enable measuring conditions in the environment or elsewhere, which will be stored in a time-series database (InfluxDB). This database will provide measurements for [Dashboard Widgets](Data-Viewing.md#dashboard), [Functions](Functions.md), and other parts of Mycodo to operate from. Add, configure, and activate inputs to begin recording measurements to the database and allow them to be used throughout Mycodo.

### Custom Inputs

See [Building a Custom Input Module](https://github.com/kizniche/Mycodo/wiki/Building-a-Custom-Input-Module) Wiki page.

There is a Custom Input import system in Mycodo that allows user-created Inputs to be created an used in the Mycodo system. Custom Inputs can be uploaded and imported from the `[Gear Icon] -> Configure -> Custom Inputs` page. After import, they will be available to use on the `Setup -> Input` page.

If you develop a working Input module, please consider [creating a new GitHub issue](https://github.com/kizniche/Mycodo/issues/new?assignees=&labels=&template=feature-request.md&title=New%20Module) or pull request, and it may be included in the built-in set.

Open any of the built-in modules located in the directory [Mycodo/mycodo/inputs](https://github.com/kizniche/Mycodo/tree/master/mycodo/inputs/) for examples of the proper formatting.

There are also example Custom Inputs in the directory [Mycodo/mycodo/inputs/examples](https://github.com/kizniche/Mycodo/tree/master/mycodo/inputs/examples)

Additionally, I have another github repository devoted to Custom Modules that are not included in the built-in set, at [kizniche/Mycodo-custom](https://github.com/kizniche/Mycodo-custom).

### Input Commands

Input Commands are functions within the Input module that can be executed from the Web UI. This is useful for things such as calibration or other functionality specific to the input. By default, there is at least one action, Acquire Measurements Now, which will cause the input to acquire measurements rather than waiting until the next Period has elapsed.

!!! note
    Actions can only be executed while the Input is active.

### Input Actions

Every Period the Input will acquire measurements and store then in the time-series database. Following measurement acquisition, one or more [Actions](Actions.md) can be executed to enhance the functionality of Inputs. For example, the MQTT Publish Action can be used to publish measurements to an MQTT server.

### Input Options

<table>
<thead>
<tr class="header">
<th>Setting</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td>Activate</td>
<td>After the sensor has been properly configured, activation begins acquiring measurements from the sensor. Any activated Conditional Functions will now being operating.</td>
</tr>
<tr>
<td>Deactivate</td>
<td>Deactivation stops measurements from being acquired from the sensor. All associated Conditional Functions will cease to operate.</td>
</tr>
<tr>
<td>Save</td>
<td>Save the current configuration entered into the input boxes for a particular sensor.</td>
</tr>
<tr>
<td>Delete</td>
<td>Delete a particular sensor.</td>
</tr>
<tr>
<td>Acquire Measurements Now</td>
<td>Force the input to conduct measurements and them in the database.</td>
</tr>
<tr>
<td>Up/Down</td>
<td>Move a particular sensor up or down in the order displayed.</td>
</tr>
<tr>
<td>Power Output</td>
<td>Select a output that powers the sensor. This enables powering cycling (turn off then on) when the sensor returns 3 consecutive errors to attempt to fix the issue. Transistors may also be used instead of a relay (note: NPN transistors are preferred over PNP for powering sensors).</td>
</tr>
<tr>
<td>Location</td>
<td>Depending on what sensor is being used, you will need to either select a serial number (DS18B20 temperature sensor), a GPIO pin (in the case of sensors read by a GPIO), or an I2C address. or other.</td>
</tr>
<tr>
<td>I2C Bus</td>
<td>The bus to be used to communicate with the I2C address.</td>
</tr>
<tr>
<td>Period (seconds)</td>
<td>After the sensor is successfully read and a database entry is made, this is the duration of time waited until the sensor is measured again.</td>
</tr>
<tr>
<td>Measurement Unit</td>
<td>Select the unit to save the measurement as (only available for select measurements).</td>
</tr>
<tr>
<td>Pre Output</td>
<td>If you require a output to be activated before a measurement is made (for instance, if you have a pump that extracts air to a chamber where the sensor resides), this is the output number that will be activated. The output will be activated for a duration defined by the Pre Duration, then once the output turns off, a measurement by the sensor is made.</td>
</tr>
<tr>
<td>Pre Output Duration (seconds)</td>
<td>This is the duration of time that the Pre Output runs for before the sensor measurement is obtained.</td>
</tr>
<tr>
<td>Pre Output During Measurement</td>
<td>If enabled, the Pre Output stays on during the acquisition of a measurement. If disabled, the Pre Output is turned off directly before acquiring a measurement.</td>
</tr>
<tr>
<td>Command</td>
<td>A linux command (executed as the user 'root') that the return value becomes the measurement</td>
</tr>
<tr>
<td>Command Measurement</td>
<td>The measured condition (e.g. temperature, humidity, etc.) from the linux command</td>
</tr>
<tr>
<td>Command Units</td>
<td>The units of the measurement condition from the linux command</td>
</tr>
<tr>
<td>Edge</td>
<td>Edge sensors only: Select whether the Rising or Falling (or both) edges of a changing voltage are detected. A number of devices to do this when in-line with a circuit supplying a 3.3-volt input signal to a GPIO, such as simple mechanical switch, a button, a magnet (reed/hall) sensor, a PIR motion detector, and more.</td>
</tr>
<tr>
<td>Bounce Time (ms)</td>
<td>Edge sensors only: This is the number of milliseconds to bounce the input signal. This is commonly called debouncing a signal [1] and may be necessary if using a mechanical circuit.</td>
</tr>
<tr>
<td>Reset Period (seconds)</td>
<td>Edge sensors only: This is the period of time after an edge detection that another edge will not be recorded. This enables devices such as PIR motion sensors that may stay activated for longer periods of time.</td>
</tr>
<tr>
<td>Measurement</td>
<td>Analog-to-digital converter only: The type of measurement being acquired by the ADC. For instance, if the resistance of a photocell is being measured through a voltage divider, this measurement would be &quot;light&quot;.</td>
</tr>
<tr>
<td>Units</td>
<td>Analog-to-digital converter only: This is the unit of the measurement. With the above example of &quot;light&quot; as the measurement, the unit may be &quot;lux&quot; or &quot;intensity&quot;.</td>
</tr>
<tr>
<td>BT Adapter</td>
<td>The Bluetooth adapter to communicate with the input.</td>
</tr>
<tr>
<td>Clock Pin</td>
<td>The GPIO (using BCM numbering) connected to the Clock pin of the ADC</td>
</tr>
<tr>
<td>CS Pin</td>
<td>The GPIO (using BCM numbering) connected to the CS pin of the ADC</td>
</tr>
<tr>
<td>MISO Pin</td>
<td>The GPIO (using BCM numbering) connected to the MISO pin of the ADC</td>
</tr>
<tr>
<td>MOSI Pin</td>
<td>The GPIO (using BCM numbering) connected to the MOSI pin of the ADC</td>
</tr>
<tr>
<td>RTD Probe Type</td>
<td>Select to measure from a PT100 or PT1000 probe.</td>
</tr>
<tr>
<td>Resistor Reference (Ohm)</td>
<td>If your reference resistor is not the default (400 Ohm for PT100, 4000 Ohm for PT1000), you can manually set this value. Several manufacturers now use 430 Ohm resistors on their circuit boards, therefore it's recommended to verify the accuracy of your measurements and adjust this value if necessary.</td>
</tr>
<tr>
<td>Channel</td>
<td>Analog-to-digital converter only: This is the channel to obtain the voltage measurement from the ADC.</td>
</tr>
<tr>
<td>Gain</td>
<td>Analog-to-digital converter only: set the gain when acquiring the measurement.</td>
</tr>
<tr>
<td>Sample Speed</td>
<td>Analog-to-digital converter only: set the sample speed (typically samples per second).</td>
</tr>
<tr>
<td>Volts Min</td>
<td>Analog-to-digital converter only: What is the minimum voltage to use when scaling to produce the unit value for the database. For instance, if your ADC is not expected to measure below 0.2 volts for your particular circuit, set this to &quot;0.2&quot;.</td>
</tr>
<tr>
<td>Volts Max</td>
<td>Analog-to-digital converter only: This is similar to the Min option above, however it is setting the ceiling to the voltage range. Units Min Analog-to-digital converter only: This value will be the lower value of a range that will use the Min and Max Voltages, above, to produce a unit output. For instance, if your voltage range is 0.0 -1.0 volts, and the unit range is 1 -60, and a voltage of 0.5 is measured, in addition to 0.5 being stored in the database, 30 will be stored as well. This enables creating calibrated scales to use with your particular circuit.</td>
</tr>
<tr>
<td>Units Max</td>
<td>Analog-to-digital converter only: This is similar to the Min option above, however it is setting the ceiling to the unit range.</td>
</tr>
<tr>
<td>Weighting</td>
<td>The This is a number between 0 and 1 and indicates how much the old reading affects the new reading. It defaults to 0 which means the old reading has no effect. This may be used to smooth the data.</td>
</tr>
<tr>
<td>Pulses Per Rev</td>
<td>The number of pulses for a complete revolution.</td>
</tr>
<tr>
<td>Port</td>
<td>The server port to be queried (Server Port Open input).</td>
</tr>
<tr>
<td>Times to Check</td>
<td>The number of times to attempt to ping a server (Server Ping input).</td>
</tr>
<tr>
<td>Deadline (seconds)</td>
<td>The maximum amount of time to wait for each ping attempt, after which 0 (offline) will be returned (Server Ping input).</td>
</tr>
<tr>
<td>Number of Measurement</td>
<td>The number of unique measurements to store data for this input.</td>
</tr>
<tr>
<td>Application ID</td>
<td>The Application ID on The Things Network.</td>
</tr>
<tr>
<td>App API Key</td>
<td>The Application API Key on The Things Network.</td>
</tr>
<tr>
<td>Device ID</td>
<td>The Device ID of the Application on The Things Network.</td>
</tr>
</tbody>
</table>

1.  [Debouncing a signal](https://kylegabriel.com/projects/2016/02/morse-code-translator.html#debouncing)

### The Things Network

[The Things Network](https://www.thethingsnetwork.org/) (TTN, v2 and v3) Input module enables downloading of data from TTN if the Data Storage Integration is enabled in your TTN Application. The Data Storage Integration will store data for up to 7 days. Mycodo will download this data periodically and store the measurements locally.

The payload on TTN must be properly decoded to variables that correspond to the "Variable Name" option under "Channel Options", in the lower section of the Input options. For instance, in your TTN Application, if a custom Payload Format is selected, the decoder code may look like this:

```javascript
function Decoder(bytes, port) {
    var decoded = {};
    var rawTemp = bytes[0] + bytes[1] * 256;
    decoded.temperature = sflt162f(rawTemp) * 100;
    return decoded;
}

function sflt162f(rawSflt16) {
    rawSflt16 &= 0xFFFF;
    if (rawSflt16 === 0x8000)
        return -0.0;
    var sSign = ((rawSflt16 & 0x8000) !== 0) ? -1 : 1;
    var exp1 = (rawSflt16 >> 11) & 0xF;
    var mant1 = (rawSflt16 & 0x7FF) / 2048.0;
    return sSign * mant1 * Math.pow(2, exp1 - 15);
}
```

This will decode the 2-byte payload into a temperature float value with the name "temperature". Set "Number of Measurements" to "1", then set the "Variable Name" for the first channel (CH0) to "temperature" and the "Measurement Unit" to "Temperature: Celsius (°C)".

Upon activation of the Input, data will be downloaded for the past 7 days. The latest data timestamp will be stored so any subsequent activation of the Input will only download new data (since the last known timestamp).

This Input also allows multiple measurements to be stored. You merely have to change "Number of Measurements" to a number larger than 1, save, and there will now be multiple variable names and measurement units to set.

There are several example Input modules that, in addition to storing the measurements of a sensor in the influx database, will write the measurements to a serial device. This is useful of you have a LoRaWAN transmitter connected via serial to receive measurement information from Mycodo and transmit it to a LoRaWAN gateway (and subsequently to The Things Network). The data on TTN can then be downloaded elsewhere with the TTN Input. These example Input modules are located in the following locations:

`~/Mycodo/mycodo/inputs/examples/bme280_ttn.py`

`~/Mycodo/mycodo/inputs/examples/k30_ttn.py`

For example, the following excerpt from `bme_280.py` will write a set of comma-separated strings to the user-specified serial device with the first string (the letter "B") used to denote the sensor/measurements, followed by the actual measurements (humidity, pressure, and temperature, in this case).

```python
string_send = 'B,{},{},{}'.format(
    return_dict[1]['value'],
    return_dict[2]['value'],
    return_dict[0]['value'])
self.serial_send = self.serial.Serial(self.serial_device, 9600)
self.serial_send.write(string_send.encode())
```

This is useful if multiple data strings are to be sent to the same serial device (e.g. if both `bme280_ttn.py` and `k30_ttn.py` are being used at the same time), allowing the serial device to distinguish what data is being received.

The full code used to decode both `bme280_ttn.py` and `k30_ttn.py`, with informative comments, is located at `~/Mycodo/mycodo/inputs/examples/ttn_data_storage_decoder_example.js`.

These example Input modules may be modified to suit your needs and imported into Mycodo through the `[Gear Icon] -> Configure -> Custom Inputs` page. After import, they will be available to use on the `Setup -> Input` page.