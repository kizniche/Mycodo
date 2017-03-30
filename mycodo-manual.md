
Mycodo Manual
=============

Table of Contents
=================

[About Mycodo](#about-mycodo)

[Frequently Asked Questions](#frequently-asked-questions)

[Settings](#settings)

   - [General Settings](#general-settings)
   - [Relay Usage Settings](#relay-usage-settings)
   - [Users](#users)
   - [User Roles](#user-roles)
   - [Alert Settings](#alert-settings)
   - [Camera Settings](#camera-settings)

[Controllers](#controllers)

   - [Sensors](#sensors)
   - [Relays](#relays)
   - [PIDs](#pids)
   - [Timers](#timers)
   - [LCDs](#lcds)

[Controller Functions](#controller-functions)

   - [Conditional Statements](#conditional-statements)
   - [Methods](#methods)

[PID Tuning](#pid-tuning)

   - [PID Control Theory](#pid-control-theory)
   - [Quick Setup Examples](#quick-setup-examples)
   - [Exact-Temperature Regulation](#exact-temperature-regulation)
   - [High-Temperature Regulation](#high-temperature-regulation)

[Miscellaneous](#miscellaneous)

   - [Graphs](#graphs)
   - [Camera](#camera)
   - [Relay Usage](#relay-usage)
   - [System Backup](#system-backup)
   - [System Restore](#system-restore)

[Troubleshooting](#troubleshooting)

   - [Daemon Not Running](#daemon-not-running)
   - [More](#more)

[Appendix](#appendix)

[Temperature Sensors](#temperature-sensors)

   - [Raspberry Pi](#raspberry-pi)
   - [Atlas Scientific PT-1000](#atlas-scientific-pt-1000)
   - [DS18B20](#ds18b20)
   - [TMP006, TMP007](#tmp006-tmp007)

[Temperature, Humidity Sensors](#temperature-humidity-sensors)

   - [AM2315](#am2315)
   - [DHT11](#dht11)
   - [DHT22, AM2302](#dht22-am2302)
   - [HTU21D](#htu21d)
   - [SHT1x](#sht1x)
   - [SHT7x](#sht7x)

[CO2 Sensors](#co2-sensors)

   - [K-30](#k-30)

[Moisture Sensors](#moisture-sensors)

   - [Chirp](#chirp)

[Pressure Sensors](#pressure-sensors)

   - [BMP085, BMP180](#bmp085-bmp180)

[Luminosity Sensors](#luminosity-sensors)

   - [BH1750](#bh1750)
   - [TSL2561](#tsl2561)

[I<sup>2</sup>C Multiplexers](#i2c-multiplexers)

   - [TCA9548A](#tca9548a)

[Analog to Digital Converters](#analog-to-digital-converters)

   - [ADS1x15](#ads1x15)
   - [MCP342x](#mcp342x)

[Schematics and Diagrams](#schematics-and-diagrams)

   - [Pi Schematics](#pi-schematics)

* * * * *

About Mycodo
============

Mycodo is a remote monitoring and automated regulation system with a
focus on modulating environmental conditions. It was built to run on the
Raspberry Pi (versions Zero, 1, 2, and 3) and aims to be easy to install
and set up.

The core system coordinates a diverse set of responses to sensor
measurements, including actions such as camera captures, email
notifications, relay activation/deactivation, regulation with PID
control, and more. Mycodo has been used for cultivating gourmet
mushrooms, cultivating plants, culturing microorganisms, maintaining
honey bee apiary homeostasis, incubating snake eggs and young animals,
aging cheeses, fermenting foods, maintaining aquatic systems, and more.

A [proportional-derivative-integral (PID)
controller](https://en.wikipedia.org/wiki/PID_controller) is a control
loop feedback mechanism used throughout industry for controlling
systems. It efficiently brings a measurable condition, such as the
temperature, to a desired state and maintains it there with little
overshoot and oscillation. A well-tuned PID controller will raise to the
setpoint quickly, have minimal overshoot, and maintain the setpoint with
little oscillation.

Frequently Asked Questions
==========================

*Where do I even begin?*

Here is how I generally set up Mycodo to monitor and regulate:

1.  Determine what environmental condition you want to measure or
    regulate. Consider the devices that must be coupled to achieve this.
    For instance, temperature regulation require a temperature sensor
    and an electric heater and/or electric air conditioner.
2.  Determine what relays you will need to power your electric devices.
    The Raspberry Pi is capable of directly switching relays (using a
    3.3-volt signal), although opto-isolating the circuit is advisable.
    Be careful when selecting a relay not to exceed the current draw of
    the Raspberry Pi's PGIO.
3.  See the [Appendix](#appendix) for information about what sensors are
    supported. Acquire one or more of these sensors and relays and
    connect them to the Raspberry Pi according to the manufacturer's
    instructions.
4.  On the ```Sensors``` page, create a new sensor, using the
    dropdown to select the correct sensor. Configure the sensor with the
    correct communication pins, etc. and save. Activate the sensor to
    begin recording measurements.
5.  Go to the ```Data``` -> ```Live Measurements``` page to ensure there
    is recent data being acquired from the sensor.
6.  On the ```Relay``` -> ```Relays``` page, add a relay and configure
    the GPIO pin that switches it, whether the relay switches On when the
    signal is HIGH or LOW, and what state (On or Off) to set the relay
    when Mycodo starts.
7.  Test the relay by switching it On and Off from the ```Relay``` ->
    ```Relays``` page and make sure the device connected to the relay
    turns On when you select "On", and Off when you select "Off".
8.  On the ```PID``` -> ```PID Controllers``` page, create a PID
    controller with the appropriate sensor, measurement, relay, and other
    parameters. Refer to the [Quick Setup Examples](#quick-setup-examples)
    for setting up and tuning a PID controller.
9.  On the ```Data``` -> ```Live Graphs``` page, create a graph that
    includes the sensor measurement, the relay that is being used by the
    PID, and the PID setpoint. This provides a good visualization for
    tuning and adjusting the system.

* * * * *

*Why is there only one FAQ?*

Good question.

* * * * *

Settings
========

The settings menu, accessed by selecting the gear icon in the top-right,
then the Configure link, is a general area for various system-wide
configuration options.


General Settings
----------------

Setting | Description
--- | ---
Language | Set the language that will be displayed in the web user interface.
Force HTTPS | Require web browsers to use SSL/HTTPS. Any request to http:// will be redirected to https://.
Hide success alerts | Hide all success alert boxes that appear at the top of the page.
Hide info alerts | Hide all info alert boxes that appear at the top of the page.
Hide warning alerts | Hide all warning alert boxes that appear at the top of the page.
Opt-out of statistics | Turn off sending anonymous usage statistics. Please consider that this helps the development to leave on.


Relay Usage Settings
--------------------

In order to calculate accurate relay usage statistics, a few
characteristics of your electrical system needs to be know. These
variables should describe the characteristics of the electrical system
being used by the relays to operate electrical devices. Note: Proper
relay usage calculations also rely on the correct current draw to be set
for each relay (see [Relay Settings](#relays)).

Setting | Description
--- | ---
Voltage | Alternating current (AC) voltage that is switched by the relays. This is usually 120 or 240.
Cost per kWh | This is how much you pay per kWh.
Currency Unit | This is the unit used for the currency that pays for electricity.
Day of Month | This is the day of the month (1-30) that the electricity meter is read (which will correspond to the electrical bill).

Users
-----

Mycodo requires at least one Admin user for the login system to be
enabled. If there isn't an Admin user, the web server will redirect to
an Admin Creation Form. This is the first page you see when starting
Mycodo for the first time. After an Admin user has been created,
additional users may be created from the User Settings page.

Setting | Description
--- | ---
Username | Choose a user name that is between 2 and 64 characters. The user name is case insensitive (all user names are converted to lower-case).
Email | The email associated with the new account.
Password/Repeat | Choose a password that is between 6 and 64 characters and only contain letters, numbers, and symbols.
Role | Roles are a way of imposing access restrictions on users, to either allow or deny actions. See the table below for explanations of the four default Roles.

User Roles
----------

Roles define the permissions of each user. There are 4 default roles
that determine if a user can view or edit particular areas of Mycodo.
Custom roles may be created, but these four roles may not be modified or
deleted.

| Role | Admin | Editor | Monitor | Guest |
| --- | --- | --- | --- | --- |
| Edit Users       | X | | | |
| Edit Controllers | X | X | | |
| Edit Settings    | X | X | | |
| View Settings    | X | X | X | |
| View Camera      | X | X | X | |
| View Stats       | X | X | X | |
| View Logs        | X | X | X | |

<sup>1</sup>The ```Edit Controllers``` permission protects the editing of Graphs, LCDs, Methods, PIDs, Relays, Sensors, and Timers.

<sup>2</sup>The ```View Stats``` permission protects the viewing of usage statistics and the System Info and Relay Usage pages.

Alert Settings
--------------

Alert settings set up the credentials for sending email notifications.

Setting | Description
--- | ---
SMTP Host | The SMTP server to use to send emails from.
SMTP Port | Port to communicate with the SMTP server (465 for SSL, 587 for TSL).
Enable SSL | Check to emable SSL, uncheck to enable TSL.
SMTP User | The user name to send the email from. This can be just a name or the entire email address.
SMTP Password | The password for the user.
From Email | What the from email address be set as. This should be the actual email address for this user.
Max emails (per hour) | Set the maximum number of emails that can be sent per hour. If more notifications are triggered within the hour and this number has been reached, the notifications will be discarded.

Camera Settings
---------------

Many cameras can be used simultaneously with Mycodo. Each camera needs
to be set up in the camera settings, then may be used throughout the
software. Note that not every option (such as Hue or White Balance) may
be able to be used with your particular camera, due to manufacturer
differences in hardware and software.

Setting | Description
--- | ---
Type | Select whether the camera is a Raspberry Pi Camera or a USB camera.
Library | Select which library to use to communicate with the camera. The Raspberry Pi Camera uses picamera (and potentially opencv), and USB cameras should be set to opencv.
OpenCV Device | Any devices detected by opencv will populate this dropdown list. If there are no values in this list, none were detected. If you have multiple opencv devices detected, try setting the camera to each device and take a photo to determine which camera is associated with which device.
Relay ID | This relay will turn on during the capture of any still image (which includes timelapses).
Rotate Image | The number of degrees to rotate the image.
... | Image Width, Image Height, Brightness, Contrast, Exposure, Gain, Hue, Saturation, White Balance. These options are self-explanatory. Not all options will work with all cameras.
Pre Command | A command to execute (as user mycodo) before a still image is captured.
Post Command | A command to execute (as user mycodo) after a still image is captured.
Flip horizontally | Flip, or mirror, the image horizontally.
Flip vertically | Flip, or mirror, the image vertically.

Controllers
===========

Controllers are essentially modules that can be used to perform
functions or communicate with other parts of Mycodo. Each controller
performs a specific task or group of related tasks. There are also
Controller Functions, which are larger functions of a controller or
controllers and have been given their own sections.

Sensors
-------

Sensors measure environmental conditions, which will be stored in an
influx database. This database will provide recent measurement for
[Conditional Statements](/help#conditional-statements) or [PID
Controllers](/help#pids) to operate from, among other uses.

Setting | Description
--- | ---
Activate | After the sensor has been properly configured, activation begins acquiring measurements from the sensor. Any activated conditional statements will now being operating.
Deactivate | Deactivation stops measurements from being acquired from the sensor. All associated conditional statements will cease to operate.
Save | Save the current configuration entered into the input boxes for a particular sensor.
Delete | Delete a particular sensor.
Up/Down | Move a particular sensor up or down in the order displayed.
Location | Depending on what sensor is being used, you will need to either select a serial number (DS18B20 temperature sensor), a GPIO pin (in the case of sensors read by a GPIO), or an I<sup>2</sup>C address. and channel if using the TCA9548A I<sup>2</sup>C multiplexer.
I<sup>2</sup>C Bus | The bus to be used to communicate with the I<sup>2</sup>C address. If you're using an I<sup>2</sup>C multiplexer that provides multiple buses, this allows you to select which bus the sensor is connected to.
Period | After the sensor is successfully read and a database entry is made, this is the duration of time waited until the sensor is measured again.
Pre Relay | If you require a relay to be activated before a measurement is made (for instance, if you have a pump that extracts air to a chamber where the sensor resides), this is the relay number that will be activated. The relay will be activated for a duration defined by the Pre Duration, then once the relay turns off, a measurement by the sensor is made.
Pre Relay Duration | This is the duration of time that the Pre Relay runs for before the sensor measurement is obtained.
Edge | Edge sensors only: Select whether the Rising or Falling (or both) edges of a changing voltage are detected. A number of devices to do this when in-line with a circuit supplying a 3.3-volt input signal to a GPIO, such as simple mechanical switch, a button, a magnet (reed/hall) sensor, a PIR motion detector, and more.
Bounce Time (ms) | Edge sensors only: This is the number of milliseconds to bounce the input signal. This is commonly called [debouncing a signal](http://kylegabriel.com/projects/2016/02/morse-code-translator.html#debouncing). and may be necessary if using a mechanical circuit.
Reset Period | Edge sensors only: This is the period of time after an edge detection that another edge will not be recorded. This enables devices such as PIR motion sensors that may stay activated for longer periods of time.
Multiplexer (MX) | If connected to the TCA9548A I<sup>2</sup>C multiplexer, select what the I<sup>2</sup>C address of the multiplexer is.
Mx I<sup>2</sup>C Bus | If connected to the TCA9548A I<sup>2</sup>C multiplexer, select the I<sup>2</sup>C bus the multiplexer is connected to.
Mx Channel | If connected to the TCA9548A I<sup>2</sup>C multiplexer, select the channel of the multiplexer the device is connected to.
Measurement | Analog-to-digital converter only: The type of measurement being acquired by the ADC. For instance, if the resistance of a photocell is being measured through a voltage divider, this measurement would be "light".
Units | Analog-to-digital converter only: This is the unit of the measurement. With the above example of "light" as the measurement, the unit may be "lux" or "intensity".
Channel | Analog-to-digital converter only: This is the channel to obtain the voltage measurement from the ADC.
Gain | Analog-to-digital converter only: set the gain when acquiring the measurement.
Volts Min | Analog-to-digital converter only: What is the minimum voltage to use when scaling to produce the unit value for the database. For instance, if your ADC is not expected to measure below 0.2 volts for your particular circuit, set this to "0.2".
Volts Max | Analog-to-digital converter only: This is similar to the Min option above, however it is setting the ceiling to the voltage range. Units Min Analog-to-digital converter only: This value will be the lower value of a range that will use the Min and Max Voltages, above, to produce a unit output. For instance, if your voltage range is 0.0 - 1.0 volts, and the unit range is 1 - 60, and a voltage of 0.5 is measured, in addition to 0.5 being stored in the database, 30 will be stored as well. This enables creating calibrated scales to use with your particular circuit.
Units Max | Analog-to-digital converter only: This is similar to the Min option above, however it is setting the ceiling to the unit range.

### Sensor Verification

Sensor verification was introduced in an earlier version and was broken
when the system moved to its new software framework. It was a great
feature, and it's planned to be integrated into the latest version.

This allows the verification of a sensor's measurement with another
sensor's measurement. This feature is best utilized when you have two
sensors in the same location (ideally as close as possible). One sensor
(host) should be set up to use the other sensor (slave) to verify. The
host sensor should be used to operate the PID, as one feature of the
verification is the ability to disable the PID if the difference between
measurements is not within the range specified.

Setting | Description
--- | ---
GPIO | This is the sensor that will be used to verify the sensor measurement. The sensor will be read directly after the first sensor's measurement to verify whether the sensors have similar measurements.
Difference | This is the maximum measured measurement difference between the two sensors before an action is triggered (either notify by email or prevent PID from operating; more below).
Notification | If the measurements of the two sensors differ by more than the set *Difference*, an email will be sent to the address in the *Notification* field.
Stop PID | If the measurements of the two sensors differ by more than the set *Difference*, the PID controller will turn off.

Relays
------

Relays are electromechanical or solid-state devices that enable a small
voltage signal (such as from a microprocessor) to activate a much larger
voltage, without exposing the low -voltage system to the dangers of the
higher voltage.

Relays must be properly set up before PID regulation can be achieved.
Add and configure relays in the Relay tab. Set the "GPIO Pin" to the BCM
GPIO number of each pin that activates each relay. *On Trigger* should
be set to the signal that activates the relay (the device attached to
the relay turns on). If your relay activates when the potential across
the coil is 0-volts, set *On Trigger* to "Low", otherwise if your relay
activates when the potential across the coil is 3.3-volts (or whatever
switching voltage you are using, if not being driven by the GPIO pin),
set it to "High".

When a relay is initially added, the background of the new relay will be
yellow, indicating it is not configured. When properly configured, it
will either turn green, indicating the relay is activated (device is
on), or red, indicating the relay is inactivated (device is off).

Setting | Description
--- | ---
GPIO Pin | This is the GPIO that will be the signal to the relay.
Current Draw (amps) | The is the amount of current the device powered by the relay draws. Note: this value should be calculated based on the voltage set in the [Relay Usage Settings](#relay-usage-settings).
On Trigger | This is the state of the GPIO to signal the relay to turn the device on. HIGH will send a 3.3-volt signal and LOW will send a 0-volt signal. If you relay completes the circuit (and the device powers on) when a 3.3-volt signal is sent, then set this to HIGH. If the device powers when a 0-volt signal is sent, set this to LOW.
Start State | This specifies whether the relay should be ON or OFF when mycodo initially starts.
Seconds to turn On | This is a way to turn a relay on for a specific duration of time. This can be useful for testing the relays and powered devices or the measured effects a device may have on an environmental condition.

PIDs
----

A [proportional-derivative-integral (PID)
controller](https://en.wikipedia.org/wiki/PID_controller) is a control
loop feedback mechanism used throughout industry for controlling
systems. It efficiently brings a measurable condition, such as the
temperature, to a desired state and maintains it there with little
overshoot and oscillation. A well-tuned PID controller will raise to the
setpoint quickly, have minimal overshoot, and maintain the setpoint with
little oscillation.

PID settings may be changed while the PID is activated and the new
settings will take effect immediately. If settings are changed while the
controller is paused, the values will be used once the controller
resumes operation.

Setting | Description
--- | ---
Activate/Deactivate | Turn a particular PID controller on or off.
Pause | When paused, the PID will not turn on the associated relays, and settings can be changed without losing current PID output values.
Hold | When held, the PID will turn on the associated relays, and settings can be changed without losing current PID output values.
Resume | Resume a PID controller from being held or paused.
Setpoint | This is the specific point you would like the environment to be regaulted at. For example, if you would like the humidity regulated to 60%, enter 60.
Direction | This is the direction that you wish to regulate. For example, if you only require the temperature to be raised, set this to "Up," but if you require regulation up and down, set this to "Both."
Period | This is the duration between when the PID relay turns off amd when the sensor takes another measurement, the PID is updated, and the relay is turned on again for another duration.
Max Age | The time (in seconds) that the sensor measurement age is required to be less than. If the measurement is not younger than this age, the measurement is thrown out and the PID will not actuate the relay. This is a safety measure to ensure the PID is only using recent measurements.
Raise Relay | This is the relay that will cause the particular environmental condition to rise. In the case of raising the temperature, this may be a heating pad or coil.
Min Duration (raise) | This is the minimum that the PID output must be before the Up Relay turns on. If the PID output exceeds this minimum, the Up Relay will turn on for the PID output number of seconds.
Max Duration (raise) | This is the maximum duration the Up Relay is allowed to turn on for. If the PID output exceeds this number, the Up Relay will turn on for no greater than this duration of time.
Lower Relay | This is the relay that will cause the particular environmental condition to lower. In the case of lowering the CO~2~, this may be an exhaust fan.
Min Duration (lower) | This is the minimum that the PID output must be before the Down Relay turns on. If the PID output exceeds this minimum, the Down Relay will turn on for the PID output number of seconds.
Max Duration (lower) | This is the maximum duration the Down Relay is allowed to turn on for. if the PID output exceeds this number, the Down Relay will turn on for no greater than this duration of time.
K~P~ | Proportional coefficient (non-negative). Accounts for present values of the error. For example, if the error is large and positive, the control output will also be large and positive.
K~I~ | Integral coefficient (non-negative). Accounts for past values of the error. For example, if the current output is not sufficiently strong, the integral of the error will accumulate over time, and the controller will respond by applying a stronger action.
K~D~ | Derivative coefficient (non-negative). Accounts for predicted future values of the error, based on its current rate of change.
Integrator Min | The minimum allowed integrator value, for calculating Ki\_total: (Ki\_total = Ki \* integrator; and PID output = Kp\_total + Ki\_total + Kd\_total)
Integrator Max | The maximum allowed integrator value, for calculating Ki\_total: (Ki\_total = Ki \* integrator; and PID output = Kp\_total + Ki\_total + Kd\_total)

Timers
------

Timers enable a relay to be manipulated after specific durations of time
or at a specific times of the day. For *Duration Timers*, both the on
duration and the off duration can be defined and the timer will be
turned on and off for those durations until deactivated. For *Daily
Timers*, the start hour:minute can be set to turn a specific relay on or
off at the specific time of day.

LCDs
----

Data may be output to a liquid crystal display (LCD) for easy viewing.
There are only a few number fo LCDs that are supported. Only 16x2 and
20x4 character LCD displays with I<sup>2</sup>C backpacks are supported. Please
see the README for specific information regarding compatibility.

Setting | Description
--- | ---
Reset Flashing | If the LCD is flashing to alert you because it was instructed to do so by a triggered Conditional Statement, use this button to stop the flashing.
Type | Select either a 16x2 or 20x4 character LCD display.
I<sup>2</sup>C Address | Select the I<sup>2</sup>C to communicate with the LCD.
Multiplexer I<sup>2</sup>C Address | If the LCD is connected to a multiplexer, select the multiplexer I<sup>2</sup>C address.
Multiplexer Channel | If the LCD is connected to a multiplexer, select the multiplexer channel the LCD is connected to.
Period | This is the period of time (in seconds) between redrawing the LCD with new data.
Display Line \# | Select which measurement to display on each line of the LCD.

Controller Functions
====================

Conditional Statements
----------------------

A conditional statement is a way to perform certain actions based on
whether a condition is true. Conditional statements can be created for
both relays and sensors. Possible conditional statements include:

-   If Relay \#1 turns ON, turn Relay \#3 ON
-   If Relay \#1 turns ON, turn Relay \#4 ON for 40 seconds and notify
    critical-issue@domain.com
-   If Relay \#4 turns ON for 21 seconds, turn Relay \#5 ON for 50
    seconds
-   If Relay \#4 turns ON for 20 seconds, turn Relay \#1 OFF
-   If Humidity is Greater Than 80%, turn Relay \#4 ON for 40 seconds
-   If Humidity if Less Than 50%, turn Relay \#1 ON for 21 seconds,
    execute '/usr/local/bin/myscript.sh', and notify email@domain.com
-   If Temperature if Greater Than 35 C, deactivate PID \#1

Before activating any conditional statements or PID controllers, it's
advised to thoroughly explore all possible scenarios and plan a
configuration that eliminates conflicts. Then, trial run your
configuration before connecting devices to the relays. Some devices or
relays may respond atypically or fail when switched on and off in rapid
succession. Therefore, avoid creating an [infinite
loop](https://en.wikipedia.org/wiki/Loop_%28computing%29#Infinite_loops)
with conditional statements.

### Conditional Statement Actions

Setting | Description
--- | ---
Relay | Turn a relay on, off, or on for a duration of time.
Command | Execute a command in the linux shell (as user mycodo).
Activate PID | Activate a particular PID controller.
Deactivate PID | Deactivate a particular PID controller.
Email | Send an email containing information about the current condition that triggered the conditional to send the email.
Flash LCD | Have an LCD screen begin flashing in order to alert.
Photo | Capture a photo with the selected camera.
Email Photo | Capture a photo and email it as an attachment to the an email address.
Video | Capture a video of a set duration with the selected camera.
Email Video | Capture a video and email it as an attachment to the an email address.

Methods
-------

Methods allow different types of setpoint tracking in PID controllers.
Normally, a PID controller will regulate an environmental condition to a
specific setpoint. If you would like the setpoint to change over time,
this is called setpoint tracking. Setpoint tracking is useful for
applications such as reflow ovens, thermal cyclers (DNA replication),
mimicking natural daily cycles, and more.

### Universal Options

These options are shared with several method types.

Setting | Description
--- | ---
Start Time/Date | This is the start time of a range of time.
End Time/Date | This is the end time of a range of time.
Start Setpoint | This is the start setpoint of a range of setpoints.
End Setpoint | This is the end setpoint of a range of setpoints.

### Specific Method Options

#### Time/Date Method

A time/date method allows a specific time/date span to dictate the
setpoint. This is useful for long-running methods, that may take place
over the period of days, weeks, or months.

#### Duration Method

A duration method allows a specific durations of time to dictate the
setpoint. This is useful for when short periods of time are required in
a method, such as those that take place over the course of a few minutes
or hours. Each duration will stack on the previous duration, meaning a
newly-added start setpoint will begin from the previous entry's end
setpoint.

#### Daily (Time-Based) Method

The daily time-based method is similar to the time/date method, however
it will repeat every day. Therefore, it is essential that only the span
of one day be set in this method. Begin with the start time at 00:00:00
and end at 23:59:59 (or 00:00:00, which would be 24 hours from the
start). The start time must be equal or greater than the previous end
time.

#### Daily (Sine Wave) Method

The daily sine wave method defines the setpoint over the day based on a
sinusoidal wave. The sine wave is defined by y = [A \* sin(B \* x + C)]
+ D, where A is amplitude, B is frequency, C is the angle shift, and D
is the y-axis shift. This method will repeat daily.

#### Daily (Bezier Curve) Method

A daily Bezier curve method define the setpoint over the day based on a
cubic Bezier curve. If unfamiliar with a Bezier curve, it is recommended
you use the [graphical Bezier curve
generator](https://www.desmos.com/calculator/cahqdxeshd) and use the 8
variables it creates for 4 points (each a set of x and y). The x-axis
start (x3) and end (x0) will be automatically stretched or skewed to fit
within a 24-hour period and this method will repeat daily.

PID Tuning
----------

### PID Control Theory

The PID controller is the most common regulatory controller found in
industrial settings, for it"s ability to handle both simple and complex
regulation. The PID controller has three paths, the proportional,
integral, and derivative.

The **P**roportional takes the error and multiplies it by the constant
K~p~, to yield an output value. When the error is large, there will be a
large proportional output.

The **I**ntegral takes the error and multiplies it by K~i~, then
integrates it (K~i~ · 1/s). As the error changes over time, the integral
will continually sum it and multiply it by the constant K~i~. The
integral is used to remove perpetual error in the control system. If
using K~p~ alone produces an output that produces a perpetual error
(i.e. if the sensor measurement never reaches the Set Point), the
integral will increase the output until the error decreases and the Set
Point is reached.

The **D**erivative multiplies the error by K~d~, then differentiates it
(K~d~ · s). When the error rate changes over time, the output signal
will change. The faster the change in error, the larger the derivative
path becomes, decreasing the output rate of change. This has the effect
of dampening overshoot and undershoot (oscillation) of the Set Point.

* * * * *

Using temperature as an example, the Process Variable (PV) is the
measured temperature, the Setpoint (SP) is the desired temperature, and
the Error (e) is the distance between the measured temperature and the
desired temperature (indicating if the actual temperature is too hot or
too cold and to what degree). The error is manipulated by each of the
three PID components, producing an output, called the Manipulated
Variable (MV) or Control Variable (CV). To allow control of how much
each path contributes to the output value, each path is multiplied by a
gain (represented by *K~P~*, *K~I~*, and *K~D~*). By adjusting the
gains, the sensitivity of the system to each path is affected. When all
three paths are summed, the PID output is produced. If a gain is set to
0, that path does not contribute to the output and that path is
essentially turned off.

The output can be used a number of ways, however this controller was
designed to use the output to affect the measured value (PV). This
feedback loop, with a *properly tuned* PID controller, can achieve a set
point in a short period of time, maintain regulation with little
oscillation, and respond quickly to disturbance.

Therefor, if one would be regulating temperature, the sensor would be a
temperature sensor and the feedback device(s) would be able to heat and
cool. If the temperature is lower than the Set Point, the output value
would be positive and a heater would activate. The temperature would
rise toward the desired temperature, causing the error to decrease and a
lower output to be produced. This feedback loop would continue until the
error reaches 0 (at which point the output would be 0). If the
temperature continues to rise past the Set Point (this is may be
acceptable, depending on the degree), the PID would produce a negative
output, which could be used by the cooling device to bring the
temperature back down, to reduce the error. If the temperature would
normally lower without the aid of a cooling device, then the system can
be simplified by omitting a cooler and allowing it to lower on its own.

Implementing a controller that effectively utilizes *K~P~*, *K~I~*, and
*K~D~* can be challenging. Furthermore, it is often unnecessary. For
instance, the *K~I~* and *K~D~* can be set to 0, effectively turning
them off and producing the very popular and simple P controller. Also
popular is the PI controller. It is recommended to start with only
*K~P~* activated, then experiment with *K~P~* and *K~I~*, before finally
using all three. Because systems will vary (e.g. airspace volume, degree
of insulation, and the degree of impact from the connected device,
etc.), each path will need to be adjusted through experimentation to
produce an effective output.

### Quick Setup Examples

These example setups are meant to illustrate how to configure regulation
in particular directions, and not to achieve ideal values to configure
your *K~P~*, *K~I~*, and *K~D~* gains. There are a number of online
resources that discuss techniques and methods that have been developed
to determine ideal PID values (such as
[here](http://robotics.stackexchange.com/questions/167/what-are-good-strategies-for-tuning-pid-loops),
[here](http://innovativecontrols.com/blog/basics-tuning-pid-loops),
[here](https://hennulat.wordpress.com/2011/01/12/pid-loop-tuning-101/),
[here](http://eas.uccs.edu/wang/ECE4330F12/PID-without-a-PhD.pdf), and
[here](http://www.atmel.com/Images/doc2558.pdf)) and since there are no
universal values that will work for every system, it is recommended to
conduct your own research to understand the variables and essential to
conduct your own experiments to effectively implement them.

Provided merely as an example of the variance of PID values, one of my
setups had temperature PID values (up regulation) of *K~P~* = 30, *K~I~*
= 1.0, and *K~D~* = 0.5, and humidity PID values (up regulation) of
*K~P~* = 1.0, *K~I~* = 0.2, and *K~D~* = 0.5. Furthermore, these values
may not have been optimal but they worked well for the conditions of my
environmental chamber.

### Exact Temperature Regulation

This will set up the system to raise and lower the temperature to a
certain level with two regulatory devices (one that heats and one that
cools).

Add a sensor, then save the proper device and pin/address for each
sensor and activate the sensor.

Add two relays, then save each GPIO and On Trigger state.

Add a PID, then select the newly-created sensor. Change *Setpoint* to
the desired temperature, *Regulate Direction* to "Both". Set *Raise
Relay* to the relay attached to the heating device and the *Lower Relay*
to the relay attached to the cooling device.

Set *K~P~* = 1, *K~I~* = 0, and *K~D~* = 0, then activate the PID.

If the temperature is lower than the Set Point, the heater should
activate at some interval determined by the PID controller until the
temperature rises to the set point. If the temperature goes higher than
the Set Point (or Set Point + Buffer), the cooling device will activate
until the temperature returns to the set point. If the temperature is
not reaching the Set Point after a reasonable amount of time, increase
the *K~P~* value and see how that affects the system. Experiment with
different configurations involving only *Read Interval* and *K~P~* to
achieve a good regulation. Avoid changing the *K~I~* and *K~D~* from 0
until a working regulation is achieved with *K~P~* alone.

View graphs in the 6 to 12 hour time span to identify how well the
temperature is regulated to the Setpoint. What is meant by
well-regulated will vary, depending on your specific application and
tolerances. Most applications of a PID controller would like to see the
proper temperature attained within a reasonable amount of time and with
little oscillation around the Setpoint.

Once regulation is achieved, experiment by reducing *K~P~* slightly
(\~25%) and increasing *K~I~* by a low amount to start, such as 0.1 (or
lower, 0.01), then start the PID and observe how well the controller
regulates. Slowly increase *K~I~* until regulation becomes both quick
and with little oscillation. At this point, you should be fairly
familiar with experimenting with the system and the *K~D~* value can be
experimented with once both *K~P~* and *K~I~* have been tuned.

### High Temperature Regulation

Often the system can be simplified if two-way regulation is not needed.
For instance, if cooling is unnecessary, this can be removed from the
system and only up-regulation can be used.

Use the same configuration as the [Exact Temperature
Regulation](#exact-temperature-regulation) example, except change
*Regulate Direction* to "Raise" and do not touch the "Down Relay"
section.

Miscellaneous
=============

Graphs
------

There are two different types of graphs, Live and Asynchronous.

### Live Graphs

A graphical data display that is useful for viewing data sets spanning
relatively short periods of time (hours/days/weeks). Select a time frame
to view data and continually updating data from new sensor measurements.
Multiple graphs can be created on one page that enables a dashboard to
be created of graphed sensor data. Each graphs may have one or more
sensor measurement, relay duration, or PID setpoint rendered onto it.
Several live graph options exist, such as the time period (x-axis) and
line colors, as well as navigation and data/image export options. To
edit graph options, select the plus sign on the top-right of a graph.

### Asynchronous Graphs

A graphical data display that is useful for viewing data sets spanning
relatively long periods of time (weeks/months/years), which could be
very data- and processor-intensive to view as a Live Graph. Select a
time frame and data will be loaded from that time span, if it exists.
The first view will be of the entire selected data set. For every
view/zoom, 700 data points will be loaded. If there are more than 700
data points recorded for the time span selected, 700 points will be
created from an averaging of the points in that time span. This enables
much less data to be used to navigate a large data set. For instance, 4
months of data may be 10 megabytes if all of it were downloaded.
However, when viewing a 4 month span, it's not possible to see every
data point of that 10 megabytes, and aggregating of points is
inevitable. With asynchronous loading of data, you only download what
you see. So, instead of downloading 10 megabytes every graph load, only
\~50kb will be downloaded until a new zoom level is selected, at which
time only another \~50kb is downloaded.

Note: Live Graphs require measurements to be acquired, therefore at
least one sensor needs to be added and activated in order to display
live data.

Camera
------

Once a cameras has been set up (in the [Camera
Settings](#camera-settings)), it may be used to capture still images,
create time-lapses, and stream video. Cameras may also be used with
[Conditional Statements](#conditional-statements) to trigger a camera
image or video capture (as well as the ability to email the image/video
with a notification).

Relay Usage
-----------

Relay usage statistics are calculated for each relay, based on how long
the relay has been powered, the current draw of the device connected to
the relay, and other [Relay Usage Settings](#relay-usage-settings).

System Backup
-------------

A backup is made to /var/Mycodo-backups when the system is upgraded
through the web interface or the upgrade script.

System Restore
--------------

If you need to restore a backup, do the following, changing the
appropriate directory names with these commands, changing 'user' to your
user name:

    sudo mv /home/user/Mycodo /home/user/Mycodo_old
    sudo cp -a /var/Mycodo-backups/Mycodo-TIME-COMMIT /home/user/Mycodo
    sudo /bin/bash ~/Mycodo/mycoco/scripts/upgrade_post.sh

Troubleshooting
===============

## Daemon Not Running

-   Check the Logs: From the ```[Gear Icon]``` -> ```Mycodo Logs``` page, check the Daemon Log
    for any errors. If the issue began after an upgrade, also check the
    Upgrade Log for indications of an issue.
-   Determine if the Daemon is Running: Execute
    `ps aux | grep '/var/www/mycodo/env/bin/python /var/www/mycodo/mycodo/mycodo_daemon.py'`
    in a terminal and look for an entry to be returned. If nothing is
    returned, the daemon is not running.
-   Daemon Lock File: If the daemon is not running, make sure the daemon
    lock file is deleted at `/var/lock/mycodo.pid`. The daemon cannot
    start if the lock file is present.
-   If a solution could not be found after investigating the above
    suggestions, submit a [New Mycodo
    Issue](https://github.com/kizniche/Mycodo/issues/new) on github.

## More

Check out the [Diagnosing Mycodo Issues Wiki
Page](https://github.com/kizniche/Mycodo/wiki/Diagnosing-Issues) on
github for more information about diagnosing issues.

Appendix
========

Temperature Sensors
-------------------

### Raspberry Pi

The Raspberry Pi has an integrated temperature sensor on the BCM2835 SoC
that measure the temperature of the CPU/GPU. This is the easiest sensor
to set up in Mycodo, as it is immediately available to be used.

### Atlas Scientific PT-1000

The PT1000 temperature probe is a resistance type thermometer. Where PT
stands for platinum and 1000 is the measured resistance of the probe at
0&deg;C in ohms (1k at 0&deg;C).

#### Specifications

 - Accuracy &plusmn;(0.15 + (0.002\*t))
 - Probe type: Class A Platinum, RTD (resistance temperature detector)
 - Cable length: 81cm (32")
 - Cable material: Silicone rubber
 - 30mm sensing area (304 SS)
 - 6mm Diameter
 - BNC Connector
 - Reaction Time: 90% value in 13 seconds
 - Probe output: analog
 - Full temperature sensing range: -200&deg;C to 850&deg;C
 - Cable max temp 125&deg;C
 - Cable min temp -55&deg;C

### DS18B20

The DS18B20 is a 1-Wire digital temperature sensor from Maxim IC. Each
sensor has a unique 64-Bit Serial number, allowing for a huge number of
sensors to be used on one data bus (GPIO 4).

#### Specifications

 - Usable temperature range: -55 to 125&deg;C (-67&deg;F to +257&deg;F)
 - 9 to 12 bit selectable resolution
 - Uses 1-Wire interface- requires only one digital pin for communication
 - Unique 64 bit ID burned into chip
 - Multiple sensors can share one pin
 - &plusmn;0.5&deg;C Accuracy from -10&deg;C to +85&deg;C
 - Temperature-limit alarm system
 - Query time is less than 750ms
 - Usable with 3.0V to 5.5V power/data

### TMP006, TMP007

The TMP006 Breakout can measure the temperature of an object without
making contact with it. By using a thermopile to detect and absorb the
infrared energy an object is emitting, the TMP006 Breakout can determine
how hot or cold the object is.

#### Specifications

 - Usable temperature range: -40&deg;C to 125&deg;C
 - Optimal operating voltage of 3.3V to 5V (tolerant up to 7V max)

Temperature, Humidity Sensors
-----------------------------

### AM2315

#### Specifications

 - 0-100% humidity readings with 1% (10-90% RH) and 3% (0-10% RH and 90-100% RH) accuracy
 - -20 to 80&deg;C temperature readings &plusmn;0.1&deg;C typical accuracy
 - 3.5 to 5.5V power and I/O
 - 10 mA max current use during conversion (while requesting data)
 - No more than 0.5 Hz sampling rate (once every 2 seconds)

### DHT11

#### Specifications

 - 3 to 5V power and I/O
 - 2.5mA max current use during conversion (while requesting data)
 - 20-80% humidity readings with 5% accuracy
 - 0-50&deg;C temperature readings &plusmn;2&deg;C accuracy
 - No more than 1 Hz sampling rate (once every second)

### DHT22, AM2302

Compared to the DHT11, this sensor is more precise, more accurate and
works in a bigger range of temperature/humidity, but its larger and more
expensive.

#### Specifications

 - 0-100% humidity readings with 2% (10-90% RH) and 5% (0-10% RH and 90-100% RH) accuracy
 - -40 to 80&deg;C temperature readings &plusmn;0.5&deg;C accuracy
 - 3 to 5V power and I/O
 - 2.5mA max current use during conversion (while requesting data)
 - No more than 0.5 Hz sampling rate (once every 2 seconds)

### HTU21D

#### Specifications

 - 0-100% humidity readings with 2% (20-80% RH) and 2%-5% (0-20% RH and 80-100% RH) accuracy
 - Optimum accuracy measurements within 5 to 95% RH
 - -30 to 90&deg;C temperature readings &plusmn;1&deg;C typical accuracy

### SHT1x

(SHT10, SHT11, SHT15)

#### Specifications

 - 0-100% humidity readings with 2%-5% (10-90% RH) and 2%-7.5% (0-10% RH and 90-100% RH) accuracy
 - -40 to 125&deg;C temperature readings &plusmn;0.5&deg;C, &plusmn;0.4&deg;C, and &plusmn;0.3&deg;C typical accuracy (respectively)
 - 2.4 to 5.5V power and I/O
 - No more than 0.125 Hz sampling rate (once every 8 seconds)

### SHT7x

(SHT71, SHT75)

#### Specifications

 - 0-100% humidity readings with 2%-3% (10-90% RH) and 2%-5% (0-10% RH and 90-100% RH) accuracy
 - -40 to 125&deg;C temperature readings &plusmn;0.4&deg;C and &plusmn;0.3&deg;C typical accuracy (respectively)
 - 2.4 to 5.5V power and I/O
 - No more than 0.125 Hz sampling rate (once every 8 seconds)

CO~2~ Sensors
-------------

### K-30

#### Specifications

 - 0 – 10,000 ppm (0-5,000 ppm within specifications)
 - Repeatability: &plusmn;20 ppm &plusmn;1% of measured value within specifications
 - Accuracy: &plusmn;30 ppm &plusmn;3% of measured value within specifications
 - Non-dispersive infrared (NDIR) technology
 - Sensor life expectancy: \> 15 years
 - Self-diagnostics: complete function check of the sensor module
 - Warm-up time: \< 1 min. (@ full specs \< 15 min)
 - 0.5 Hz sampling rate (once every 2 seconds)

Moisture Sensors
----------------

### Chirp

The Chirp sensor measures moisture, light, and temperature.

#### Specifications

 - Vin: 3 to 5V
 - I<sup>2</sup>C 7-bit address 0x77

Pressure Sensors
----------------

### BMP085, BMP180

The BMP180 is the next-generation of sensors from Bosch, and replaces
the BMP085. It is completely identical to the BMP085 in terms of
firmware/software/interfacing.

#### Specifications

 - 300-1100 hPa (9000m to -500m above sea level)
 - Up to 0.03hPa / 0.25m resolution
 - -40 to +85&deg;C operational range
 - &plusmn;2&deg;C temperature accuracy
 - Vin: 3 to 5V
 - Logic: 3 to 5V compliant
 - I<sup>2</sup>C 7-bit address 0x77

Luminosity Sensors
------------------

### BH1750

The BH1750 is an I<sup>2</sup>C luminosity sensor that provides a digital value
in lux (Lx) over a range of 1 - 65535 lx.

### TSL2561

The TSL2561 SparkFun Luminosity Sensor Breakout is a sophisticated light
sensor which has a flat response across most of the visible spectrum.
Unlike simpler sensors, the TSL2561 measures both infrared and visible
light to better approximate the response of the human eye. And because
the TSL2561 is an integrating sensor (it soaks up light for a
predetermined amount of time), it is capable of measuring both small and
large amounts of light by changing the integration time.

#### Specifications

 - Light range: 0.1 - 40k+ Lux
 - Vin: 3V and a low supply
 - Max current: 0.6mA.

I<sup>2</sup>C Multiplexers
------------------

### TCA9548A

The TCA9548A I<sup>2</sup>C allows multiple sensors that have the same I<sup>2</sup>C
address to be used with mycodo (such as the AM2315). The multiplexer has
a selectable address, from 0x70 through 0x77, allowing up to 8
multiplexers to be used at once. With 8 channels per multiplexer, this
allows up to 64 devices with the same address to be used.

Analog to Digital Converters
----------------------------

### ADS1x15

(ADS1015, ADS1115)

#### Specifications

 - Interface: I<sup>2</sup>C
 - I<sup>2</sup>C 7-bit addresses 0x48 - 0x4B
 - Input channels: 2 (differential), 4 (single-ended)
 - Power: 2.0V to 5.5V
 - Sample Rate: 1015: 128SPS to 3.3kSPS, 1115: 8SPS to 860SPS
 - Resolution: 1015: 12-bit, 1115: 16-bit

### MCP342x

(MCP3422, MCP3423, MCP3424, MCP3426, MCP3427, MCP3428)

#### Specifications

 - Interface: I<sup>2</sup>C
 - I<sup>2</sup>C 7-bit addresses 0x68 - 0x6F
 - MCP3422: 2 channel, 12, 14, 16, or 18 bit
 - MCP3423: 2 channel, 12, 14, 16, or 18 bit
 - MCP3424: 4 channel, 12, 14, 16, or 18 bit
 - MCP3426: 2 channel, 12, 14, or 16 bit
 - MCP3427: 2 channel, 12, 14, or 16 bit
 - MCP3428: 4 channel, 12, 14, or 16 bit

Schematics and diagrams
-----------------------

### Pi Schematics

#### Pi, 4 Relays, 4 120/240-volt AC outlets, and 1 DS18B20 sensor

![Figure: Pi and 4 relays and outlets schematic](manual_images/Schematic-Pi-4-relays.png)

#### Pi, 8 Relays, and 8 120/240-volt AC outlets

![Figure: Pi and 8 relays and outlets schematic](manual_images/Schematic-Pi-8-relays.png)