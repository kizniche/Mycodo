Inputs, such as sensors, ADC signals, or even a response from a command, enable measuring conditions in the environment or elsewhere, which will be stored in a time-series database (InfluxDB). This database will provide measurements for [Dashboards](Data-Viewing.md/#dashboard), [LCDs](LCDs.md), [PID Controllers](Functions.md/#pid-controller), [Conditional Statements](Functions.md/#conditional), and other parts of Mycodo to operate from. Add, configure, and activate inputs to begin recording measurements to the database and allow them to be used throughout Mycodo.

### Input Actions

Input Actions are functions within the Input module that can be executed from the Web UI. This is useful for things such as calibration or other functionality specific to the input. By default there is at least one action, Acquire Measurements Now, which will cause the input to acquire measurements rather than waiting until the next Period has elapsed.

!!! note
    Actions can only be executed while the Input is active.

### Input Options

In addition to several supported sensors and devices, a Linux command may be specified that will be executed and the return value stored in the measurement database to be used throughout the Mycodo system.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Activate</td>
<td align="left">After the sensor has been properly configured, activation begins acquiring measurements from the sensor. Any activated conditional statements will now being operating.</td>
</tr>
<tr class="even">
<td align="left">Deactivate</td>
<td align="left">Deactivation stops measurements from being acquired from the sensor. All associated conditional statements will cease to operate.</td>
</tr>
<tr class="odd">
<td align="left">Save</td>
<td align="left">Save the current configuration entered into the input boxes for a particular sensor.</td>
</tr>
<tr class="even">
<td align="left">Delete</td>
<td align="left">Delete a particular sensor.</td>
</tr>
<tr class="odd">
<td align="left">Acquire Measurements Now</td>
<td align="left">Force the input to conduct measurements and them in the database.</td>
</tr>
<tr class="even">
<td align="left">Up/Down</td>
<td align="left">Move a particular sensor up or down in the order displayed.</td>
</tr>
<tr class="odd">
<td align="left">Power Output</td>
<td align="left">Select a output that powers the sensor. This enables powering cycling (turn off then on) when the sensor returns 3 consecutive errors to attempt to fix the issue. Transistors may also be used instead of a relay (note: NPN transistors are preferred over PNP for powering sensors).</td>
</tr>
<tr class="even">
<td align="left">Location</td>
<td align="left">Depending on what sensor is being used, you will need to either select a serial number (DS18B20 temperature sensor), a GPIO pin (in the case of sensors read by a GPIO), or an I2C address. or other.</td>
</tr>
<tr class="odd">
<td align="left">I2C Bus</td>
<td align="left">The bus to be used to communicate with the I2C address.</td>
</tr>
<tr class="even">
<td align="left">Period (seconds)</td>
<td align="left">After the sensor is successfully read and a database entry is made, this is the duration of time waited until the sensor is measured again.</td>
</tr>
<tr class="odd">
<td align="left">Measurement Unit</td>
<td align="left">Select the unit to save the measurement as (only available for select measurements).</td>
</tr>
<tr class="even">
<td align="left">Pre Output</td>
<td align="left">If you require a output to be activated before a measurement is made (for instance, if you have a pump that extracts air to a chamber where the sensor resides), this is the output number that will be activated. The output will be activated for a duration defined by the Pre Duration, then once the output turns off, a measurement by the sensor is made.</td>
</tr>
<tr class="odd">
<td align="left">Pre Output Duration (seconds)</td>
<td align="left">This is the duration of time that the Pre Output runs for before the sensor measurement is obtained.</td>
</tr>
<tr class="even">
<td align="left">Pre Output During Measurement</td>
<td align="left">If enabled, the Pre Output stays on during the acquisition of a measurement. If disabled, the Pre Output is turned off directly before acquiring a measurement.</td>
</tr>
<tr class="odd">
<td align="left">Command</td>
<td align="left">A linux command (executed as the user 'root') that the return value becomes the measurement</td>
</tr>
<tr class="even">
<td align="left">Command Measurement</td>
<td align="left">The measured condition (e.g. temperature, humidity, etc.) from the linux command</td>
</tr>
<tr class="odd">
<td align="left">Command Units</td>
<td align="left">The units of the measurement condition from the linux command</td>
</tr>
<tr class="even">
<td align="left">Edge</td>
<td align="left">Edge sensors only: Select whether the Rising or Falling (or both) edges of a changing voltage are detected. A number of devices to do this when in-line with a circuit supplying a 3.3-volt input signal to a GPIO, such as simple mechanical switch, a button, a magnet (reed/hall) sensor, a PIR motion detector, and more.</td>
</tr>
<tr class="odd">
<td align="left">Bounce Time (ms)</td>
<td align="left">Edge sensors only: This is the number of milliseconds to bounce the input signal. This is commonly called debouncing a signal [1] and may be necessary if using a mechanical circuit.</td>
</tr>
<tr class="even">
<td align="left">Reset Period (seconds)</td>
<td align="left">Edge sensors only: This is the period of time after an edge detection that another edge will not be recorded. This enables devices such as PIR motion sensors that may stay activated for longer periods of time.</td>
</tr>
<tr class="odd">
<td align="left">Measurement</td>
<td align="left">Analog-to-digital converter only: The type of measurement being acquired by the ADC. For instance, if the resistance of a photocell is being measured through a voltage divider, this measurement would be &quot;light&quot;.</td>
</tr>
<tr class="even">
<td align="left">Units</td>
<td align="left">Analog-to-digital converter only: This is the unit of the measurement. With the above example of &quot;light&quot; as the measurement, the unit may be &quot;lux&quot; or &quot;intensity&quot;.</td>
</tr>
<tr class="odd">
<td align="left">BT Adapter</td>
<td align="left">The Bluetooth adapter to communicate with the input.</td>
</tr>
<tr class="even">
<td align="left">Clock Pin</td>
<td align="left">The GPIO (using BCM numbering) connected to the Clock pin of the ADC</td>
</tr>
<tr class="odd">
<td align="left">CS Pin</td>
<td align="left">The GPIO (using BCM numbering) connected to the CS pin of the ADC</td>
</tr>
<tr class="even">
<td align="left">MISO Pin</td>
<td align="left">The GPIO (using BCM numbering) connected to the MISO pin of the ADC</td>
</tr>
<tr class="odd">
<td align="left">MOSI Pin</td>
<td align="left">The GPIO (using BCM numbering) connected to the MOSI pin of the ADC</td>
</tr>
<tr class="even">
<td align="left">RTD Probe Type</td>
<td align="left">Select to measure from a PT100 or PT1000 probe.</td>
</tr>
<tr class="odd">
<td align="left">Resistor Reference (Ohm)</td>
<td align="left">If your reference resistor is not the default (400 Ohm for PT100, 4000 Ohm for PT1000), you can manually set this value. Several manufacturers now use 430 Ohm resistors on their circuit boards, therefore it's recommended to verify the accuracy of your measurements and adjust this value if necessary.</td>
</tr>
<tr class="even">
<td align="left">Channel</td>
<td align="left">Analog-to-digital converter only: This is the channel to obtain the voltage measurement from the ADC.</td>
</tr>
<tr class="odd">
<td align="left">Gain</td>
<td align="left">Analog-to-digital converter only: set the gain when acquiring the measurement.</td>
</tr>
<tr class="even">
<td align="left">Sample Speed</td>
<td align="left">Analog-to-digital converter only: set the sample speed (typically samples per second).</td>
</tr>
<tr class="odd">
<td align="left">Volts Min</td>
<td align="left">Analog-to-digital converter only: What is the minimum voltage to use when scaling to produce the unit value for the database. For instance, if your ADC is not expected to measure below 0.2 volts for your particular circuit, set this to &quot;0.2&quot;.</td>
</tr>
<tr class="even">
<td align="left">Volts Max</td>
<td align="left">Analog-to-digital converter only: This is similar to the Min option above, however it is setting the ceiling to the voltage range. Units Min Analog-to-digital converter only: This value will be the lower value of a range that will use the Min and Max Voltages, above, to produce a unit output. For instance, if your voltage range is 0.0 -1.0 volts, and the unit range is 1 -60, and a voltage of 0.5 is measured, in addition to 0.5 being stored in the database, 30 will be stored as well. This enables creating calibrated scales to use with your particular circuit.</td>
</tr>
<tr class="odd">
<td align="left">Units Max</td>
<td align="left">Analog-to-digital converter only: This is similar to the Min option above, however it is setting the ceiling to the unit range.</td>
</tr>
<tr class="even">
<td align="left">Weighting</td>
<td align="left">The This is a number between 0 and 1 and indicates how much the old reading affects the new reading. It defaults to 0 which means the old reading has no effect. This may be used to smooth the data.</td>
</tr>
<tr class="odd">
<td align="left">Pulses Per Rev</td>
<td align="left">The number of pulses for a complete revolution.</td>
</tr>
<tr class="even">
<td align="left">Port</td>
<td align="left">The server port to be queried (Server Port Open input).</td>
</tr>
<tr class="odd">
<td align="left">Times to Check</td>
<td align="left">The number of times to attempt to ping a server (Server Ping input).</td>
</tr>
<tr class="even">
<td align="left">Deadline (seconds)</td>
<td align="left">The maximum amount of time to wait for each ping attempt, after which 0 (offline) will be returned (Server Ping input).</td>
</tr>
<tr class="odd">
<td align="left">Number of Measurement</td>
<td align="left">The number of unique measurements to store data for this input.</td>
</tr>
<tr class="even">
<td align="left">Application ID</td>
<td align="left">The Application ID on The Things Network.</td>
</tr>
<tr class="odd">
<td align="left">App API Key</td>
<td align="left">The Application API Key on The Things Network.</td>
</tr>
<tr class="even">
<td align="left">Device ID</td>
<td align="left">The Device ID of the Application on The Things Network.</td>
</tr>
</tbody>
</table>

1.  [Debouncing a signal](https://kylegabriel.com/projects/2016/02/morse-code-translator.html#debouncing)

### Custom Inputs

See [Building a Custom Input Module](https://github.com/kizniche/Mycodo/wiki/Building-a-Custom-Input-Module) Wiki page.

There is a Custom Input import system in Mycodo that allows user-created Inputs to be created an used in the Mycodo system. Custom Inputs can be uploaded and imported from the `Configure -> Inputs` page. After import, they will be available to use on the `Setup -> Data` page.

If you have a sensor that is not currently supported by Mycodo, you can build your own input module and import it into Mycodo.

Open any of the built-in modules located in the inputs directory (<https://github.com/kizniche/Mycodo/tree/master/mycodo/inputs/>) for examples of the proper formatting.

There's also minimal input module template that generates random data as an example:

<https://github.com/kizniche/Mycodo/tree/master/mycodo/inputs/examples/minimal_humidity_temperature.py>

There's also an input module that includes all available INPUT_INFORMATION options along with descriptions:

<https://github.com/kizniche/Mycodo/tree/master/mycodo/inputs/examples/example_all_options_temperature.py>

Additionally, I have another github repository devoted to Custom Inputs and Controllers that are not included in the built-in set, at [kizniche/Mycodo-custom](https://github.com/kizniche/Mycodo-custom).

### The Things Network

[The Things Network](https://www.thethingsnetwork.org/) (TTN) Input module enables downloading of data from TTN if the Data Storage Integration is enabled in your TTN Application. The Data Storage Integration will store data for up to 7 days. Mycodo will download this data periodically and store the measurements locally.

The payload on TTN must be properly decoded to variables that correspond to the "Name" option under "Select Measurements", in the lower section of the Input options. For instance, in your TTN Application, if a custom Payload Format is selected, the decoder code may look like this:

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

This will decode the 2-byte payload into a temperature float value with the name "temperature". Set "Number of Measurements" to "1", then set the "Name" for the first channel (CH0) to "temperature" and the "Measurement Unit" to "Temperature: Celsius (°C)".

Upon activation of the Input, data will be downloaded for the past 7 days. The latest data timestamp will be stored so any subsequent activation of the Input will only download new data (since the last known timestamp).

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

These example Input modules may be modified to suit your needs and imported into Mycodo through the `Configure -> Inputs` page. After import, they will be available to use on the `Setup -> Data` page.

## Math

Math controllers allow one or more Inputs to have math applied to produce a new value that may be used within Mycodo.

!!! note
    "Last" means the controller will only acquire the last (latest) measurement in the database for performing math with. "Past" means the controller will acquire all measurements from the present until the "Max Age (seconds)" set by the user (e.g. if measurements are acquired every 10 seconds, and a Max Age is set to 60 seconds, there will on average be 6 measurements returned to have math performed).

### Math Options

Types of math controllers.

<table>
<col width="41%" />
<col width="58%" />
<thead>
<tr class="header">
<th align="left">Type</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Average (Last, Multiple Channels)</td>
<td align="left">Stores the statistical mean of the last measurement of multiple selected measurement channels.</td>
</tr>
<tr class="even">
<td align="left">Average (Past, Single Channel)</td>
<td align="left">Stores the statistical mean of one selected measurement channel over a duration of time determined by the Max Age (seconds) option.</td>
</tr>
<tr class="odd">
<td align="left">Sum (Last, Multiple Channels)</td>
<td align="left">Stores the sum of multiple selected measurement channels.</td>
</tr>
<tr class="even">
<td align="left">Sum (Past, Single Channel)</td>
<td align="left">Stores the sum of one selected measurement channel over a duration of time determined by the Max Age(seconds) option.</td>
</tr>
<tr class="odd">
<td align="left">Difference</td>
<td align="left">Stores the mathematical difference (value_1 - value_2).</td>
</tr>
<tr class="even">
<td align="left">Equation</td>
<td align="left">Stores the calculated value of an equation.</td>
</tr>
<tr class="odd">
<td align="left">Redundancy</td>
<td align="left">Select multiple Inputs and if one input isn't available, the next measurement will be used. For example, this is useful if an Input stops but you don't want a PID controller to stop working if there is another measurement that can be used. More than one Input can be and the preferred Order of Use can be defined.</td>
</tr>
<tr class="even">
<td align="left">Verification</td>
<td align="left">Ensures the greatest difference between any selected Inputs is less than Max Difference, and if so, stores the average of the selected measurements.</td>
</tr>
<tr class="odd">
<td align="left">Statistics</td>
<td align="left">Calculates mean, median, minimum, maximum, standard deviation (SD), SD upper, and SD lower for a set of measurements.</td>
</tr>
<tr class="even">
<td align="left">Humidity (Wet/Dry-Bulb)</td>
<td align="left">Calculates and stores the percent relative humidity from the dry-bulb and wet-bulb temperatures, and optional pressure.</td>
</tr>
</tbody>
</table>

Math controller options.

<table>
<col width="40%" />
<col width="59%" />
<thead>
<tr class="header">
<th align="left">Setting</th>
<th align="left">Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Input</td>
<td align="left">Select the Inputs to use with the particular Math controller</td>
</tr>
<tr class="even">
<td align="left">Period (seconds)</td>
<td align="left">The duration of time between calculating and storing a new value</td>
</tr>
<tr class="odd">
<td align="left">Max Age (seconds)</td>
<td align="left">The maximum allowed age of the Input measurements. If an Input measurement is older than this period, the calculation is cancelled and the new value is not stored in the database. Consequently, if another controller has a Max Age set and cannot retrieve a current Math value, it will cease functioning. A PID controller, for instance, may stop regulating if there is no new Math value created, preventing the PID controller from continuing to run when it should not.</td>
</tr>
<tr class="even">
<td align="left">Start Offset (seconds)</td>
<td align="left">Wait this duration before attempting the first calculation/measurement.</td>
</tr>
<tr class="odd">
<td align="left">Measurement</td>
<td align="left">This is the condition being measured. For instance, if all of the selected measurements are temperature, this should also be temperature. A list of the pre-defined measurements that may be used is below.</td>
</tr>
<tr class="even">
<td align="left">Units</td>
<td align="left">This is the units to display along with the measurement, on Graphs. If a pre-defined measurement is used, this field will default to the units associated with that measurement.</td>
</tr>
<tr class="odd">
<td align="left">Reverse Equation</td>
<td align="left">For Difference calculations, this will reverse the equation order, from <code>value_1 - value_2</code> to <code>value_2 - value_1</code>.</td>
</tr>
<tr class="even">
<td align="left">Absolute Value</td>
<td align="left">For Difference calculations, this will yield an absolute value (positive number).</td>
</tr>
<tr class="odd">
<td align="left">Max Difference</td>
<td align="left">If the difference between any selected Input is greater than this value, no new value will be stored in the database.</td>
</tr>
<tr class="even">
<td align="left">Dry-Bulb Temperature</td>
<td align="left">The measurement that will serve as the dry-bulb temperature (this is the warmer of the two temperature measurements)</td>
</tr>
<tr class="odd">
<td align="left">Wet-Bulb Temperature</td>
<td align="left">The measurement that will serve as the wet-bulb temperature (this is the colder of the two temperature measurements)</td>
</tr>
<tr class="even">
<td align="left">Pressure</td>
<td align="left">This is an optional pressure measurement that can be used to calculate the percent relative humidity. If disabled, a default 101325 Pa will be used in the calculation.</td>
</tr>
<tr class="odd">
<td align="left">Equation</td>
<td align="left">An equation that will be solved with Python's eval() function. Let &quot;x&quot; represent the input value. Valid equation symbols include: + - * / ^</td>
</tr>
<tr class="even">
<td align="left">Order of Use</td>
<td align="left">This is the order in which the selected Inputs will be used. This must be a comma separated list of Input IDs (integers, not UUIDs).</td>
</tr>
</tbody>
</table>
