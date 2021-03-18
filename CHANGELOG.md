## 8.9.3 (Unreleased)

### Bugfixes

 - Fix camera paths not saving ([#955](https://github.com/kizniche/mycodo/issues/955))
 - Fix returning pylint3 report after saving Python Code

### Miscellaneous

 - Add Units kilowatt-hour and Watt


## 8.9.2 (2021-03-16)

This bugfix release changes how sessions are handled and as a result will log all users out following the upgrade.

### Bugfixes

 - Fix Function measurements not appearing in some dropdowns
 - Fix displaying saved Custom Option values when Inputs/Outputs have Custom Actions ([#952](https://github.com/kizniche/mycodo/issues/952))
 - Fix silent failures when cookies are too large ([#950](https://github.com/kizniche/mycodo/issues/950))
 - Fix use of select_measurement_channel custom option in controllers ([#953](https://github.com/kizniche/mycodo/issues/953))
 - Fix error-handling of erroneous measurements/units ([#949](https://github.com/kizniche/mycodo/issues/949))


## 8.9.1 (2021-03-13)

### Bugfixes

 - Fix API deactivating controller in database ([#944](https://github.com/kizniche/mycodo/issues/944))
 - Fix invalid conversion ([#947](https://github.com/kizniche/mycodo/issues/947))
 - Fix inability to save MQTT Input ([#946](https://github.com/kizniche/mycodo/issues/946))
 - Fix Camera Widget ([#948](https://github.com/kizniche/mycodo/issues/948))


## 8.9.0 (2021-03-08)

This release contains bug fixes and several new types of Inputs and Outputs. These include stepper motors, digital-to-analog converters, a multi-channel PWM output, as well as an input to acquire current and future weather conditions.

This release also deprecates Math controllers. Current Math controllers will continue to function, but new Math controllers cannot be created. Instead, all Math controller functionality has been ported to Functions (Setup -> Function page), in order to reduce complexity and improve customizability. Much like Inputs and Outputs, Functions are single-file modules that can be created by users and imported. Take a look at the Mycodo/mycodo/functions directory for the built-in Function modules.

The new weather input acquires current and future weather conditions from openweathermap.org with either a city (200,000 to choose from) or latitude/longitude for a location and a time frame from the present up to 7 days in the future, with a resolution of days or hours. An API key to use the service is free and the measurements returned include temperature (including minimum and maximum if forecasting days in the future), humidity, dew point, pressure, wind speed, and wind direction. This can be useful for incorporating current or future weather conditions into your conditional controllers or other functions or calculations. For instance, you may prevent Mycodo from watering your outdoor plants if the forecasted temperature in the next 12 to 24 hours is below freezing. You may also want to be alerted by email if the forecasted weather conditions are extreme. Not everyone wants to set up a weather station, but might still want to have local outdoor measurements, so this input was made to bridge that gap.

### Bugfixes

 - Fix broken Output API get/post calls
 - Fix selecting output channels in custom functions
 - Fix Autotune PID Function ([#876](https://github.com/kizniche/mycodo/issues/876))
 - Fix issue with LockFile not locking
 - Fix Output State and Output Duration On Conditional Conditions ([#879](https://github.com/kizniche/mycodo/issues/879))
 - Fix not showing camera stream buttons for cameras libraries that don't have stream support ([#899](https://github.com/kizniche/mycodo/issues/899))
 - Fix Clock Pin option showing twice for UART Inputs
 - Fix MCP3008 Input error ([#902](https://github.com/kizniche/mycodo/issues/902))
 - Fix Input Measurement option Invert Scale not displaying properly ([#902](https://github.com/kizniche/mycodo/issues/902))
 - Fix MQTT output being able to set 0 to disable option
 - Fix compounding of Function Action return messages in Conditionals
 - Fix ADS1015 and ADS1115 inputs only measuring channel 0 ([#911](https://github.com/kizniche/mycodo/issues/911))
 - Fix install of pyusb dependency of Adafruit_Extended_Bus ([#863](https://github.com/kizniche/mycodo/issues/863))
 - Fix Message and New Line options in Custom Options
 - Fix Conditional sample_rate not being set from Config
 - Fix Saving Angular and Solid Gauge Widget stop values ([#916](https://github.com/kizniche/mycodo/issues/916))
 - Fix uncaught exception if trying to acquire image when opencv can't detect a camera ([#917](https://github.com/kizniche/mycodo/issues/917))
 - Fix displaying input/output pypi.org dependencies with "=="
 - Fix pressure measurement in BME680 and BME280 Inputs ([#923](https://github.com/kizniche/mycodo/issues/923))
 - Fix controllers disappearing following reorder ([#925](https://github.com/kizniche/mycodo/issues/925))
 - Fix Inputs that use w1thermsensor ([#926](https://github.com/kizniche/mycodo/issues/926))
 - Fix issue generating documentation for similar Inputs/Outputs/Widgets
 - Fix execution of Input stop_input()
 - Fix Input Pre-Outputs not turning on
 - Fix Output not activating for Camera
 - Fix PWM trigger and Duration Method ([#937](https://github.com/kizniche/mycodo/issues/937))
 - Fix stopping Trigger Controllers ([#940](https://github.com/kizniche/mycodo/issues/940))
 - Fix Tags not appearing in Graph Widgets
 - Fix variable measurement Inputs saving correctly
 - Fix detection of custom_option save type (CSV or JSON) for proper parsing
 - Fix saving of unchecked checkboxes when using forms

### Features

 - Add Digital-to-Analog Converter output support (and add MCP4728) ([#893](https://github.com/kizniche/mycodo/issues/893))
 - Add Stepper Motor Controller output support (and add DRV8825) ([#857](https://github.com/kizniche/mycodo/issues/857))
 - Add Output: GrovePi multi-channel relay I2C board
 - Add Output: PCA9685 16-channel PWM servo/LED controller
 - Add Input: MAX31865 (CircuitPython) ([#900](https://github.com/kizniche/mycodo/issues/900))
 - Add Input: Generic Hall Effect Flow sensor
 - Add Input: INA219 current sensor
 - Add Input: Grove Pi DHT11/22 sensor
 - Add Input: HC-SR04 Ultrasonic Distance sensor
 - Add Input: SCD30 CO2/Humidity/Temperature sensor
 - Add Input: Current Weather from OpenWeatherMap.org (Free API Key, Latitude/Longitude, 200,000 cities, Humidity/Temperature/Pressure/Dewpoint/Wind Speed/Wind Direction)
 - Add Input: Forecast Hourly/Daily Weather from OpenWeatherMap.org (Free API Key, , Humidity/Temperature/Pressure/Dewpoint)
 - Add Input: Raspberry Pi Sense HAT (humidity/temperature/pressure/compass/magnetism/acceleration/gyroscope)
 - Add Input: Xiaomi Mijia LYWSD03MMC
 - Add Input: Atlas Scientific CO2 sensor
 - Add Input: AHTx0 Temperature/Humidity sensor
 - Add Input: BME680 (Circuitpython)
 - Add measurements to Custom Controllers
 - Add Measurement and Unit: Speed, Meters/Second
 - Add Measurement and Unit: Direction, Bearing
 - Add Conversions: m/s <-> mph <-> knots, hour <-> minutes and seconds
 - Add LCD: Grove RGB LCD
 - Add Function: Bang-bang/hysteretic
 - Add Function Action: Output Value
 - Add Function Action: Set LCD Backlight Color
 - Add configurable link for navbar brand link
 - Add User option to Shell Command Function Action
 - Add Message and New Line options to Custom Options of Outputs
 - Add set_custom_option/get_custom_option to Conditionals ([#901](https://github.com/kizniche/mycodo/issues/901))
 - Add ability to login with username/password using MQTT Input and Outputs
 - Add ability to use Custom Channel Options with Inputs (first used in MQTT Input)
 - Add Custom Functions/Inputs/Outputs/Widgets to Settings Export/Import
 - Add user_scripts directory for user code that's preserved during upgrade/export/import ([#930](https://github.com/kizniche/mycodo/issues/930))
 - Add pin mode option (float, pull-up, pull-down) for Edge and State Inputs
 - Add Method: Cascaded Method, allows combining (multiply) any number of existing methods ([discussion](https://kylegabriel.com/forum/general-discussion/refactor-method-implementation-to-enable-further-methods/))
 - Add Functions and to API
 - Add missing Input Channels to Input API calls

### Miscellaneous

 - Remove lirc
 - Change widget title styles
 - Fix GCC warnings ([#906](https://github.com/kizniche/mycodo/issues/906))
 - Remove default user "pi" with "mycodo" (for compatibility with non-Raspberry Pi operating systems)
 - Update pyusb to 1.1.1
 - Refactor Edge detection Input
 - Refactor method implementation from single large method into multiple small classes
 - Changed duration method start- and end-time handling
 - Port Math controllers to Functions: Equation (Single/Multi), Difference, Statistics (Single/Multi), Average (Single/Multi), Sum (Single/Multi), Wet-Bulb Humidity, Redundancy, Vapor Pressure Deficit, Verification
 - Deprecate Math controllers
 - Remove Math controllers from and add Functions to Live page


## 8.8.8 (2020-10-30)

### Bugfixes

 - Fix PiOLED (CircuitPython) ([#842](https://github.com/kizniche/mycodo/issues/842))

### Miscellaneous

 - Update Polish translations


## 8.8.7 (2020-10-27)

### Bugfixes

 - Fix missing default values when adding new controllers ([#868](https://github.com/kizniche/mycodo/issues/868))
 - Fix catching loss of internet connection during upgrade ([#869](https://github.com/kizniche/mycodo/issues/869))
 - Fix Function Actions Output PWM and Output PWM Ramp not working ([#865](https://github.com/kizniche/mycodo/issues/865))
 - Fix dependencies not being installed for LCDs
 - Fix saving when missing/malformed custom_options JSON present ([#866](https://github.com/kizniche/mycodo/issues/866))

### Features

 - Add LCDs: 128x32 and 128x64 PiOLED using the Adafruit CircuitPython library ([#842](https://github.com/kizniche/mycodo/issues/842))


## 8.8.6 (2020-10-07)

### Bugfixes

 - Fix order of Atlas Scientific pH sensor calibration points ([#861](https://github.com/kizniche/mycodo/issues/861))

### Features

 - Add Polish translation


## 8.8.5 (2020-10-01)

### Bugfixes

 - Fix Output Widgets not able to control outputs
 - Fix ADS1256 ([#854](https://github.com/kizniche/mycodo/issues/854))
 - Fix PID controllers not obeying minimum off duration ([#859](https://github.com/kizniche/mycodo/issues/859))


## 8.8.4 (2020-09-28)

### Bugfixes

 - Increase nginx proxy buffer to accommodate large headers ([#849](https://github.com/kizniche/mycodo/issues/849))
 - Fix URL generation for cameras ([#850](https://github.com/kizniche/mycodo/issues/850))
 - Fix display of Output data on Asynchronous Graphs ([#847](https://github.com/kizniche/mycodo/issues/847))


## 8.8.3 (2020-09-15)

### Bugfixes

 - Fix inability to create Angular Gauge Widget with more than 4 stops ([#844](https://github.com/kizniche/mycodo/issues/844))
 - Fix issue with Python Code Input ([#846](https://github.com/kizniche/mycodo/issues/846))
 - Fix issue with install ([#845](https://github.com/kizniche/mycodo/issues/845))


## 8.8.2 (2020-09-13)

### Bugfixes

 - Fix PID Controller not operating ([#843](https://github.com/kizniche/mycodo/issues/843))
 - Fix inability to switch any output except channel 0 from web interface ([#840](https://github.com/kizniche/mycodo/issues/840))
 - Minor fixes for PCF8574 Output
 - Fix Atlas Pump recording two pump durations

### Features

 - Add ability to select method in Input/Output/Function controller custom options


## 8.8.1 (2020-09-09)

### Bugfixes

 - Fix partially broken upgrade to new output system
 - Fix GPIO output startup states


## 8.8.0 (2020-09-08)

This release changes the Output framework to add the ability for a single Output to control multiple channels. This was originally based on the PCF8574 8-bit I/O Expander, which allows 8 additional IO pins to be controlled via the I2C bus, but applies to any other output device with more than one channel. As a result of this change, you will need to update any Custom Outputs to follow the new format (see /mycodo/outputs directory).

### Bugfixes

 - Fix inability to save Python Code Input settings ([#827](https://github.com/kizniche/mycodo/issues/827))
 - Fix Cameras not appearing in Camera Widget ([#828](https://github.com/kizniche/mycodo/issues/828))
 - Fix inability to save Pause PID Function Action ([#836](https://github.com/kizniche/mycodo/issues/836))
 - Fix error diaplying Measurement or Gauge Widgets with Math controllers using non-default units ([#831](https://github.com/kizniche/mycodo/issues/831))
 - Fix default values not displaying for Input/Output Custom Actions
 - Fix some apt packages being detected as installed when they are not installed
 
### Features

 - Convert Input module custom_options from CSV to JSON
 - Add Anyleaf ORP and pH Inputs ([#825](https://github.com/kizniche/Mycodo/pull/825))

### Miscellaneous

 - Remove unused Output selection in Methods


## 8.7.2 (2020-08-23)

### Bugfixes

 - Fix issue displaying Measurement Widgets when a Math measurement is selected ([#817](https://github.com/kizniche/mycodo/issues/817))
 - Fix inability to generate Widget HTML ([#817](https://github.com/kizniche/mycodo/issues/817), [#822](https://github.com/kizniche/mycodo/issues/822))

### Features

 - Add ability to duplicate a dashboard and its widgets ([#812](https://github.com/kizniche/mycodo/issues/812))


## 8.7.1 (2020-08-10)

### Bugfixes

 - Remove copy of widget HTML files during upgrade


## 8.7.0 (2020-08-10)

This update includes the final refactoring of the output system to accommodate output modules that can operate multiple different types of output types. For instance, a peristaltic pump can be instructed to turn on for a duration or instructed to pump a volume. As a result of the output framework being modified to accommodate this, the duty_cycle parameter was removed from ```output_on_off()``` and ```output_on()``` functions of the ```DaemonControl``` class of mycodo_client.py. As a result, if you were previously using either of these function, you will need to add the parameter ```output_type='pwm'``` and change the ```duty_cycle``` parameter to ```amount```. For example, ```output_on(output_id, duty_cycle=50)``` would need to be changed to ```output_on(output_id, output_type='pwm', amount=50)```, and ```output_on_off(output_id, 'on', duty_cycle=50)``` to ```output_on_off(output_id, 'on', output_type='pwm', amount=50)```.

This update also adds the ability to import custom Widget modules. Much like custom Inputs, Outputs, and Functions, you can now create and import your own single-file Widget module that allow new widgets to be added to a dashboard.

### Bugfixes

 - Fix issue installing Python modules ([#804](https://github.com/kizniche/mycodo/issues/804))
 - Fix inability to save PID options when On/Off output selected ([#805](https://github.com/kizniche/mycodo/issues/805))
 - Fix graph shift issues
 - Fix PID Input/Math Setpoint Tracking unit and integer issue ([#811](https://github.com/kizniche/mycodo/issues/811))
 - Fix PID Controller debug logging ([#811](https://github.com/kizniche/mycodo/issues/811))
 - Fix bug in password reset function that would allow an attacker to discover if a user name doesn't exist

### Features

 - Add Output: On/Off MQTT Publish
 - Add Output information links
 - Add ability to download Mycodo Backups ([#803](https://github.com/kizniche/mycodo/issues/803))
 - Add ability to import custom Widget modules
 - Add Widget Controller for background widget processes
 - Add Widget: Python Code ([#803](https://github.com/kizniche/mycodo/issues/803))
 - Add an option to the password reset function to save the reset code to a file

### Miscellaneous

 - Deprecate duty_cycle parameter of output functions
 - Remove graph Shift X-Axis option
 - Move Autotune from PID Controller to Separate PID Autotune Controller ([#811](https://github.com/kizniche/mycodo/issues/811))


## 8.6.4 (2020-07-25)

### Bugfixes

 - Fix issue displaying lines 5-8 on SD1306 LCDs ([#800](https://github.com/kizniche/mycodo/issues/800))
 - Fix Atlas Scientific Pump duration unit issues ([#801](https://github.com/kizniche/mycodo/issues/801))

### Features

 - Add Inputs: Ads1115 (Circuit Python library), ADS1015 (Circuit Python library)
 - Add Input: BMP280 (bmp280-python library, includes ability to set forced mode) ([#608](https://github.com/kizniche/mycodo/issues/608))

### Miscellaneous

 - Deprecate Input using the Adafruit_ADS1x15 library


## 8.6.3 (2020-07-25)

### Bugfixes

 - Fix ADS1x15 Input


## 8.6.2 (2020-07-25)

### Bugfixes

 - Fix DS18S20 Input module ([#796](https://github.com/kizniche/mycodo/issues/796))
 - Fix Peristaltic Pump Outputs unable to turn on for durations ([#799](https://github.com/kizniche/mycodo/issues/799))

### Features

 - Add a ([Building a Custom Input Module wiki page](https://github.com/kizniche/Mycodo/wiki/Building-a-Custom-Input)

### Miscellaneous

 - Improve custom output framework
 - Consolidate locking code to utils/lockfile.py


## 8.6.1 (2020-07-22)

### Bugfixes

 - Fix Wireless 315/433 MHz Output module


## 8.6.0 (2020-07-22)

This update adds a Generic Peristaltic Pump Output to compliment the Atlas Scientific Peristaltic Pump Output. Generic peristaltic pumps are less expensive but often have acceptable dispensing accuracy. Once your pump's flow rate has been measured and this rate set in the Output options, your pump can be used to dispense specific volumes of liquid just like the Atlas Scientific pumps. This release also enables pumps to dispense for durations of time in addition to specific volumes (once calibrated). So, you can now operate a PID controller or other functions/controllers that instruct a pump to dispense for a duration in seconds or a volume in milliliters.

In this update, the Atlas Scientific Peristaltic Pump Output duration units have been changed form minutes to seconds, to align with other Outputs that use the second SI unit.

WARNING: As a result of how this new output operates, a potentially breaking change has been introduced. If you use any custom Output modules, you will need to add the parameter output_type=None to the output_switch() function of all of your custom Output module files. If you do not, the Mycodo daemon/backend will fail to start after upgrading to or beyond this version. It is advised to modify your custom Output modules prior to upgrading to ensure the daemon successfully starts after the upgrade. If you have not created or imported any custom Output modules, there is nothing that needs to be done.

### Bugfixes

 - Fix measurement being stored in database after sensor error ([#795](https://github.com/kizniche/mycodo/issues/795))
 - Fix UART communication with Atlas Scientific devices ([#785](https://github.com/kizniche/mycodo/issues/785))
 - Fix FTDI communication with Atlas Scientific devices
 - Fix PID Dashboard Widget error in log when PID inactive
 - Fix install on Desktop version of Raspberry Pi OS by removing python3-cffi-backend
 - Fix inability to change I2C address of ADS1x15 Input ([#788](https://github.com/kizniche/mycodo/issues/788))
 - Fix issues with calibrating Atlas Scientific devices ([#789](https://github.com/kizniche/mycodo/issues/789))
 - Fix missing default input custom option values if not set in the database
 - Add missing TSL2561 I2C addresses
 - Fix daemon hang on use of incorrect Atlas Scientific UART device (add writeTimeout to every serial.Serial())
 - Fix uninstall of pigpiod
 - Fix missing pigpio dependency for GPIO PWM Outputs
 - Prevent LCD controllers from activating if Max Age or Decimal Places are unset ([#795](https://github.com/kizniche/mycodo/issues/795))

### Features

 - Add Inputs: ADXL34x, ADT7410 ([#791](https://github.com/kizniche/mycodo/issues/791))
 - Add Output: Generic Peristaltic Pump
 - Add ability to turn peristaltic pumps on for durations (in addition to volumes)
 - Add Function Action: Output (Volume)
 - Improve general compatibility with Atlas Scientific devices
 - Add ability to utilize volume Outputs (pumps) with PID Controllers
 - Add pypi.org links to Input libraries in Input description information
 - Add SPI interface as an option for SD1306 LEDs ([#793](https://github.com/kizniche/mycodo/issues/793))

### Miscellaneous

 - Change Atlas Scientific Peristaltic Pump Output duration unit from minute to second
 - Move clear total volume function for Atlas Scientific Flow Meter to Input Module
 - Add instruction for viewing the frontend web log on the web 502 error page ([#786](https://github.com/kizniche/mycodo/issues/786))


## 8.5.8 (2020-07-07)

### Bugfixes

 - Fix inability to install pigpio ([#783](https://github.com/kizniche/mycodo/issues/783))


## 8.5.7 (2020-07-07)

### Bugfixes

 - Fix inability to install internal dependencies (pigpio, bcm2835, etc.) ([#783](https://github.com/kizniche/mycodo/issues/783))


## 8.5.6 (2020-06-30)

### Bugfixes

- Fix API database schema issue


## 8.5.5 (2020-06-30)

### Bugfixes

 - Prevent user with insufficient permissions from rearranging dashboard widgets
 - Fix installing internal dependencies
 - Fix restore of influxdb measurement data from import/Export page
 - Fix Gauge Widget Measurement options from being selected after saving

### Features

 - Create scripts to automatically generate Input section of manual

### Miscellaneous

 - Add URLs to Input information
 - Switch from deprecated SSLify to Talisman
 - Update Python dependencies


## 8.5.4 (2020-06-06)

### Bugfixes

 - Fix Atlas Scientific pump on duration calculation


## 8.5.3 (2020-06-06)

### Bugfixes

 - Fix upgrade not preserving custom outputs
 - Fix missing output device measurements in database ([#779](https://github.com/kizniche/mycodo/issues/779))


## 8.5.2 (2020-06-01)

### Bugfixes

 - Fix Atlas Scientific Pump Output timestamp parsing


## 8.5.1 (2020-05-30)

### Bugfixes

 - Fix translations
 - Fix dependency check during upgrade
 - Fix Atlas Scientific Pump Output


## 8.5.0 (2020-05-30)

With this release comes the ability to write and import custom Outputs. If you want to utilize an output that Mycodo doesn't currently support, you can now create your own Output module and import it to be used within the system. See [Custom Outputs](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#custom-outputs) in the manual for more information.

WARNING: There are changes with this version that may cause issues with your currently-configured outputs. Therefore, after upgrading, test if your outputs work and update their configuration if needed.

### Bugfixes

 - Fix PID Widget preventing graph custom colors from being editable
 - Fix graph Widget custom color issues ([#760](https://github.com/kizniche/mycodo/issues/760))
 - Fix PWM Trigger Functions reacting to 0 % duty cycle being set ([#761](https://github.com/kizniche/mycodo/issues/761))
 - Fix KeyError if missing options when saving Input
 - Fix ZH03B Input: add repeat measurement option and discard erroneous measurements
 - Fix update check IndexError if there's no internet connection
 - Fix parsing API api_key from requests
 - Fix the inability of Math Controllers to use converted measurements
 - Fix Redundancy Math controller ([#768](https://github.com/kizniche/mycodo/issues/768))
 - Fix display of Custom Controller options
 - Fix hostname display on login page
 - Fix missing blank line check for LCDs with 8 lines ([#771](https://github.com/kizniche/mycodo/issues/771))
 - Fix unset user groups when executing shell commands
 - Fix guest users being able to create dashboards
 - Fix queries with updated influxdb Python library

### Features

 - Add ability to write and import your own Custom Output Modules
 - Add Input: VL53L0X (Laser-Range Measurement) ([#769](https://github.com/kizniche/mycodo/issues/769))
 - Add Input: AS7262 Spectral Sensor (measures 450, 500, 550, 570, 600, and 650 nm wavelengths)
 - Add Input: Atlas Scientific EZO Pressure Sensor
 - Add ability to create custom Input actions
 - Add MH-Z19/MH-Z19B Input actions: zero and span point calibrations
 - Add unit conversions: PSI to kPa, PSI to cm H2O, kPa to PSI
 - Add literature links to Input options: Manufacturer, Datasheet, Product
 - Add 'tail dmesg' to System Information page
 - Add Function Actions: System Restart and System Shutdown ([#763](https://github.com/kizniche/mycodo/issues/763))
 - Add Conditional options: Log Level Debug and Message Includes Code
 - Add Force Command option for Command/Python/Wireless Outputs ([#728](https://github.com/kizniche/mycodo/issues/728))
 - Add ability to select which user executes Linux Output commands ([#719](https://github.com/kizniche/mycodo/issues/719))
 - Add Cameras: URL (urllib), URL (requests) ([Feature Request - IP Camera/Network Camera](https://kylegabriel.com/forum/general-discussion/feature-request-ip-camera-network-camera-stream))
 - Add ability to encode videos from time-lapse image sets
 - Add send_email() to Daemon Control object

### Miscellaneous

 - Upon controller activation, generate Input and Conditional code files if they don't exist
 - Update Werkzeug to 1.0.1 ([#742](https://github.com/kizniche/mycodo/issues/742)), Flask-RESTX to 0.2.0, alembic to 1.4.2, pyro5 to 5.8, SQLAlchemy to 1.3.15, distro to 1.5.0,
 - Refactor Python Output code 
 - Update all translations (all complete)
 - Rename MH-Z19 Input to MH-Z19B (and add MH-Z19 Input)
 - Change Email Notification options to allow unauthenticated sending
 - Add conversions: m <-> cm <-> mm
 - Make PID Controller a class
 - Restyle Output page ([#732](https://github.com/kizniche/mycodo/issues/732))
 - Include error response in PWM/On-Off Command Output debug logging line
 - Update InfluxDB to 1.8.0


## 8.4.0 (2020-03-23)

### Bugfixes

 - Fix invalid links to Help pages
 - Prevent unstoppable Conditional Controller by adding self.running bool variable
 - Fix calculation error causing inaccuracy with ADS1x15 analog-to-digital converter Input
 - Remove PWM and Pump Outputs from Energy Usage calculations
 - Fix links to camera widget error images
 - Fix reference to input library to properly display 1-Wire device IDs ([#752](https://github.com/kizniche/mycodo/issues/752))
 - If a camera output is already on when capturing an image, dont' turn it off after capture
 - Discard first measurement of Atlas Scientific Inputs to prevent some erroneous measurements
 - Fix display of setpoint on PID widget if a band is in use ([#744](https://github.com/kizniche/mycodo/issues/744))
 - Fix Amp calculation ([#758](https://github.com/kizniche/mycodo/issues/758))

### Features

 - Add temperature compensation option for the Atlas Scientific Electrical Conductivity and Dissolved Oxygen Inputs
 - Add Inputs: Atlas Scientific Flow Sensor, Atlas Scientific RGB Color Sensor
 - Add Function Action: Clear Total Volume of Flow Meter, Force Input Measurements
 - Add option to repeat measurements and store average for ADS1x15 analog-to-digital converter Input
 - Add PID option Always Min for PWM outputs to always use at least the min duty cycle ([#757](https://github.com/kizniche/mycodo/issues/757))
 - Add email password reset

### Miscellaneous

 - Add prefix to device IDs when using w1thermsensor ([#752](https://github.com/kizniche/mycodo/issues/752))


## 8.3.0 (2020-02-21)

### Bugfixes

 - Fix determining frontend/backend virtualenv status
 - Fix error detecting GPIO state during energy usage report generation ([#745](https://github.com/kizniche/mycodo/issues/745))
 - Fix Atlas Scientific pH Input temperature calibration measurement
 - Fix Atlas Scientific EZO-PMP flow mode not taking effect immediately upon saving
 - Change deprecated w1thermsensor set_precision() to set_resolution()
 - Fix setting DS sensor resolution ([#747](https://github.com/kizniche/mycodo/issues/747))
 - Split DS18B20 Input into two files (one using w1thermsensor and another using ow-shell) ([#746](https://github.com/kizniche/mycodo/issues/746))
 - Prevent users without "view settings" permission from viewing email addresses
 - Fix TSL2561 input ([#750](https://github.com/kizniche/mycodo/issues/750))

### Features

 - Add Temperature Offset option for BME680 Input ([#735](https://github.com/kizniche/mycodo/issues/735))
 - Add ability to change number of stops for Gauge Widgets ([#749](https://github.com/kizniche/mycodo/issues/749))

### Miscellaneous

 - Fix logging level of calibration functions
 - Populate setpoint in field of PID dashboard widget ([#748](https://github.com/kizniche/mycodo/issues/748))


## 8.2.5 (2020-02-09)

### Bugfixes

 - Fix daemon not being able to read measurements ([#743](https://github.com/kizniche/mycodo/issues/743))


## 8.2.4 (2020-02-08)

### Bugfixes

 - Fix logs appearing blank after logrotate runs ([#734](https://github.com/kizniche/mycodo/issues/734))
 - Update Flask-Babel to 1.0.0 to fix broken werkzeug ([#742](https://github.com/kizniche/mycodo/issues/742))
 - Increase install wait times to prevent timeouts ([#742](https://github.com/kizniche/mycodo/issues/742))

### Features

 - Add BME680 temperature/humidity/pressure/VOC sensor ([#735](https://github.com/kizniche/mycodo/issues/735))
 - Add measurement: resistance
 - Add unit: Ohm
 - Merge from [Flask-RESTPlus](https://github.com/noirbizarre/flask-restplus/issues/770) to [Flask-RESTX](https://github.com/python-restx/flask-restx) ([#742](https://github.com/kizniche/mycodo/issues/742))

### Miscellaneous

 - Improve sanity-checking of Input custom_options
 - Improve sanity-checking of API endpoints ([#741](https://github.com/kizniche/mycodo/issues/741))
 - Update pip requirements


## 8.2.3 (2020-01-27)

### Bugfixes

 - Fix error during upgrade check if there is no internet connection
 - Fix MQTT input, prevent keepalive from being <= 0 ([#733](https://github.com/kizniche/mycodo/issues/733))
 - Fix issue restarting frontend using diagnostic database delete feature
 - Fix ability to import Inputs with measurements/units that don't exist in database ([#735](https://github.com/kizniche/mycodo/issues/735))
 - Fix ability to modify measurement/unit names that Inputs rely on
 - Fix inability to modify custom measurements
 - Fix error when deleting dashboards from the Config->Diagnostics menu ([#737](https://github.com/kizniche/mycodo/issues/737))
 - Fix dashboard gauges causing the dashboard to crash ([#736](https://github.com/kizniche/mycodo/issues/736))

### Miscellaneous

 - Refactor upgrade check code into class to reduce the number of hits to github.com
 - Rearrange dashboard dropdown menu
 - Allow creation of measurement/unit IDs with upper-case letters ([#735](https://github.com/kizniche/mycodo/issues/735))

## 8.2.2 (2020-01-06)

### Bugfixes

 - Fix table colors ([#724](https://github.com/kizniche/mycodo/issues/724))
 - Fix error when dashboard is set to default landing page ([#727](https://github.com/kizniche/mycodo/issues/727))

### Features

 - Add options to show/hide various widget info ([#717](https://github.com/kizniche/mycodo/issues/717))
 - Add Input: MLX90614 ([#723](https://github.com/kizniche/mycodo/pull/723))

### Miscellaneous

 - Update Bootstrap to 4.4.1
 - Update Bootstrap themes


## 8.2.1 (2019.12.08)

This update brings the ability to create multiple dashboards. The dashboard grid spacing has also changed, so you will need to resize your widgets.

This update also brings the ability to run Mycodo/Influxdb in Docker containers, enabling Mycodo to run outside the Raspberry Pi and Raspbian environment. For instance, I currently have Mycodo running on my 64-bit PC in Ubuntu 18.04. This is an experimental feature and is not yet recommended to be used in a production environment. See the [Docker README](https://github.com/kizniche/Mycodo/blob/master/docker/README.md) for more information.

### Features

 - Add ability to run Mycodo in Docker containers ([#637](https://github.com/kizniche/mycodo/issues/637))
 - Add ability to create multiple dashboards ([#717](https://github.com/kizniche/mycodo/issues/717))
 - Add Dashboard Widget: Spacer ([#717](https://github.com/kizniche/mycodo/issues/717))
 - Add ability to hide Widget drag handle, set Widget name font size, and hide Graph Widget buttons ([#717](https://github.com/kizniche/mycodo/issues/717))
 - Add ability to set Dashboard grid cell height

### Miscellaneous

 - Change grid width from 12 to 20 columns
 - Update InfluxDB from 1.7.8 to 1.7.9


## 8.1.1 (2019.11.26)

### Bugfixes

 - Fix outputs not turning on


## 8.1.0 (2019.11.26)

This update brings a new Dashboard organization method, allowing drag-and drop placement and resizing of widgets using gridstack.js. This new system is not comparable to the old; and after upgrading, all widgets will lose their size and position and will need to be repositioned on your dashboard.

### Bugfixes

 - Fix Atlas Scientific UART interfaces
 - Fix display of units in conversion list on Measurement Settings page
 - Fix unit conversions for Math controllers ([#716](https://github.com/kizniche/mycodo/issues/716))
 - Fix Wet-Bulb Humidity calculation in Math controller ([#716](https://github.com/kizniche/mycodo/issues/716))
 - Fix disabled measurements not appearing for math controllers ([#716](https://github.com/kizniche/mycodo/issues/716))
 - Fix disabled measurements from Math controllers still being recorded in influxdb
 - Fix inability to select PID Controller with PID Control Widget ([#718](https://github.com/kizniche/mycodo/issues/718))
 - Fix displaying image in Camera Widgets
 - Fix display of measurement unit on Gauge Widgets

### Features

 - Implement new method for arranging and sizing Dashboard Widgets ([#717](https://github.com/kizniche/mycodo/issues/717))
 - Add API endpoints: /measurements/historical and /measurements/historical_function
 - Add ability to set timestamp with /measurements/create API endpoint
 - Display the entire log for the ongoing upgrade rather than only the last 40 lines
 - Add Calibration: Atlas Scientific Electrical Conductivity Sensor ([#710](https://github.com/kizniche/mycodo/issues/710))
 - Add Input: Mycodo Version (mainly for testing)
 - Allow timestamp to be specified for Python 3 Code Input measurement creation ([#716](https://github.com/kizniche/mycodo/issues/716))

### Miscellaneous

 - Update Bootstrap to 4.3.1
 - Update FontAwesome to 5.11.2


## 8.0.3 (2019.11.15)

### Bugfixes

 - Fix timeout errors during settings/influxdb database import
 - Fix python3 version check during install ([#714](https://github.com/kizniche/mycodo/issues/714))
 - Fix upgrade checking
 

## 8.0.2 (2019.11.13)

### Bugfixes

 - Fix doubling the amount used to calculate Amp draw during an output being turned on


## 8.0.1 (2019.11.11)

### Bugfixes

 - Add Python version check to Mycodo installer ([#712](https://github.com/kizniche/mycodo/issues/712))
 - Daemon now checks for any newer version during upgrade check

### Features

 - Allow any database version <= the currently-installed Mycodo version to be imported


## 8.0.0 (2019.11.09)

Warning: This version will not work with Python 3.5 (Raspbian Stretch). Only upgrade if you have Python 3.7 installed (Raspbian Buster).

This version introduces an improved upgrade system and a REST API (requiring Python >= 3.6) for communicating with Mycodo ([API Info](https://github.com/kizniche/Mycodo/blob/master/mycodo-api.rst) and [API Manual](https://kizniche.github.io/Mycodo/mycodo-api.html)).

### Features

 - Add REST API ([#705](https://github.com/kizniche/mycodo/issues/705))


## 7.10.0 (2019.11.09)

### Bugfixes

 - Fix Output control toaster always displaying error
 - Fix translations not working ([#708](https://github.com/kizniche/mycodo/issues/708))
 - Fix display of units on LCDs
 - Fix inability of Graph Range Selector option to stay checked

### Features

 - Add button to copy device UUID to clipboard
 - Add ability to set IP, port, and timeout for upgrade internet check
 - Add new Camera library: opencv
 - Add ability for variables to persist in Conditional statements
 - Add ability to import any database <= the current Mycodo version (database upgrade will be performed)
 - Add ability to install all unmet dependencies when importing a database
 - Improve upgrade system


## 7.9.1 (2019.10.26)

### Bugfixes

 - Fix issue querying data for Asynchronous graphs

### Features

 - Add ability to select duty cycle step size for PWM Ramp Function Action ([#704](https://github.com/kizniche/mycodo/issues/704))


## 7.9.0 (2019.10.24)

This update improves the backup/restore mechanism for the Mycodo InfluxDB time-series database. InfluxDB backups made prior to v7.8.5 will need to be restored manually. All new backups made will be in the Enterprise-compatible backup format, and only this format will be able to be restored moving forward. See [Backing up and restoring in InfluxDB](https://docs.influxdata.com/influxdb/v1.7/administration/backup_and_restore/) for more information.

This update also moves the Camera options from the Settings to the Camera page, to be more in-line with the formatting of other pages.

### Bugfixes

 - Fix Asynchronous Graphs not displaying data
 - Fix Conditional Measurement (Multiple) Condition error
 - Fix inability to set Raspberry Pi (raspi-config) settings from the Configuration menu

### Features

 - Update InfluxDB database export/import to use new Enterprise-compatible backup format
 - Add general camera options: stream height/width, hide last still, and hide last timelapse ([#703](https://github.com/kizniche/mycodo/issues/703))
 - Add picamera options: white balance, shutter speed, sharpness, iso, exposure mode, meter mode, and image effect ([#313](https://github.com/kizniche/mycodo/issues/313), [#703](https://github.com/kizniche/mycodo/issues/703))
 - Add Function Action: Ramp PWM ([#704](https://github.com/kizniche/mycodo/issues/704))
 - Add Conditional Conditions: Measurement (Single, Past, Average), Measurement (Single, Past, Sum) ([#636](https://github.com/kizniche/mycodo/issues/636))

### Miscellaneous

 - Move camera settings from Settings page to Camera page


## 7.8.4 (2019.10.18)

### Bugfixes

 - Actually fix inability to save PID options ([#701](https://github.com/kizniche/mycodo/issues/701))


## 7.8.3 (2019.10.18)

### Bugfixes

 - Fix inability to save PID options ([#701](https://github.com/kizniche/mycodo/issues/701))


## 7.8.2 (2019.10.17)

### Bugfixes

 - Fix Output Action


## 7.8.1 (2019.10.15)

### Bugfixes

 - Fix copying custom controllers during upgrade


## 7.8.0 (2019.10.14)

This release brings a big feature: Custom Controllers. Now users can import Custom Controllers just like Custom Inputs. There is a new settings section of the Configuration menu called Controllers, where a single-file Custom Controller can be imported into Mycodo. This new controller will appear in the dropdown list on the Functions page, and will act like any other function controller (PID, Trigger, LCD, etc.). See the [Custom Controllers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#custom-controllers) section of the manual.

There's also a new Android app, [Mycodo Support](https://play.google.com/store/apps/details?id=com.mycodo.mycododocs) that provides access to several Mycodo support resources.

### Bugfixes

 - Fix Atlas Scientific EZP Pump not working with PID Controllers ([#562](https://github.com/kizniche/mycodo/issues/562))
 - Fix Output page not showing Duty Cycle for PWM Output status
 - Fix blank Live page if Inputs added but not yet activated
 - Fix inability to capture photos with USB camera ([#677](https://github.com/kizniche/mycodo/issues/677))
 - Fix issues related to influxdb not fully starting before the Mycodo daemon
 - Fix timeout exporting large amounts of data

### Features

 - Add ability to import Custom Controllers (See [Custom Controllers](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#custom-controllers))
 - Add ability to set PWM Output startup and shutdown state ([#699](https://github.com/kizniche/mycodo/issues/699))
 - Add Dashboard Widget: Output PWM Range Slider ([#699](https://github.com/kizniche/mycodo/issues/699))
 - Add ability to use Input/Math measurements with PID setpoint tracking ([#639](https://github.com/kizniche/mycodo/issues/639))
 - Add search to Function select

### Miscellaneous

 - Remove Flask_influxdb
 - Upgrade Influxdb from 1.7.6 to 1.7.8


## 7.7.9 (2019.09.29)

### Bugfixes

 - Fix issue displaying Outputs on Asynchronous Graph

### Features

 - Add Start Offset option for Inputs
 - Add ability to disable Graph series Data Grouping

### Miscellaneous

 - Rename Conditional Statement measure() to condition() in Conditional Controllers
 - Add description for all Conditional Conditions and Actions


## 7.7.8 (2019.09.22)

### Bugfixes

 - Fix LCD controller

### Miscellaneous

 - PEP8
 - Improve error/debug logging


## 7.7.7 (2019.09.20)

### Bugfixes

 - Add reset to SHT31 Input when it errors ([#695](https://github.com/kizniche/mycodo/issues/695))

### Features

 - Add LCD Line: Custom Text
 - Add Input: BME280 using RPi.bme280 library ([#694](https://github.com/kizniche/mycodo/issues/694))
 - Add "Library" to distinguish inputs that use different libraries to acquire measurements for the same sensor


## 7.7.6 (2019.09.19)

### Bugfixes

 - Fix Outputs not showing up on Dashboard and mislabeled measurements ([#692](https://github.com/kizniche/mycodo/issues/692))
 - Update wiringpi to fix issue with Raspberry Pi 4 board ([#689](https://github.com/kizniche/mycodo/issues/689))

### Features

 - Add Conditional Conditions: Output Duration On, Controller Running ([#691](https://github.com/kizniche/mycodo/issues/691))
 - Remove the need for Pyro5 Nameserver ([#692](https://github.com/kizniche/mycodo/issues/692))
 - Add Flask profiler


## 7.7.5 (2019.09.18)

### Bugfixes

 - Fix inability to activate Conditional Controllers ([#690](https://github.com/kizniche/mycodo/issues/690))

### Miscellaneous

 - Improve post-alembic upgrade system
 - Improve Pyro5 logging


## 7.7.4 (2019.09.18)

### Bugfixes

 - Fix issue with Pyro5 proxy handling ([#688](https://github.com/kizniche/mycodo/issues/688))
 - Fix missing Stdout from several log files


## 7.7.3 (2019.09.17)

### Bugfixes

 - Fix wait time for Atlas Scientific pH Calibration ([#686](https://github.com/kizniche/mycodo/issues/686))
 - Add 'minute' measurement storage to EZO Pump Output
 - Fix database upgrade issues

### Features

 - Add ability to store multiple measurements for Outputs ([#562](https://github.com/kizniche/mycodo/issues/562))
 - Add Calibration: Atlas Scientific EZO Pump ([#562](https://github.com/kizniche/mycodo/issues/562))
 - Add ability to select pump modes for Atlas Scientific EZO Pump ([#562](https://github.com/kizniche/mycodo/issues/562))
 - Add ability to enable Daemon debug mode from Configuration page
 - Add ability to use FTDI to communicate with Atlas Scientific EZO Pump
 - Upgrade from Pyro4 to Pyro5


## 7.7.2 (2019.09.14)

### Bugfixes

 - Remove redundant alembic upgrade that can cause upgrade errors
 - Fix moving Conditional/input code during upgrade
 - Generate Conditional/input code for next upgrade
 - Fix MQTT Input ([#685](https://github.com/kizniche/mycodo/issues/685))
 - Fix Atlas Scientific EZO Pump Input issue ([#562](https://github.com/kizniche/mycodo/issues/562))
 - Fix Atlas Scientific EZP Pump Output (UART) error on Output page
 - Fix Atlas Scientific pH Input issue ([#686](https://github.com/kizniche/mycodo/issues/686))
 - Fix issues with calibration of Atlas Scientific pH sensor ([#686](https://github.com/kizniche/mycodo/issues/686))

### Features

 - Add ability to choose 1, 2, or 3 point pH calibration of Atlas Scientific pH sensor ([#686](https://github.com/kizniche/mycodo/issues/686))


## 7.7.1 (2019.09.08)

### Bugfixes

 - Fix issue with Pyro4
 - Fix issue with Trigger controllers


## 7.7.0 (2019.09.08)

This release changes how user-created Python code is executed. This affects Python Code Inputs and Conditional Functions. All effort was made to reformat user scripts during the upgrade process to adhere to the new formatting guidelines, however there are a few instances where scripts could not be updated properly and will need to be done manually by the user before they will work properly. After upgrading your system, ensure your code conforms to the following guidelines:

1. Conditional Functions
   * Use 4-space indentation (not 2-space, tab, or other)
   * Change measure() to self.measure()
   * Change measure_dict() to self.measure_dict()
   * Change run_action() to self.run_action()
   * Change run_all_actions() to self.run_all_actions()
   * Change message to self.message
2. Python Code Inputs
   * Use 4-space indentation (not 2-space, tab, or other)
   * Change store_measurement() to self.store_measurement()

### Bugfixes

 - Fix sunrise/sunset calculation
 - Fix inability to use "," in Input custom options
 - Fix install dependencies for Ruuvitag Input ([#638](https://github.com/kizniche/mycodo/issues/638))
 - Fix reliability issue with Ruuvitag Input (crashing Mycodo daemon) ([#638](https://github.com/kizniche/mycodo/issues/638))
 - Fix storing of SHT31 Smart Gadget erroneous measurements
 - Prevent Pyro4 TimeoutErrors from stopping PID and Conditional controllers
 - Improve Controller reliability/stability
 - Fix path to pigpiod ([#684](https://github.com/kizniche/mycodo/issues/684))

### Features

 - Add Pylint test for Python 3 Code Input
 - Add execute_at_creation option for Inputs
 - Add Measurement: Radiation Dose Rate
 - Add Units: Microsieverts per hour (µSv/hr), Counts per minute (cpm)
 - Add 'message' option for custom Inputs to display a message with the Input options in the web interface
 - Add more logs to view and consolidate "View Logs" page
 - Add automatic initialization of Input custom_options variables

### Miscellaneous

 - Refactor how user-created Python code is executed (i.e. Python Code Inputs and Conditional Statements)
 - Refactor RPC by replacing RPyC with Pyro4 for improved system stability ([#671](https://github.com/kizniche/mycodo/issues/671), [#679](https://github.com/kizniche/mycodo/issues/679))
 - Increase Nginx file upload size
 - Reorganize menu layout
 - Modify linux_command exception-handling ([#682](https://github.com/kizniche/mycodo/issues/682))


## 7.6.3 (2019-07-14)

### Bugfixes

 - Fix calculating VPD

### Features

 - Add Python 3 Code execution Input


## 7.6.2 (2019-07-11)

### Bugfixes

 - Various fixes for Raspbian Buster ([#668](https://github.com/kizniche/mycodo/issues/668))


## 7.6.1 (2019-07-11)

### Bugfixes

 - Fix TH1X-AM2301 Input ([#670](https://github.com/kizniche/mycodo/issues/670))


## 7.6.0 (2019-07-10)

### Bugfixes

 - Fix inability of Input custom_options value to be 0
 - Fix improper unit conversion for TH1X-AM2301 Input ([#670](https://github.com/kizniche/mycodo/issues/670))
 - Fix Bash Command Input script execution ([#667](https://github.com/kizniche/mycodo/issues/667))

### Features

 - Add MQTT (paho) Input ([#664](https://github.com/kizniche/mycodo/issues/664))
 - Add timeout option for Linux Command Input


## 7.5.10 (2019-06-17)

### Bugfixes

 - Fix TTN Data Input timestamps


## 7.5.9 (2019-06-16)

### Bugfixes

 - Fix rare measurement issue with Ruuvitag
 - Ensure Output Controller has fully started before starting other controllers ([#665](https://github.com/kizniche/mycodo/issues/665))
 - Fix module path of mycodo_client.py when executed from symlink ([#665](https://github.com/kizniche/mycodo/issues/665))


## 7.5.8 (2019-06-13)

### Bugfixes

 - Fix "getrandom() initialization failed" with rng-tools ([#663](https://github.com/kizniche/mycodo/issues/663))
 - Fix issues with TH16/10 with AM2301 and Linux Command Inputs ([#663](https://github.com/kizniche/mycodo/issues/663))

### Features

 - Add Debug Logging as an LCD option
 - Add traceback to error message during adding Input ([#664](https://github.com/kizniche/mycodo/issues/664))


## 7.5.7 (2019-06-11)

### Bugfixes

 - Fix Ruuvitag Input


## 7.5.6 (2019-06-11)

### Bugfixes

 - Fix issues with SHT31 Smart Gadget and Ruuvitag Inputs ([#638](https://github.com/kizniche/mycodo/issues/638))
 - Fix 500 Error generating measurement/unit choices ([#662](https://github.com/kizniche/mycodo/issues/662))
 - Change AM2320 Input code ([#585](https://github.com/kizniche/mycodo/issues/585))
 - Fix issue with Base Input

### Features

 - Increase Live page measurement query duration to fix the display of Input measurements


## 7.5.5 (2019-06-03)

### Bugfixes

 - Add influxdb read/write wait timers to prevent connection errors at startup before influxdb has started

### Features

 - Add --get_measurement parameter to mycodo_client.py
 
### Miscellaneous

 - Replace locket with filelock


## 7.5.4 (2019-05-29)

### Bugfixes

 - Prevent rapid successive measurements from inputs after measurement delay
 - Increase lock timeout for Ruuvitag and SHT31 Smart Gadget ([#638](https://github.com/kizniche/mycodo/issues/638))
 - Fix IO error during locking for Ruuvitag ([#638](https://github.com/kizniche/mycodo/issues/638))
 - Fix pytests

### Features

 - Add RPyC Timeout configuration option
 - Allow multiple PIDs to use the same output ([#661](https://github.com/kizniche/mycodo/issues/661))
 - Add timeout parameter to cmd_output() function
 
### Miscellaneous

 - Refactor Min Off Duration to be centrally controlled by the Output Controller ([#660](https://github.com/kizniche/mycodo/issues/660))


## 7.5.3 (2019-05-17)

### Bugfixes

 - Prevent logging aberrant SHT31 Smart Gadget measurements
 - Handle type casting issues with Ruuvitag Input
 - Add Tags to Custom Colors selection of Graphs ([#656](https://github.com/kizniche/mycodo/issues/656))
 - Fix issues with Single Channel Sum and Average Math controllers
 - Fix inability to change Measurement Conversion back to "Do Not Convert"
 - Avoid build error with bcrypt 3.1.6 by lowering to version 3.1.4 ([#658](https://github.com/kizniche/mycodo/issues/658))
 - Fix issue with conversion calculation in wet-bulb humidity function

### Features

 - Add Function Actions: Raise/Lower PID Setpoint ([#657](https://github.com/kizniche/mycodo/issues/657))

### Miscellaneous

 - Add Unit: Pounds per square inch (psi) ([#657](https://github.com/kizniche/mycodo/issues/657))


## 7.5.2 (2019-05-08)

### Bugfixes

 - Fix issues with logging


## 7.5.1 (2019-05-06)

### Bugfixes

 - Fix bug in Input get_value() ([#654](https://github.com/kizniche/mycodo/issues/654))


## 7.5.0 (2019-05-06)

### Bugfixes

 - Fix storing latest SHT31 Smart Gadget measurements
 - Fix Base Input \_\_repr__ and \_\_str__
 - Fix unaccounted PID error if activation attempted when Measurement not set ([#649](https://github.com/kizniche/mycodo/issues/649))
 - Fix missing GPIO Pin sanity check ([#650](https://github.com/kizniche/mycodo/issues/650))
 - Fix "Unknown math type" filling log ([#651](https://github.com/kizniche/mycodo/issues/651))
 - Fix inability to stop PID autotune ([#651](https://github.com/kizniche/mycodo/issues/651))
 - Fix incomplete display of PID Settings on Mycodo Logs page

### Features

 - Add Conditional Condition: Measurement (Multiple)
 - Add ability of Inputs to store measurements with the same or separate timestamps
 - Add option to show debug lines in Daemon Log (for Input/Math/PID/Trigger/Conditional)
 - Add Log Filters: Daemon INFO, Daemon DEBUG
 - Add Input: TH1x with DS18B20 ([#654](https://github.com/kizniche/mycodo/issues/654))

### Miscellaneous

 - Update InfluxDB to 1.7.6


## 7.4.3 (2019-04-17)

### Bugfixes

 - Fix Sunrise/Sunset calculation
 - Update Infrared Remote section of manual to work with latest kernel
 - Add Bluetooth locking to prevent broken pipes

### Features

 - Add Input: RuuviTag ([#638](https://github.com/kizniche/mycodo/issues/638))
 - Add Inputs: Atlas Scientific ORP, Atlas Scientific DO (FTDI, UART, I2C) ([#643](https://github.com/kizniche/mycodo/issues/643))
 - Add Reset Pin option and editable location for SD1306 OLED display ([#647](https://github.com/kizniche/mycodo/issues/647))


## 7.4.2 (2019-04-02)

### Bugfixes

 - Fix Average (single) and Sum (single) Math controllers with an Output selected


## 7.4.1 (2019-04-02)

### Bugfixes

 - Fix custom input preservation during upgrade


## 7.4.0 (2019-04-01)

### Bugfixes

 - Include Pre Output activation during Acquire Measurements Now instruction
 - Fix Outputs triggering at startup
 - Fix CCS811 Input measurement issue ([#641](https://github.com/kizniche/mycodo/issues/641))
 - Fix Math controller (equation)
 - Fix sending email notification to multiple recipients
 - Prevent RPyC TimeoutError from crashing PID controller

### Features

 - Add Input: [The Things Network: Data Storage Integration](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#the-things-network)
 - Add Math controllers: Sum (past, single channel), Sum (last, multiple channels)
 - Add Outputs to Math controllers: Average, Redundancy, Statistics, Sum
 - Add 'required' option for Input 'custom_options' (indicates if option is required to activate Input)
 - Add 'Output State' ('on', 'off', or duty cycle) Condition for Conditional controllers ([#642](https://github.com/kizniche/mycodo/issues/642))

### Miscellaneous

 - Change channel designations to start at 0


## 7.3.1 (2019-02-26)

### Bugfixes

 - Fix settings menu layout
 - Significantly improve speed of dependency-checking
 - Fix missing names for Function Actions

### Features

 - Add dependency system for Function Actions
 - Add proper dependencies for infrared Send Function Action
 - Improve Infrared Send Action by detecting remotes and codes


## 7.3.0 (2019-02-22)

### Bugfixes

 - Fix issue with check_triggers() in output controller
 - Fix issue preventing export of Notes
 - Fix table issue on Note page

### Features

 - Add Function Trigger: Infrared Remote Input
 - Add Function Action: Infrared Remote Send

### Miscellaneous

 - Remove redundant Output (Duration) Trigger (use Output (On/Off) Trigger)


## 7.2.4 (2019-02-20)

### Bugfixes

 - Fix unset channel causing 500 error ([#631](https://github.com/kizniche/mycodo/issues/631))
 - During first install, initialize after install of influxdb

### Miscellaneous

 - Add wiringpi to install


## 7.2.3 (2019-02-19)

### Bugfixes

 - Fix issue with SHT31 Smart Gadget disconnect error-handling
 - Prevent dashboard camera streaming if using the fswebcam library ([#630](https://github.com/kizniche/mycodo/issues/630))
 - Fix number of line characters for 20x4 LCDs ([#627](https://github.com/kizniche/mycodo/issues/627))
 - Fix PID Dashboard widget issues

### Features

 - Add option to set Output shutdown state (on/off/neither)


## 7.2.2 (2019-02-08)

### Bugfixes

 - Fix inability to change BMP280 I2C address ([#625](https://github.com/kizniche/mycodo/issues/625))
 - Fix issue triggering function actions ([#626](https://github.com/kizniche/mycodo/issues/626))

### Features

 - Add log line of PID settings when activated or saved
 - Add PID Settings button to Mycodo Logs page


## 7.2.1 (2019-02-06)

### Bugfixes

 - Remove bluepy version restriction that conflicts with another requirement for the latest version
 - Fix Energy Usage calculations
 - Fix output controller startup issue
 - Fix notes duplicating on graphs
 - Fix inability of Function Action (Output PWM) to set a duty cycle of 0
 - Fix inability of Function Action (Activate Controller) to activate Conditional
 - Fix pigpio dependency issue ([#617](https://github.com/kizniche/mycodo/issues/617))

### Features

 - Add asynchronous graphs to Energy Usage summaries

### Miscellaneous

 - Improve error-handling of Function Actions


## 7.2.0 (2019-02-04)

### Bugfixes

 - Fix calculating Output Usage
 - Fix error-handling of PWM signal generation ([#617](https://github.com/kizniche/mycodo/issues/617))
 - Fix output dependency issue ([#617](https://github.com/kizniche/mycodo/issues/617))

### Features

 - Add new energy usage/cost analysis based on amperage measurements (See [Energy Usage](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#energy-usage) in the manual)
 - Add password recovery feature (technically just creates new admin user from the command line)


## 7.1.7 (2019-02-02)

### Bugfixes

 - Attempted fix of output dependency issue ([#617](https://github.com/kizniche/mycodo/issues/617))
 - Fix PID Autotune ungraceful exit ([#621](https://github.com/kizniche/mycodo/issues/621))


## 7.1.6 (2019-01-30)

### Bugfixes

 - Attempted fix of output dependency issue ([#617](https://github.com/kizniche/mycodo/issues/617))
 - Fix issue creating Triggers ([#618](https://github.com/kizniche/mycodo/issues/618))

### Features

 - Add LCD: 128x64 OLED ([#589](https://github.com/kizniche/mycodo/issues/589))
 - Improve SHT31 Smart Gadget module

### Miscellaneous

 - Update Translations
 - Add Languages: Dutch, Norwegian, Serbian, Swedish


## 7.1.5 (2019-01-28)

### Bugfixes

 - Fix issue downloading logged data from SHT31 Smart Gadget
 - Fix issue using PID measurements on Measurement Dashboard widget ([#616](https://github.com/kizniche/mycodo/issues/616))
 - Fix issue with Python Command Output variable declaration

### Features

 - Add Dashboard widget: Indicator ([#606](https://github.com/kizniche/mycodo/issues/606))


## 7.1.4 (2019-01-26)

### Bugfixes

 - Fix dependency issue preventing Mycodo installation ([#614](https://github.com/kizniche/mycodo/issues/614))

### Features

 - Add Diagnostic option: Delete Settings Database


## 7.1.3 (2019-01-23)

### Bugfixes

 - Fix missing PID Setpoint measurement
 - Fix missing location option for Free Space Input


## 7.1.2 (2019-01-23)

### Bugfixes

 - Fix Method editing


## 7.1.1 (2019-01-22)

### Bugfixes

 - Fix Conditional Statement testing during form save ([#610](https://github.com/kizniche/mycodo/issues/610))


## 7.1.0 (2019-01-20)

This release changes Conditional behavior. After upgrading to this version, your Conditional Statements should have every Condition '{ID}' changed to 'measure("{ID}")'. Check every Conditional after the upgrade to ensure they work as expected. Additionally, the recommended logic to store and test measurements has changed, so review the Examples in the [Conditionals section of the manual](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#conditional).

### Bugfixes

 - Fix Error message when activating/deactivating controllers (no actual error occurred)
 - Fix (workaround) for inability to display Note whitespaces on Graphs

### Features

 - Add ability to conduct individual measurement in Conditional Statements ([#605](https://github.com/kizniche/mycodo/issues/605))
 - Add ability to execute individual actions in Conditional Statements ([#605](https://github.com/kizniche/mycodo/issues/605))
 - Add ability to modify the Conditional message ([#605](https://github.com/kizniche/mycodo/issues/605))
 - Add Function Actions: Email with Photo Attachment, Email with Video Attachment


## 7.0.5 (2019-01-10)

### Bugfixes

 - Fix missing Atlas pH Input baud rate option ([#597](https://github.com/kizniche/mycodo/issues/597))
 - Fix properly displaying I2C/UART Input options
 - Fix issue requiring action selection to submit form ([#595](https://github.com/kizniche/mycodo/issues/595))
 - Fix output duration not being logged if settings saved while output is currently on
 - Fix instability of dependency system
 - Fix missing libglib2.0-dev dependency of SHT31 Smart Gadget

### Features

 - Add FTDI support for Atlas Scientific sensors ([#597](https://github.com/kizniche/mycodo/issues/597))
 - Add Output option to trigger Functions at startup

### Miscellaneous

 - Update SHT31 Smart Gadget Input module


## 7.0.4 (2019-01-07)

### Bugfixes

 - Fix issue with converted measurements unable to be used with Conditionals ([#592](https://github.com/kizniche/mycodo/issues/592))
 - Add pi-bluetooth to SHT31 Smart Gadget dependencies ([#588](https://github.com/kizniche/mycodo/issues/588))
 - Fix issue using PIDs and Graphs with converted measurement units ([#594](https://github.com/kizniche/mycodo/issues/594))
 - Fix issue with mixed up order of Graph series
 - Fix issue recording output durations

### Features

 - Add OWFS support for 1-wire devices (currently only DS18B20, DS18S20 supported) ([#582](https://github.com/kizniche/mycodo/issues/582))
 - Add ability to delete .dependency and .upgrade files from the web UI ([#590](https://github.com/kizniche/mycodo/issues/590))

### Miscellaneous

 - Update several Python modules, update InfluxDB to 1.7.2
 - Update manual FAQs


## 7.0.3 (2018-12-25)

### Bugfixes

 - Fix rendering new lines in Note text on graphs
 - Fix display of proper unit on Measurement Dashboard element ([#583](https://github.com/kizniche/mycodo/issues/583))
 - Fix missing libjpeg-dev dependency for PiOLED ([#584](https://github.com/kizniche/mycodo/issues/584))
 - Fix dependencies for AMG88xx Input

### Features

 - Add Function Action: Create Note
 - Add Input: Sonoff TH10/16 humidity and temperature sensor ([#583](https://github.com/kizniche/mycodo/issues/583))
 - Add Input: AM2320 I2C humidity and temperature sensor ([#585](https://github.com/kizniche/mycodo/issues/585))

### Miscellaneous

 - Change method for detecting 1-wire devices ([#582](https://github.com/kizniche/mycodo/issues/582))
 - Disable variable replacement in Command Execution Function Action until it can be fixed to work with new measurement system


## 7.0.2 (2018-12-21)

### Bugfixes

 - Fix inability to reorder Dashboard, Data, Output, and Function elements
 - Fix Edge Inputs not appearing in Edge Trigger input selection
 - Fix use of Atlas pH temperature calibration from Input/Math

### Features

 - Add Additional check for Conditional Statements if {ID} is replaced with None ([#571](https://github.com/kizniche/mycodo/issues/571))
 - Add ability to set Logging Interval and download logged data from SHT31 Smart Gadget ([#559](https://github.com/kizniche/mycodo/issues/559))
 - Add Math: Input Backup: If a measurement of an Input cannot be found, look for a measurement of another (or another, etc.) ([#559](https://github.com/kizniche/mycodo/issues/559))

### Miscellaneous

 - Add check so SHT31 Smart Gadget user options don't cause the number of stored measurements to exceed the internal memory


## 7.0.1 (2018-12-09)

### Bugfixes

 - Fix PiOLED LCD from changing I2C address when options are saved ([#579](https://github.com/kizniche/mycodo/issues/579))
 - Fix Generic 16x2/16x4 LCD display issue ([#578](https://github.com/kizniche/mycodo/issues/578))
 - Fix Math Add dropdown items having the same name ([#580](https://github.com/kizniche/mycodo/issues/580))

### Features

 - Add ability to induce an Input to acquire/store measurements from the web UI
 - Add Input: SHT31 Smart Gadget (Bluetooth) humidity/temperature sensor ([#559](https://github.com/kizniche/mycodo/issues/559))
 - Add blank line to LCD display options ([#579](https://github.com/kizniche/mycodo/issues/579))

 ### Miscellaneous

 - Add verification for Conditional Statement code


## 7.0.0 (2018-12-08)

The Mycodo 7.0 introduces many redesigned systems, including measurements/units, conversions, conditionals, and more (see full list, below). The remnants of Conditionals have been moved to a new controller, called Triggers, which executes actions in response to event triggers (such as time-based events, Output changes, sunrises/sunsets, etc.). The new Conditional system incorporates a powerful way of developing complex conditional statements. See ([#493](https://github.com/kizniche/mycodo/issues/493)) for more information. Since earlier versions are not compatible with 7.x, all 6.x users will have to perform a fresh install or delete their settings database. An option will be presented on the upgrade page to delete the database and perform an upgrade.

### Bugfixes

 - Fix issue preventing PID Method from changing setpoint (#566)
 - Fix issue with calibration of DS-type sensors
 - Fix module loading issue by restarting the daemon following dependency install ([#569](https://github.com/kizniche/mycodo/issues/569))
 - Fix issue adding Daily Time-Based method ([#550](https://github.com/kizniche/mycodo/issues/550))

### Features

 - Add Function: Execute Actions
 - Add Function Action: Pause (pause for a duration of time between executing specific actions)
 - Add Input: MCP9808 (I2C) high accuracy temperature sensor
 - Add Input: AMG8833 (I2C) 8x8 pixel thermal sensor
 - Add Input: SHT31 (I2C) humidity/temperature sensor
 - Add LCD: PiOLED 128x32 (I2C) LCD ([#579](https://github.com/kizniche/mycodo/issues/579))
 - Add Output: Python Command (On/Off and PWM)
 - Add Output: Atlas EZO-PMP (I2C/UART) Peristaltic Pump ([#562](https://github.com/kizniche/mycodo/issues/562))
 - Add Vapor Pressure Deficit calculation to Inputs that measure temperature and relative humidity ([#572](https://github.com/kizniche/mycodo/issues/572))
 - Add Vapor Pressure Deficit Math controller ([#572](https://github.com/kizniche/mycodo/issues/572))
 - Add Start Offset option for PID, Math, and Conditionals
 - Add ability to search Input selection dropdown list

### Miscellaneous

 - Refactor Conditional system ([#493](https://github.com/kizniche/mycodo/issues/493))
 - Refactor Analog-to-digital converters ([#550](https://github.com/kizniche/mycodo/issues/550))
 - Refactor Measurement/Unit system ([#550](https://github.com/kizniche/mycodo/issues/550))
 - Refactor Conversion system ([#493](https://github.com/kizniche/mycodo/issues/493))
 - Upgrade InfluxDB from 1.6.0 to 1.7.0
 - Add User Role: Kiosk


## 6.4.7 (2018-12-08)

This is the final release of version 6.x. Upgrading to 7.x will require a database wipe. This will be an option presented in the Mycodo upgrade page. If you do not want to lose your Mycodo data (settings AND measurement data), do not upgrade to 7.x.


## 6.4.5 (2018-10-17)

### Bugfixes

 - Fix issues with ADS1256 module ([#537](https://github.com/kizniche/mycodo/issues/537))
 - Fix issue with saving float values

### Miscellaneous

 - Replace smbus with smbus2 ([#549](https://github.com/kizniche/mycodo/issues/549))


## 6.4.4 (2018-10-14)

### Features

 - Add enhanced reorder functionality for Input, Output, Math, PID, and Conditional controllers
 - Add ability to set camera still, timelapse, and video file save locations ([#498](https://github.com/kizniche/mycodo/issues/498))
 - Add ability to export/import notes and note attachments ([#548](https://github.com/kizniche/mycodo/issues/548))

### Bugfixes

 - Fix authentication issue with Remote Administration
 - Fix issues with ADS1256 module ([#537](https://github.com/kizniche/mycodo/issues/537))
 - Fix issue with saving float values

### Miscellaneous

 - Replace smbus with smbus2 ([#549](https://github.com/kizniche/mycodo/issues/549))


## 6.4.3 (2018-10-13)

### Bugfixes

 - Fix authentication issue introduced in 6.4.2


## 6.4.2 (2018-10-13)

### Features

 - Add MH-Z19 option: enable/disable automatic baseline correction (ABC)
 - Add ability to Test/trigger all Conditional Actions of a Conditional ([#524](https://github.com/kizniche/mycodo/issues/524))

### Bugfixes

 - Fix Cozir module pycozir egg
 - Fix often-erroneous first measurement of ZH03B and MH-Z19 sensors
 - Fix issue with ADS1256 module ([#537](https://github.com/kizniche/mycodo/issues/537))


## 6.4.1 (2018-10-11)

### Bugfixes

 - Fix database upgrade issue


## 6.4.0 (2018-10-11)

### Features

 - Add Input: ADS1256 Analog-to-digital converter ([#537](https://github.com/kizniche/mycodo/issues/537))
 - Add ability to create custom options for Input modules ([#525](https://github.com/kizniche/mycodo/issues/525))
 - Add conversions between ppm/ppb and percent

### Bugfixes

 - Fix issue determining PID setpoint unit on LCDs
 - Fix issue displaying IP address on LCD
 - Fix issue with client activating controllers ([#532](https://github.com/kizniche/mycodo/issues/532))
 - Fix issue with Linux Command Input ([#537](https://github.com/kizniche/mycodo/issues/537))
 - Fix issue with installing internal dependencies (e.g. pigpiod) ([#538](https://github.com/kizniche/mycodo/issues/538))
 - Potential fix for Miflora input ([#540](https://github.com/kizniche/mycodo/issues/540))
 - Fix missing Baud Rate option for K30 input ([#541](https://github.com/kizniche/mycodo/issues/541))
 - Fix 500 Error on Raspberry Pi Config page ([#536](https://github.com/kizniche/mycodo/issues/536))
 - Add turning ABC mode off during MHZ19 input initialization ([#546](https://github.com/kizniche/mycodo/issues/546))
 - Fix German "Output" translation

### Miscellaneous

 - Set InfluxDB timeout to 5 seconds ([#539](https://github.com/kizniche/mycodo/issues/539))
 - Update Winsen ZH03B input module code ([#543](https://github.com/kizniche/mycodo/issues/543))


## 6.3.9 (2018-09-18)

### Bugfixes

 - Fix issue with installing dependencies ([#531](https://github.com/kizniche/mycodo/issues/531))
 - Fix issue with Edge devices


## 6.3.8 (2018-09-17)

### Bugfixes

 - Fix issue with database upgrade


## 6.3.7 (2018-09-17)

### Bugfixes

 - Fix issue with database upgrade


## 6.3.6 (2018-09-17)

### Bugfixes

 - Fix issue with Edge devices


## 6.3.5 (2018-09-17)

### Bugfixes

 - Fix issue with 1-Wire devices ([#529](https://github.com/kizniche/mycodo/issues/529))


## 6.3.4 (2018-09-17)

### Bugfixes

 - Fix issue with note system during upgrade ([#529](https://github.com/kizniche/mycodo/issues/529))


## 6.3.3 (2018-09-17)

### Bugfixes

 - Fix Cozir input issue


## 6.3.2 (2018-09-16)

### Bugfixes

 - Fix ZH03B input


## 6.3.1 (2018-09-16)

This release adds the ability to import input modules, allowing new inputs to be created by the user. Documentation (https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#create-your-own-input-module) for developing your own input modules is in development. See issue #525 for more information about it's development and discussion. Also with this release is a new section for Notes (More -> Notes, https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.rst#notes). Notes are associated with one more more tags that can be created. Notes can also have files attached to them. These notes can be displayed on graphs to easily identify when a certain event happened in the past (or future).

### Features

 - Implement self-contained input modules ([#525](https://github.com/kizniche/mycodo/issues/525))
 - Add Note system ([#527](https://github.com/kizniche/mycodo/issues/527))


## 6.2.4 (2018-09-03)

### Features

 - Add Winsen ZH03B Particulate sensor ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Reduce install to one command

### Bugfixes

 - Fix inability to set camera device ([#519](https://github.com/kizniche/mycodo/issues/519))
 - Fix initialization of UART MHZ16 ([#520](https://github.com/kizniche/mycodo/issues/520))
 - Fix issue with BMP280 ([#522](https://github.com/kizniche/mycodo/issues/522))

## 6.2.3 (2018-08-28)

### Bugfixes

 - Fix issue with major version upgrade initialization
 - Fix issue with PWM output dashboard element updating ([#517](https://github.com/kizniche/mycodo/issues/517))
 - Fix dependency check for DS-type sensor calibration ([#518](https://github.com/kizniche/mycodo/issues/518))
 - Fix issue with Adafruit deprecating BMP, TMP, and CCS811 ([#346](https://github.com/kizniche/mycodo/issues/346), [#503](https://github.com/kizniche/mycodo/issues/503))


## 6.2.2 (2018-08-22)

### Features

 - Add translations: Italian, Portuguese

### Bugfixes

 - Fix display of IP address on LCD ([#507](https://github.com/kizniche/mycodo/issues/507))
 - Fix graph manual y-axis min/max ([#516](https://github.com/kizniche/mycodo/issues/516))
 - Fix issue with deleting all dashboard elements


## 6.2.1 (2018-08-20)

### Features

 - Add Diagnostic section of configuration menu with first function: Delete All Dashboard Elements ([#515](https://github.com/kizniche/mycodo/issues/515), [#516](https://github.com/kizniche/mycodo/issues/516))

### Bugfixes

 - Fix issue with units on LCDs ([#514](https://github.com/kizniche/mycodo/issues/514))


## 6.2.0 (2018-08-15)

### Features

 - New measurement/unit configuration system (select which unit to convert/store for input measurements) ([#506](https://github.com/kizniche/mycodo/issues/506))
 - Add ability to create new measurements, units, and conversions ([#506](https://github.com/kizniche/mycodo/issues/506))
 - Enable conversion of disk space (kB, MB, GB), frequency (Hz, kHz, MHz), and humidity (%, decimal)
 - Add option to display IP address on LCD ([#507](https://github.com/kizniche/mycodo/issues/507))
 - Full German Translation ([#507](https://github.com/kizniche/mycodo/issues/507)) (@pmunz75)
 - Add PID Autotune feature (currently disabled; may be enabled in the release, pending testing)
 - Add New Translations: Russian, Chinese
 - Complete Translations: German, Spanish, French

### Bugfixes

 - Fix issue activating Cozir CO2 sensor ([#495](https://github.com/kizniche/mycodo/issues/495))
 - Fix issue with order not updating correctly when Conditional is deleted
 - Fix issue with output usage report generation ([#504](https://github.com/kizniche/mycodo/issues/504))
 - Fix proper conversion of temperatures/pressure for Wet-Bulb Humidity Math
 - Fix Atlas pH UART sensor module ([#509](https://github.com/kizniche/mycodo/issues/509))

### Miscellaneous

 - Update InfluxDB 1.5.0 -> 1.6.0


## 6.1.4 (2018-06-28)

### Features

 - Increase verbosity of conditional email notification
 - Add Cozir CO2 sensor Input ([#495](https://github.com/kizniche/mycodo/issues/495))
 - Allow CO2 to be converted from ppm <-> ppb

### Bugfixes

 - Fix pressure measurements being forced to integer ([#476](https://github.com/kizniche/mycodo/issues/476))
 - Fix CCS811 Input measurement ([#467](https://github.com/kizniche/mycodo/issues/467))
 - Fix pigpio dependency install issue
 - Prevent pre-output from remaining on after an Input is deactivated
 - Enable unit conversions for AM2315
 - Fix issue setting PID setpoint from Dashboard ([#496](https://github.com/kizniche/mycodo/issues/496))
 - Fix displaying custom graph colors ([#491](https://github.com/kizniche/mycodo/issues/491))

### Miscellaneous

 - Remove I2C support for K30 CO2 sensor (until properly tested)
 - Update to Bootstrap 4.1.1
 - Remove remaining Fahrenheit conversions from Live page
 - Update 433 MHz wireless script (test send/receive, determine/receive commands from remote)


## 6.1.3 (2018-06-05)

### Features

 - Add I2C support for K30 CO2 sensor (untested)

### Bugfixes

 - Fix service executable location ([#487](https://github.com/kizniche/mycodo/issues/487))
 - Fix inability to set duty cycle from frontend ([#485](https://github.com/kizniche/mycodo/issues/485))
 - Fix (finally) saving Time-based Conditional times ([#488](https://github.com/kizniche/mycodo/issues/488))


## 6.1.2 (2018-05-23)

### Features

 - Add option to set Miflora Bluetooth adapter ([#483](https://github.com/kizniche/mycodo/issues/483))

### Bugfixes

 - Fix exception-handling of sending test email ([#471](https://github.com/kizniche/mycodo/issues/471))
 - Fix HDC1000 initialization issue ([#467](https://github.com/kizniche/mycodo/issues/467))
 - Fix Command PWM frontend issues ([#469](https://github.com/kizniche/mycodo/issues/469))
 - Fix ADC modules ([#482](https://github.com/kizniche/mycodo/issues/482))
 - Update miflora to 0.4 ([#481](https://github.com/kizniche/mycodo/issues/481))
 - Fix BH1750 sensor ([#480](https://github.com/kizniche/mycodo/issues/480))

### Miscellaneous

- Update alembic, Flask, Flask_CSV, geocoder, gunicorn, imutils, pytest, python-dateutil, SQLAlchemy, testfixtures


## 6.1.1 (2018-05-18)

### Features

- Add CCS811 CO2 sensor input ([#467](https://github.com/kizniche/mycodo/issues/467))
- Add HDC1000/HDC1080 Temperature/Humidity sensor input ([#467](https://github.com/kizniche/mycodo/issues/467))
- Add Pascal/kiloPascal conversion for pressure
- Add ppm/ppb conversion for CO2 and VOC concentration
- Improve accuracy of float measurement values
- Add option to set camera output duration (before image capture)
- Improve handling of multiple queries to a single device

### Bugfixes

 - Fix saving settings of Conditional Timers ([#470](https://github.com/kizniche/mycodo/issues/470))
 - Fix Command PWM output use in PIDs ([#469](https://github.com/kizniche/mycodo/issues/469))
 - Fix proper display of Outputs in Conditionals ([#469](https://github.com/kizniche/mycodo/issues/469))


## 6.1.0 (2018-05-02)

### Features

- Add Output (Duration) Conditional ([#186](https://github.com/kizniche/mycodo/issues/186))

### Bugfixes

 - Fix refreshing settings of active conditional controllers
 - Fix saving settings of Conditional Timers ([#464](https://github.com/kizniche/mycodo/issues/464))


## 6.0.9 (2018-04-27)

### Bugfixes

 - Fix command measurement checking ([#460](https://github.com/kizniche/mycodo/issues/460))
 - Fix rendering of Math measurements/units ([#461](https://github.com/kizniche/mycodo/issues/461))


## 6.0.8 (2018-04-27)

### Bugfixes

 - Fix identification of custom command measurement/units ([#457](https://github.com/kizniche/mycodo/issues/457))
 - Fix AM2315 Input issue ([#459](https://github.com/kizniche/mycodo/issues/459))


## 6.0.7 (2018-04-26)

### Features

- Add ability to change sample rate of controllers ([#386](https://github.com/kizniche/mycodo/issues/386))

### Bugfixes

 - Fix display of graph custom y-axis names
 - Fix inability to change pigpiod sample rate ([#458](https://github.com/kizniche/mycodo/issues/458))


## 6.0.6 (2018-04-23)

### Bugfixes

 - Fix issue with Edge Input
 - Fix issue with Conditional timers
 - Fix issue with BME280 dependency identification


## 6.0.5 (2018-04-22)

### Features

- Add Conditional: Time Span ([#444](https://github.com/kizniche/mycodo/issues/444))

### Bugfixes

 - Fix dependency check ([#422](https://github.com/kizniche/mycodo/issues/422))
 - Try lower integration times when TSL2561 sensor is saturated ([#450](https://github.com/kizniche/mycodo/issues/450))
 - Fix DHT11/DHT22 output power check ([#454](https://github.com/kizniche/mycodo/issues/454))


## 6.0.4 (2018-04-21)

### Bugfixes

 - Fix scanning for DS18B20 sensors ([#452](https://github.com/kizniche/mycodo/issues/452))


## 6.0.3 (2018-04-21)

### Bugfixes

 - Fix upgrade issue


## 6.0.1 (2018-04-21)

### Bugfixes

 - Fix setting landing page ([#452](https://github.com/kizniche/mycodo/issues/452))


## 6.0.0 (2018-04-21)

Version 6 has changes to the database schema that could not be upgraded to. To upgrade to this version, the settings database must be created anew. You either have the options of staying at the last version (5.7.x), or deleting the settings database and upgrading. A fresh install is necessary to run this version.

### Features

 - Add Conditionals: Run PWM Method, Daily Time Point Timer, Duration Timer, Output PWM ([#444](https://github.com/kizniche/mycodo/issues/444), [#448](https://github.com/kizniche/mycodo/issues/448))
 - Add Conditional Actions: Activate/Deactivate any controller, Set PID Method ([#440](https://github.com/kizniche/mycodo/issues/440))
 - Use actual range value for color stops of solid gauges ([#434](https://github.com/kizniche/mycodo/issues/434))
 - Add option to set setpoint from PID dashboard element without epanding element ([#449](https://github.com/kizniche/mycodo/issues/449))
 - Refactor Conditional Controllers to be multithreaded

### Bugfixes

 - Fix Hold bug in PID controllers
 - Fix error-handing when changing PID setting from Dashboard if PID is inactive ([#449](https://github.com/kizniche/mycodo/issues/449))

### Miscellaneous

 - Remove multiplexer integration (use kernel driver)
 - Remove Timers (Conditionals have replaced their functionality)
 - Improve testing coverage of frontend ([#444](https://github.com/kizniche/mycodo/issues/444))


## 5.7.3 (2018-04-20)

This is the last version of the 5.x branch. If your system is upgraded to 5.7.3, you will have the option of upgrading to the next major version (6.x), however the settings database will need to be deleted. This can be done through the web UI or manually by reinstalling Mycodo fresh.

### Features

 - Add Conditional Action: Set PID Method ([#440](https://github.com/kizniche/mycodo/issues/440))


## 5.7.2 (2018-04-07)

### Features

 - Add ability to invert PWM duty cycle ([#444](https://github.com/kizniche/mycodo/issues/444))
 - Add ability to select landing page ([#444](https://github.com/kizniche/mycodo/issues/444))
 - Add ability to set setpoint from PID dashboard elements ([#444](https://github.com/kizniche/mycodo/issues/444))
 - Add Conditional Actions: Activate/Deactivate Timer ([#440](https://github.com/kizniche/mycodo/issues/440))

### Bugfixes

 - Fix catching erroneous DS18B20 values ([#404](https://github.com/kizniche/mycodo/issues/404))
 - Fix camera selection of Photo Conditional Action ([#444](https://github.com/kizniche/mycodo/issues/444))

### Miscellaneous

 - Set picamera use_video_port=False ([#444](https://github.com/kizniche/mycodo/issues/444))
 - Rearrange navigation menu ([#444](https://github.com/kizniche/mycodo/issues/444))


## 5.7.1 (2018-04-04)

### Features

 - Add Conditional Action: Set PID Setpoint
 - Add Input: Xiaomi MiFlora ([#422](https://github.com/kizniche/mycodo/issues/422))

### Bugfixes

 - Restore missing help menu on navigation bar
 - Fix issue reading SHT sensors ([#437](https://github.com/kizniche/mycodo/issues/437))

### Miscellaneous

 - Convert README and Manual from MD to RST
 - Update sht_sensor to 18.4.1


## 5.7.0 (2018-04-03)

### Features

 - Add ability to convert Input measurements between units ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add unit conversions: celsius, fahrenheit, kelvin, meters, feet
 - Add ability to select whether lowering PID outputs are stored as positive or negative values
 - Add Sunrise/Sunset Conditional ([#440](https://github.com/kizniche/mycodo/issues/440))
 - Add ability to set the precision for DS18B20, DS1822, DS28EA00, and DS1825 sensors ([#439](https://github.com/kizniche/mycodo/issues/439))
 - Add Inputs: DS18S20, DS1822, DS28EA00, DS1825, MAX31850K
 - Add Input option to select resolution for DS18B20, DS1822, DS28EA00, and DS1825 ([#439](https://github.com/kizniche/mycodo/issues/439))


### Bugfixes

 - Fix issues with PID control on Dashboard ([#441](https://github.com/kizniche/mycodo/issues/441))
 - Improve LCD controller shutdown speed
 - Fix installer not displaying progress in console ([#442](https://github.com/kizniche/mycodo/issues/442))
 - Force measurement values to float before writing to influxdb (except 'pressure') ([#441](https://github.com/kizniche/mycodo/issues/441))


## 5.6.10 (2018-03-31)

### Bugfixes

 - Fix issue executing mycodo_client.py
 - Fix Command Outputs not turning off after turning on for a duration ([#432](https://github.com/kizniche/mycodo/issues/432))
 - Prevent DS18B20 measurements outside expected range ([#404](https://github.com/kizniche/mycodo/issues/404))
 - Prevent race condition preventing output from remaining on for a duration ([#436](https://github.com/kizniche/mycodo/issues/436))
 - Ensure outputs turned on for a duration only turn off once ([#436](https://github.com/kizniche/mycodo/issues/436))
 - Update sht-sensor to 18.3.6 for Python 3 compatibility ([#437](https://github.com/kizniche/mycodo/issues/437))

### Miscellaneous

 - Change SSL certificate expiration from 1 year to 10 years
 - Fix style issues with Remote Admin following Bootstrap upgrade
 - Fix issue with setup.sh script not catching errors


## 5.6.9 (2018-03-24)

### Features

 - Add Refractory Period to Measurement Conditional options
 - Add method to hide/show/reorder all Dashboard Elements at once ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Make Output/PID popups respond to show/hide configuration options ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add Input: Atlas Electrical Conductivity sensor ([#411](https://github.com/kizniche/mycodo/issues/411))

### Bugfixes

 - Fix issue saving reference resistor value ([#345](https://github.com/kizniche/mycodo/issues/345))
 - Fix LCD display of timestamps
 - Fix inability to change Solid Gauge Stops ([#433](https://github.com/kizniche/mycodo/issues/433))
 - Fix Command Outputs not turning off after turning on for a duration ([#432](https://github.com/kizniche/mycodo/issues/432))
 - Fix encoding issue with df command output ([#430](https://github.com/kizniche/mycodo/issues/430))


## 5.6.8 (2018-03-19)

### Bugfixes

 - Fix Camera Output not having an effect
 - Fix issues with MAX31856/MAX31865 ([#345](https://github.com/kizniche/mycodo/issues/345))


## 5.6.7 (2018-03-18)

### Bugfixes

 - Fix upgrade menu not turning red when an upgrade is available
 - Add lockfile breaking ([#418](https://github.com/kizniche/mycodo/issues/418))
 - Fix bcrypt dependency issue preventing install ([#429](https://github.com/kizniche/mycodo/issues/429))


## 5.6.6 (2018-03-17)

### Features

 - Add Input: MAX31865 for PT100 and PT1000 temperature probes ([#345](https://github.com/kizniche/mycodo/issues/345))

### Bugfixes

 - Fix incorrect conversion of I2C address during Atlas pH sensor calibration ([#425](https://github.com/kizniche/mycodo/issues/425))
 - Potential fix for ADC issues when using pre-output ([#418](https://github.com/kizniche/mycodo/issues/418))
 - Fix Linux Command measurement display on lines 2 through 4 of LCDs ([#427](https://github.com/kizniche/mycodo/issues/427))
 - Fix display of PID setpoint units on LCDs
 - Fix display of LCD lines without measurement units
 - Fix locking to be thread safe (replaced fasteners with locket) ([#418](https://github.com/kizniche/mycodo/issues/418))


## 5.6.5 (2018-03-14)

### Features

 - Update to Bootstrap 4
 - Update to InfluxDB 1.5.0

### Bugfixes

 - Add proper max voltage for MCP3008 ([#418](https://github.com/kizniche/mycodo/issues/418))
 - Fix PID persisting as paused/held after deactivating and activating
 - Fix Atlas pH Calibration issue ([#425](https://github.com/kizniche/mycodo/issues/425))
 - Fix issue with Linux Command Inputs and LCDs ([#427](https://github.com/kizniche/mycodo/issues/427))


## 5.6.4 (2018-03-11)

### Features

 - Add Input: MAX31856 for measuring several types of thermocouples (K, J, N, R, S, T, E, and B) ([#345](https://github.com/kizniche/mycodo/issues/345)
 - Add mycodo_client.py option: get or set PID setpoint, integrator, derivator, kp, ki, and kd ([#420](https://github.com/kizniche/mycodo/issues/420))
 - Add option to enable pre-output during measurement (previously turned off before measurement) ([#418](https://github.com/kizniche/mycodo/issues/418))

### Bugfixes

 - Fix frontend pid in System Information page
 - Fix issue with mycodo_client.py PID hold and resume commands

### Miscellaneous

 - Make rpi-rf an optional Output dependency


## 5.6.3 (2018-03-09)

### Features

 - Add ability to use custom command line options for fswebcam camera image captures ([#419](https://github.com/kizniche/mycodo/issues/419))
 - Add Input: MAX31855K for measuring K-type thermocouples ([#345](https://github.com/kizniche/mycodo/issues/345))
 - Add ability to set duty cycle of output via mycodo_client.py ([#420](https://github.com/kizniche/mycodo/issues/420))
 - Add Conditional Action: Output PWM ([#420](https://github.com/kizniche/mycodo/issues/420))
 - Add Output Type: Execute Command (PWM) ([#420](https://github.com/kizniche/mycodo/issues/420))

### Bugfixes

 - Fix LCD issues
 - Fix state display of Command Outputs turned on for a duration


## 5.6.2 (2018-03-04)

### Features

 - Make install of WiringPi optional ([#412](https://github.com/kizniche/mycodo/issues/412))
 - Make install of numpy optional ([#412](https://github.com/kizniche/mycodo/issues/412))
 - Add pause color and Pause/Hold/Resume buttons to PID Dashboard element options ([#416](https://github.com/kizniche/mycodo/issues/416))
 - Display a log when installing dependencies to follow the progress
 - Add Dependency Install Log to the Log page
 - Add mycodo_client.py user commands: pid_pause, pid_hold, pid_resume
 
### Bugfixes

 - Fix issues with PID Conditional Actions ([#416](https://github.com/kizniche/mycodo/issues/416))
 - Fix display of last edge on Live page
 - Fix issue updating the status of some dependencies after their install

### Miscellaneous

 - Remove redundant upgrade commands ([#412](https://github.com/kizniche/mycodo/issues/412))
 - Remove GPIO State from Edge Conditional (use Measurement Conditional) ([#416](https://github.com/kizniche/mycodo/issues/416))


## 5.6.1 (2018-02-27)

### Features

 - Add Conditional Actions: Pause/Resume PID ([#346](https://github.com/kizniche/mycodo/issues/346))

### Bugfixes

 - Fix pigpiod configuration options when pigpiod is not installed ([#412](https://github.com/kizniche/mycodo/issues/412))
 - Fix setting up pigpiod during install
 - Fix TSL2561 Input module ([#414](https://github.com/kizniche/mycodo/issues/414))
 - Fix Measurement Dashboard element condition/unit display ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Fix saving PID Conditional Actions ([#415](https://github.com/kizniche/mycodo/issues/415))


## 5.6.0 (2018-02-25)

### Features

 - Add interactive installer
 - Make Python modules conditionally imported ([#412](https://github.com/kizniche/mycodo/issues/412))


## 5.5.24 (2018-02-24)

### Features

 - Add new Input: MCP3008 Analog-to-Digital Converter ([#409](https://github.com/kizniche/mycodo/issues/409))


## 5.5.23 (2018-02-23)

### Features

 - Add option to set decimal places on Dashboard elements ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add option to show detailed PID information on Dashboard element ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add units to PID Dashboard element ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add Fahrenheit conversion to gauges ([#137](https://github.com/kizniche/mycodo/issues/137))
 - Add new Math: Average (Single Measurement) ([#335](https://github.com/kizniche/mycodo/issues/335))

### Bugfixes

 - Allow disabled pigpiod to persist after upgrades ([#386](https://github.com/kizniche/mycodo/issues/386))
 - Fix display of Math measurement/units of Measurement Dashboard element
 - Prevent a large D-value the the first cycle after a PID is activated
 - Handle TypeErrors for Humidity Math controller


## 5.5.22 (2018-02-19)

### Features

 - Add PID-Values to Graphs ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add Dashboard elements: Measurement, Output, PID Control ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add system date and time to menu

### Bugfixes

 - Add checks to ensure Humidity Math only returns 0% - 100% humidity
 - Prevent opposing relays from being turned off in PID Controllers ([#402](https://github.com/kizniche/mycodo/issues/402))
 - Fix adding and viewing hosts in Remote Admin ([#377](https://github.com/kizniche/mycodo/issues/377))
 - Fix error-handling of DS18B20 communication error ([#404](https://github.com/kizniche/mycodo/issues/404))
 - Add error-handling for influxdb queries ([#405](https://github.com/kizniche/mycodo/issues/405))


## 5.5.21 (2018-02-13)

### Bugfixes

 - Add error-handling of DS18B20 communication error ([#404](https://github.com/kizniche/mycodo/issues/404))
 - Fix setup abort from unmet pigpiod dependency ([#406](https://github.com/kizniche/mycodo/issues/406))


## 5.5.20 (2018-02-11)

### Features

 - Add new configuration section: Pi Settings
 - Add to Pi Settings: common ```raspi-config``` options
 - Add to Pi Settings: select pigpiod sample rate ([#386](https://github.com/kizniche/mycodo/issues/386))
 - Add option to completely disable pigpiod ([#386](https://github.com/kizniche/mycodo/issues/386))

### Bugfixes

 - Add ability to set custom Graph colors for Math measurements
 

## 5.5.19 (2018-02-06)

### Features

 - Enable custom minimum/maximum to be set for any y-axis ([#335](https://github.com/kizniche/mycodo/issues/335))
 - Add Asynchronous Graph options for duration of data to display (All or past year, month, week, day)

### Bugfixes

 - Fix saving Math Humidity options ([#400](https://github.com/kizniche/mycodo/issues/400))


## 5.5.18 (2018-02-04)

### Features

 - Allow multiple data series on Asynchronous Graphs ([#399](https://github.com/kizniche/mycodo/issues/399))
 - Add Outputs and PIDs to Asynchronous Graphs ([#399](https://github.com/kizniche/mycodo/issues/399))
 - Preserve Asynchronous Graph selections after form submissions ([#399](https://github.com/kizniche/mycodo/issues/399))

### Bugfixes

 - Fix reloading of asynchronous graphs ([#399](https://github.com/kizniche/mycodo/issues/399))


## 5.5.17 (2018-02-03)

### Features

 - Add option to show/hide Gauge timestamp ([#392](https://github.com/kizniche/mycodo/issues/392))
 - Add new Math: Equation ([#335](https://github.com/kizniche/mycodo/issues/335))
 - Add PID control hysteresis ([#398](https://github.com/kizniche/mycodo/issues/398))
 - Automatically restart pigpiod when it fails

### Bugfixes

 - Move pigpiod from cron to systemd service to improve reliability ([#388](https://github.com/kizniche/mycodo/issues/388))
 - Improve deamon error-handling and Input connectivity ([#388](https://github.com/kizniche/mycodo/issues/388))
 - Fix Mycodo service timeout ([#379](https://github.com/kizniche/mycodo/issues/379))
 - Fix display of Graph custom colors


## 5.5.16 (2018-01-28)

### Bugfixes

 - Fix issue with conditionals not triggering when measurement values are 0 ([#387](https://github.com/kizniche/mycodo/issues/387))
 - Fix issue with settings Output PWM duty cycles
 - Fix issues with Atlas UART module ([#382](https://github.com/kizniche/mycodo/issues/382))
 - Fix issues with calibrating the Atlas pH sensor ([#382](https://github.com/kizniche/mycodo/issues/382))


## 5.5.15 (2018-01-28)

### Features

 - Add Graph button to manually update graph with new data
 - Increase output timing accuracy (0.01 second, previously 0.1 second)
 - Improve graph update efficiency
 - Add Graph option: Enable Graph Shift (used in conjunction with Enable Navbar)
 - Add new Math: Difference ([#395](https://github.com/kizniche/mycodo/issues/395))

### Bugfixes

 - Fix issue modifying the Conditional Max Age ([#387](https://github.com/kizniche/mycodo/issues/387))
 - Fix issue with new data on graphs requiring a page refresh to see
 - Fix issue with updating inputs/maths with long periods on the Live page

### Miscellaneous

 - Remove debug line from GPIO State Input module ([#387](https://github.com/kizniche/mycodo/issues/387))


## 5.5.14 (2018-01-25)

### Bugfixes

 - Fix display of PID timestamp on LCDs
 - Fix missing pigpio.zip (breaks install/upgrade) on remote server (package pigpio.tar with Mycodo)


## 5.5.13 (2018-01-23)

### Features

 - Add Input: GPIO State ([#387](https://github.com/kizniche/mycodo/issues/387))
 - Refactor Dashboard code (improve load time, reduce code size)

### Bugfixes

 - Fix inability to change Input Period ([#393](https://github.com/kizniche/mycodo/issues/393))
 - Fix Exception while reading the GPIO pin of Edge Conditional ([#387](https://github.com/kizniche/mycodo/issues/387))

### Miscellaneous

 - Add Input Template for the [Wiki](https://github.com/kizniche/Mycodo/wiki/Adding-Support-for-a-New-Input)


## 5.5.12 (2018-01-21)

### Features

 - Add two new Inputs: Server Ping and Server Port Open ([#389](https://github.com/kizniche/mycodo/issues/389))


## 5.5.11 (2018-01-21)

### Bugfixes

 - Fix issues with Dashboard Gauges ([#391](https://github.com/kizniche/mycodo/issues/391))
 - Fix issues with Dashboard Cameras

### Miscellaneous

 - Add ID numbers to Conditionals in UI for identification ([#387](https://github.com/kizniche/mycodo/issues/387))


## 5.5.10 (2018-01-20)

### Features

 - Add ability to set graph y-axis minimum/maximum ([#384](https://github.com/kizniche/mycodo/issues/384))
 - Add ability to view Math outputs on asynchronous graphs ([#335](https://github.com/kizniche/mycodo/issues/335))
 - Improve Dashboard Object creation/manipulation user interaction

### Bugfixes

 - Fix inability to activate Edge Conditionals ([#381](https://github.com/kizniche/mycodo/issues/381))
 - Fix inability to add new gauges or graphs to the dashboard ([#384](https://github.com/kizniche/mycodo/issues/384))
 - Fix issues with UART Atlas pH Input device ([#382](https://github.com/kizniche/mycodo/issues/382))
 - Fix issue with Atlas pH calibration ([#382](https://github.com/kizniche/mycodo/issues/382))
 - Fix issue with caching of Camera images on the Dashboard
 - Fix issue with Edge Conditionals ([#387](https://github.com/kizniche/mycodo/issues/387))


## 5.5.9 (2018-01-14)

### Bugfixes

 - Fix issue generating output usage reports ([#380](https://github.com/kizniche/mycodo/issues/380))
 - Fix inability to save Edge Conditionals ([#381](https://github.com/kizniche/mycodo/issues/381))


## 5.5.8 (2018-01-11)

### Features

 - Add ability to add Camera modules to the Dashboard (formerly Live Graphs page)

### Bugfixes

 - Fix issue with new installations failing to start the flask frontend ([#379](https://github.com/kizniche/mycodo/issues/379))
 - Fix issue with services starting on Pi Zeros ([#379](https://github.com/kizniche/mycodo/issues/379))

### Miscellaneous

 - Reduce gunicorn (web UI) workers from 2 to 1


## 5.5.7 (2018-01-08)

### Bugfixes

- Fix forcing of HTTPS via user configuration
- Fix inability to save Gauge Refresh Period option ([#376](https://github.com/kizniche/mycodo/issues/376))
- Fix Atlas Scientific communication issues ([#369](https://github.com/kizniche/mycodo/issues/369))


## 5.5.6 (2018-01-05)

### Features

 - Add ability to restart the frontend from the web UI

### Bugfixes

- Attempt to fix issue where DHT22 sensor may become unresponsive
- Fix inability to stream video from PiCamera


## 5.5.5 (2018-01-04)

### Bugfixes

 - Fix IP address of user login log entries
 - Fix issue reading DHT11 sensor ([#370](https://github.com/kizniche/mycodo/issues/370))


## 5.5.4 (2018-01-03)

### Features

 - Add ability to replace edge variable in edge conditional command action

### Bugfixes

 - Fix issue with proper python 3 virtualenv ([#362](https://github.com/kizniche/mycodo/issues/362))
 - Fix starting web server during install
 - Fix issue with gunicorn worker timeouts on Raspberry Pi Zeros ([#365](https://github.com/kizniche/mycodo/issues/365))
 - Fix command variable replacement for Output conditionals ([#367](https://github.com/kizniche/mycodo/issues/367))
 - Fix pH Input causing an error with a deactivated Calibration Measurement ([#369](https://github.com/kizniche/mycodo/issues/369))
 - Fix issue preventing capture of still images from the web interface ([#368](https://github.com/kizniche/mycodo/issues/368))

### Miscellaneous

 - Move mycodo root symlink from /var/www to /var
 - Create symlinks in PATH for mycodo-backup, mycodo-client, mycodo-commands, mycodo-daemon, mycodo-pip, mycodo-python, mycodo-restore, and mycodo-wrapper


## 5.5.3 (2017-12-29)

### Bugfixes

 - Fix issue with web UI and daemon not restarting properly after upgrade
 - Fix issue with the log not updating properly on the Upgrade page


## 5.5.2 (2017-12-27)

### Features

 - Add Conditional Actions: Flash LCD Off, LCD Backlight On, LCD Backlight Off ([#363](https://github.com/kizniche/mycodo/issues/363))

### Bugfixes

 - Add more log lines to find out exactly which part makes the end of an upgrade hang
 - Fix MHZ16/19 UART communication ([#359](https://github.com/kizniche/mycodo/issues/359))
 - Fix missing I2C devices from System Information page ([#354](https://github.com/kizniche/mycodo/issues/354))
 - Fix output state determination of other outputs if a wireless output is unconfigured ([#364](https://github.com/kizniche/mycodo/issues/364))
 - Fix LCD controller issues with flashing and backlight management


## 5.5.1 (2017-12-25)

### Bugfixes

 - Fix inability to send Conditional email notification to multiple recipients
 - Fix inability to select LCDs as Conditional Actions
 - Fix BME280 sensor module ([#358](https://github.com/kizniche/mycodo/issues/358))
 - Fix TSL2591 sensor module
 - Fix MHZ16/MHZ19 unicode errors (still investigating other potential issues reading these sensors)


## 5.5.0 (2017-12-25)

Merry Christmas!

With the release of 5.5.0, Mycodo becomes modern by migrating from Python 2.7.9 to Python 3 (3.5.3 if on Raspbian Stretch, 3.4.2 if on Raspbian Jessie). This release also brings a big switch from apache2+mod_wsgi to nginx+gunicorn as the web server.

### Issues

***You may experience an error during the upgrade that doesn't allow it to complete***

***It will no longer be possible to restore pre-5.5.0 backups***

***All users will be logged out of the web UI during the upgrade***

***All Conditionals will be deactivated and need reconfiguring***

***OpenCV has been removed as a camera module***

If you rely on your system to work, it is highly recommended that you ***DO NOT UPGRADE***. Wait until your system is no longer performing critical tasks to upgrade, in order to allow yourself the ability to thoroughly test your particular configuration works as expected, and top perform a fresh install if the upgrade fails. Although most parts of the system have been tested to work, there is, as always, the potential for unforeseen issues (for instance, not every sensor that Mycodo supports has physically been tested). Read the following notes carefully to determine if you want to upgrade to 5.5.0 and newer versions.

#### Failure during the upgrade to >= 5.5.0

I found that occasionally the upgrade will spontaneously stop without an indication of the issue. I've seen it happen during an apt-get install and during a pip upgrade. It does not seem consistent, and there were no erorrs, therefore it wasn't able to be fixed. If you experience an error during the upgrade that doesn't allow the upgrade to complete, issue the following commands to attempt to resume and complete the upgrade. If that doesn't fix it, you may have to install Mycodo from scratch.

```bash
sudo dpkg --configure -a
sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_post.sh
```

#### No restoring of pre-5.5.0 backups

Restoring pre-5.5.0 backups will not work. This is due to the moving of the pip virtual environments during the restore, the post-5.5.0 (python3) virtualenv not being compatible with the pre-5.5.0 virtualenv (python2), and moving from the apache2 web server to nginx. If you absolutely need to restore a backup, it must be done manually. Create a new github issue to get asistance with this.

Also with this release, exporting and importing both the Mycodo settings database and InfluxDB measurement database has been added. These may be imported back into Mycodo at a later timer. Currently, the InfluxDB (measurement) database may be imported into any other version of Mycodo, and the Mycodo (settings) database may only be imported to the same version of Mycodo. Automatic upgrading or downgrading of the Mycodo database to allow cross-version compatibility will be included in a future release. For the meantime, if you need to restore Mycodo settings to a particular Mycodo version, you can do the following: download the tar.gz of the particular [Mycodo Release](https://github.com/kizniche/Mycodo/releases) compatible with your database backup, extract, install normally, import the Mycodo settings database, then perform an upgrade of Mycodo to the latest release.

#### All users will be logged out during the upgrade

Another consequence of changing from Python 2 to 3 is current browser cookies will cause an error with the web user interface. Therefore, all users will be logged out after upgrading to >= 5.5.0. This will cause some strange behavior that may be misconstrued as a failed upgrade:
 
 1. The upgrade log will not update during the upgrade. Give the upgrade ample time to finish, or monitor the upgrade log from the command line.
 
 2. After the upgrade is successful, the upgrade log box on the Upgrade page will redirect to the login page. Do not log in through the log box, but rather refresh the entire page to be redirected to the login page.

#### All Conditionals will be deactivated

The Conditional code has been refactored to make them more modular. Because some conditionals will need to be reconfigured before they will operate corectly, all conditionals have been deactivated. Therefore, after the upgrade, reconfigure them appropriately, then reactivate. Additionally, conditionals (for all controllers) have been moved to a new 'Function' page.

#### OpenCV has been disabled

A Python 3 compatible binary version of opencv, whoch doesn't require an extremely long (hours) compiling process, is unfortunately unavailable. Therefore, if you know of a library or module that can successfully acquire an image from your webcam (you have tested to work), create a [new issue](https://github.com/kizniche/Mycodo/issues/new) with the details of how you acquired the image and we can determine if the method can be integrated into Mycddo.

### Features

 - Migrate from Python 2 to Python 3 ([#253](https://github.com/kizniche/mycodo/issues/253))
 - Migrate from apache2 (+mod_wsgi) to nginx (+gunicorn) ([#352](https://github.com/kizniche/mycodo/issues/352))
 - Add ability to export and import Mycodo (settings) database ([#348](https://github.com/kizniche/mycodo/issues/348))
 - Add ability to export and import Influxdb (measurements) database ([#348](https://github.com/kizniche/mycodo/issues/348))
 - Add size of each backup (in MB) on Backup Restore page
 - Add check to make sure there is enough free space before performing a backup/upgrade
 - Add dedicated, modular Conditional controller ([#346](https://github.com/kizniche/mycodo/issues/346))
 - Add PID and Math to input options of Conditionals

### Bugfixes

 - Fix deleting Inputs ([#250](https://github.com/kizniche/mycodo/issues/250))
 - Fix 500 error if 1-wire support isn't enabled
 - Fix Edge Detection Input callback function missing required parameter
 - Fix LCD display of Output duty cycle
 - Fix email notification
 - Make Conditional email notification send after last Action to include all Actions in message

### Miscellaneous

 - Disable the use of the opencv camera library
 - Update translations
 - Combine Input and Math pages to a new 'Data' page
 - Move Conditionals and PIDs to a new 'Function' page
 - Show tooltips by default


## 5.4.19 (2017-12-15)

### Features

 - Add ability to use other Math controller outputs as Math controller inputs
 - Add checks to ensure a measurement is selected for Gauges

### Bugfixes

 - Fix not deleting associated Math Conditionals when a Math controller is deleted
 - Fix displaying LCD lines for Controllers/Measurements that no longer exist
 - Fix improper WBT input-checking for humidity math controller
 - Fix issue where Math controller could crash ([#335](https://github.com/kizniche/mycodo/issues/335))


## 5.4.18 (2017-12-15)

### Bugfixes

 - Fix error on Live page if no Math controllers exist ([#345](https://github.com/kizniche/mycodo/issues/345))


## 5.4.17 (2017-12-14)

### Features

 - Add Decimal Places option to LCD lines

### Bugfixes

 - Fix Input conditional refresh upon settings change
 - Fix display of Math controllers with atypical measurements on Live page ([#343](https://github.com/kizniche/mycodo/issues/343))
 - Fix inability to use Math controller values with PID Controllers ([#343](https://github.com/kizniche/mycodo/issues/343))
 - Fix display of Math data on LCDs ([#343](https://github.com/kizniche/mycodo/issues/343))
 - Fix LCD Max Age only working for first line
 - Fix display of Math data on LCDs
 - Fix issue displaying some Graph page configurations
 - Fix issue with PID recording negative durations
 - Fix Date Methods ([#344](https://github.com/kizniche/mycodo/issues/344))

### Miscellaneous

 - Place PID Controllers in a subcategory of new section called Function
 - Don't disable an LCD when an Input that's using it is disabled


## 5.4.16 (2017-12-13)

### Features

 - Add new Math controller type: Median
 - Add the ability to use Conditionals with Math controllers
 - Add ability to use Math Controllers with LCDs and PIDs
 - Add Math Controllers to Live page
 - Add Math and PID Controllers to Gauge measurement selection ([#342](https://github.com/kizniche/mycodo/issues/342))
 - Add "None Found Last x Seconds" to Conditional options (trigger action if a measurement was not found within the last x seconds)
 - Add Restart Daemon option to the Config menu
 - More detailed 'incorrect database version' error message on System Information page

### Bugfixes

 - Fix measurement list length on Graph page
 - Fix PWM output display on Live page
 - Fix issue changing Gauge type ([#342](https://github.com/kizniche/mycodo/issues/342))
 - Fix display of multiplexer options for I2C devices
 - Fix display order of I2C busses on System Information page

### Miscellaneous

 - Add new multiplexer overlay option to manual ([#184](https://github.com/kizniche/mycodo/issues/184))


## 5.4.15 (2017-12-08)

### Features

 - Add Math controller types: Humidity, Maximum, Minimum, and Verification ([#335](https://github.com/kizniche/mycodo/issues/335))

### Bugfixes

 - Fix Atlas pH sensor calibration


## 5.4.14 (2017-12-05)

### Features

 - Add Math Controller (Math in menu) to perform math on Input data
 - Add first Math controller type: Average ([#328](https://github.com/kizniche/mycodo/issues/328))
 - Add fswebcam as a camera library for acquiring images from USB cameras
 - Complete Spanish translation
 - Update korean translations
 - Add more translatable texts
 - Make PIDs collapsible
 - Refactor daemon controller handling and daemonize threads

### Bugfixes

 - Fix TCA9548A multiplexer channel issues ([#330](https://github.com/kizniche/mycodo/issues/330))
 - Fix selection of current language on General Config page
 - Fix saving options when adding a Timer
 - Fix Graph display of Lowering Output durations as negative values
 - Fix double-logging of output durations

### Miscellaneous

 - Update Manual with Math Controller information


## 5.4.11 (2017-11-29)

### Bugfixes

 - Fix issue displaying Camera page


## 5.4.10 (2017-11-28)

### Features

 - Add display of all detected I2C devices on the System Information page

### Bugfixes

 - Change web UI restart command
 - Fix issue saving Timer options ([#334](https://github.com/kizniche/mycodo/issues/334))
 - Fix Output Usage error


## 5.4.9 (2017-11-27)

### Bugfixes

 - Fix adding Gauges ([#333](https://github.com/kizniche/mycodo/issues/333))


## 5.4.8 (2017-11-22)

### Features

 - Add 1 minute, 5 minute, and 15 minute options to Graph Range Selector ([#319](https://github.com/kizniche/mycodo/issues/319))

### Bugfixes

 - Fix AM2315 sensor measurement acquisition ([#328](https://github.com/kizniche/mycodo/issues/328))


## 5.4.7 (2017-11-21)

### Bugfixes

 - Fix flood of errors in the log if an LCD doesn't have a measurement to display
 - Fix LCD display being offset one character when displaying errors


## 5.4.6 (2017-11-21)

### Features

 - Add Max Age (seconds) to LCD line options
 - Make LCDs collapsable in the web UI

### Bugfixes

 - Fix saving user theme ([#326](https://github.com/kizniche/mycodo/issues/326))


## 5.4.5 (2017-11-21)

### Features

 - Add Freqency, Duty Cycle, Pulse Width, RPM, and Linux Command variables to Conditional commands ([#311](https://github.com/kizniche/mycodo/issues/311)) (See [Input Conditional command variables](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md#input-conditional-command-variables))
 - Add Graph options: Enable Auto Refresh, Enable Title, and Enable X-Axis Reset ([#319](https://github.com/kizniche/mycodo/issues/319))
 - Add automatic checks for Mycodo updates (can be disabled in the configuration)

### Bugfixes

 - Fix Input Conditional variable


## 5.4.4 (2017-11-19)

### Features

 - Add 12-volt DC fan control circuit to manual (@Theoi-Meteoroi) ([#184](https://github.com/kizniche/mycodo/issues/184)) (See [Schematics for DC Fan Control](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md#schematics-for-dc-fan-control))

### Bugfixes

 - Fix PWM Signal, RPM Signal, DHT22, and DHT11 Inputs ([#324](https://github.com/kizniche/mycodo/issues/324))
 - Add Frequency, Duty Cycle, Pulse Width, and RPM to y-axis Graph display

### Miscellaneous

 - Upgrade InfluxDB from 1.3.7 to 1.4.2


## 5.4.3 (2017-11-18)

### Bugfixes

 - Fix Output Conditional triggering ([#323](https://github.com/kizniche/mycodo/issues/323))
 

## 5.4.2 (2017-11-18)

### Features

 - Add Output Conditional If option of "On (any duration)" ([#323](https://github.com/kizniche/mycodo/issues/323)) (See [Output Conditional Statement If Options](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md#output-conditional-statement-if-options))

### Bugfixes

 - Fix display of first point of Daily Bezier method
 - Fix inability to use Daily Bezier method in PID ([#323](https://github.com/kizniche/mycodo/issues/323))
 - Fix saving Output options and turning Outputs On and Off


## 5.4.1 (2017-11-17)

### Features

 - Prevent currently-logged in user from: deleting own user, changing user role from Admin
 - Force iPhone to open Mycodo bookmark as standalone web app instead of in Safari
 - Refactor and add tests for all inputs ([#128](https://github.com/kizniche/mycodo/issues/128))
 - Add Flask-Limiter to limit authentication requests to 30 per minute (mainly for Remote Admin feature)
 - Add first working iteration of data acquisition to the Remote Admin dashboard
 - Add SSL certificate authentication with Remote Admin communication

### Bugfixes

 - Fix inability to modify timer options ([#318](https://github.com/kizniche/mycodo/issues/318))

### Miscellaneous

 - Rename objects (warning: this may break some things. I tried to be thorough with testing)
 - Switch from using init.d to systemd for controlling apache2


## 5.4.0 (2017-11-12)

This release has refactored how LCD displays are handled, now allowing an infinite number of data sets on a single LCD.

Note: All LDCs will be deactivated during the upgrade. As a consequence, LCD displays will need to be reconfigured and reactivated.

***Note 2: During the upgrade, the web interface will display "500 Internal Server Error." This is normal and you should give Mycodo 5 to 10 minutes (or longer) to complete the upgrade process before attempting to access the web interface again.***

### Features

 - Add ability to cycle infinite sets of data on a single LCD display ([#316](https://github.com/kizniche/mycodo/issues/316))
 - Add logrotate script to manage mycodo logs

### Bugfixes

 - Fix language selection being applied globally (each user now has own language)
 - Fix display of degree symbols on LCDs


## 5.3.6 (2017-11-11)

### Features

 - Allow camera options to be used for picamera library

### Bugfixes

 - Fix inability to take a still image while a video stream is active
 - Make creating new user names case-insensitive
 - Fix theme not saving when creating a new user

### Miscellaneous

 - Remove ability to change camera library after a camera has been added
 - Update Korean translation


## 5.3.5 (2017-11-10)

### Features

 - Add timestamp to lines of the upgrade/backup/restore logs
 - Add sensor measurement smoothing to Chirp light sensor (module will soon expand to all sensors)
 - Add ability to stream video from USB cameras
 - Add ability to stream video from several cameras at the same time

### Bugfixes

 - Fix an issue loading the camera settings page without a camera connected
 - Fix video streaming with Pi Camera ([#228](https://github.com/kizniche/mycodo/issues/228))

### Miscellaneous

 - Split flaskform.py and flaskutils.py into smaller files for easier management


## 5.3.4 (2017-11-06)

Note: The Chirp light sensor scale has been inverted. Please adjust your settings accordingly to respond to 0 as darkness and 65535 as bright.

### Features

 - Replace deprecated LockFile with fasteners ([#260](https://github.com/kizniche/mycodo/issues/260))
 - Add Timer type: PWM duty cycle output using Method ([#262](https://github.com/kizniche/mycodo/issues/262)), read more: [PWM Method](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md#pwm-method)

### Bugfixes

 - Fix display of PID setpoints on Graphs
 - Invert Chirp light sensor scale (0=dark, 65535=bright)

### Miscellaneous

 - Update Korean translations
 - Add 2 more significant digits to ADC voltage measurements
 - Upgrade InfluxDB to v1.3.7


## 5.3.3 (2017-10-29)

### Features

 - Add Sample Time option to PWM and RPM Input options ([#302](https://github.com/kizniche/mycodo/issues/302))

### Bugfixes

 - Fix issues with PWM and RPM Inputs ([#306](https://github.com/kizniche/mycodo/issues/306))


## 5.3.2 (2017-10-28)

### Features

 - Turning Outputs On or Off no longer refreshes the page ([#192](https://github.com/kizniche/mycodo/issues/192))

### Bugfixes

 - Fix exporting measurements
 - Fix Live Data page displaying special characters ([#304](https://github.com/kizniche/mycodo/issues/304))
 - Fix PWM and RPM Input issues ([#302](https://github.com/kizniche/mycodo/issues/302))

## 5.3.1 (2017-10-27)

### Features

 - Add two new Inputs: PWM and RPM ([#302](https://github.com/kizniche/mycodo/issues/302))
 - Allow a PID to use both Relay and PWM Outputs ([#303](https://github.com/kizniche/mycodo/issues/303))


## 5.3.0 (2017-10-24)

#### ***IMPORTANT***

Because of a necessary database schema change, this update will deactivate all PID controllers and deselect the input measurement. All PID controllers will need the input measurement reconfigured before they can be started again.

### Features

Input and Output Conditional commands may now include variables. There are 23 variables currently-supported. See [Conditional Statement variables](https://github.com/kizniche/Mycodo/blob/master/mycodo-manual.md#conditional-statement-variables) for details.

 - Add new Input type: Linux Command (measurement is the return value of an executed command) ([#264](https://github.com/kizniche/mycodo/issues/264))
 - Refactor PID input option to allow new input and simplify PID configuration
 - Add ability to select LCD I2C bus ([#300](https://github.com/kizniche/mycodo/issues/300))
 - Add ADC Option to Inverse Scale ([#297](https://github.com/kizniche/mycodo/issues/300))
 - Add ability to use variables in Input/Output Conditional commands

### Bugfixes

 - Fix "Too many files open" error when using the TSL2591 sensor ([#254](https://github.com/kizniche/mycodo/issues/254))
 - Fix bug that had the potential to lose data with certain graph display configurations
 - Prevent more than one active PID from using the same output ([#108](https://github.com/kizniche/mycodo/issues/108))
 - Prevent a PID from using the same Raise and Lower output
 - Prevent a currently-active PID from changing the output to a currently-used output

### Miscellaneous

 - Update Readme and Wiki to fix outdated and erroneous information and improve coverage ([#285](https://github.com/kizniche/mycodo/issues/285))


## 5.2.5 (2017-10-14)

### Features

 - Add another status indicator color (top-left of web UI): Orange: unable to connect to daemon

### Bugfixes

 - Fix Asynchronous Graphs ([#296](https://github.com/kizniche/mycodo/issues/296))
 - Disable sensor tests to fix testing environment (will add later when the issue is diagnosed)


## 5.2.4 (2017-10-05)

### Features

 - Add ability to set time to end repeating duration method


## 5.2.3 (2017-09-29)

### Bugfixes

 - Fix issues with method repeat option


## 5.2.2 (2017-09-27)

### Features

 - Add 'restart from beginning' option to PID duration methods
 
### Bugfixes

 - Fix adding new graphs


## 5.2.1 (2017-09-21)

### Bugfixes

 - Fix changing a gauge from angular to solid ([#274](https://github.com/kizniche/mycodo/issues/274))


## 5.2.0 (2017-09-17)

### Features

 - Add gauges to Live Graphs ([#274](https://github.com/kizniche/mycodo/issues/274))


## 5.1.10 (2017-09-12)

### Bugfixes

 - Fix issue reporting issue with the web UI communicating with the daemon ([#291](https://github.com/kizniche/mycodo/issues/291))


## 5.1.9 (2017-09-07)

### Features

 - Enable daemon monitoring script (cron @reboot) to start the daemon if it stops

### Bugfixes

 - Potential fix for certain sensor initialization issues when using a multiplexer ([#290](https://github.com/kizniche/mycodo/issues/290))
 - Handle connection error when the web interface cannot connect to the daemon/relay controller ([#289](https://github.com/kizniche/mycodo/issues/289))


## 5.1.8 (2017-08-29)

### Bugfixes

 - Fix saving relay start state ([#289](https://github.com/kizniche/mycodo/issues/289))


## 5.1.7 (2017-08-29)

### Bugfixes

 - Fix MH-Z16 sensor issues in I2C read mode ([#281](https://github.com/kizniche/mycodo/issues/281))
 - Fix Atlas Scientific I2C device query response in the event of an error
 - Fix issue preventing PID from using duration Methods
 - Fix issue with PID starting a method again after it has already ended
 - Fix TSL2591 sensor ([#257](https://github.com/kizniche/mycodo/issues/257))
 - Fix saving relay trigger state ([#289](https://github.com/kizniche/mycodo/issues/289))


## 5.1.6 (2017-08-11)

### Features

 - Add MH-Z16 sensor module ([#281](https://github.com/kizniche/mycodo/issues/281))


## 5.1.5 (2017-08-11)

### Bugfixes

 - Fix MH-Z19 sensor module ([#281](https://github.com/kizniche/mycodo/issues/281))


## 5.1.4 (2017-08-11)

### Features

 - Update InfluxDB (v1.3.3) and pip packages

### Bugfixes

 - Fix K30 sensor module ([#279](https://github.com/kizniche/mycodo/issues/279))


## 5.1.3 (2017-08-10)

### Bugfixes

 - Fix install issue in setup.sh install script (catch 1-wire error if not enabled) ([#258](https://github.com/kizniche/mycodo/issues/258))


## 5.1.2 (2017-08-09)

### Bugfixes

 - Fix new timers not working ([#284](https://github.com/kizniche/mycodo/issues/284))


## 5.1.1 (2017-08-09)

### Features

 - Add live display of upgrade log during upgrade
 
### Bugfixes

 - Fix setup bug preventing database creation ([#277](https://github.com/kizniche/mycodo/issues/277), [#278](https://github.com/kizniche/mycodo/issues/278), [#283](https://github.com/kizniche/mycodo/issues/283))


## 5.1.0 (2017-08-07)

Some graphs will need to be manually reconfigured after upgrading to 5.1.0. This is due to adding PWM as an output and PID option, necessitating refactoring certain portions of code related to graph display.

### Features

 - Add PWM support as output ([#262](https://github.com/kizniche/mycodo/issues/262))
 - Add PWM support as PID output
 - Add min and max duty cycle options to PWM PID
 - Add "Max Amps" as a general configuration option
 - Improve error reporting for devices and sensors
 - Add ability to power-cycle the DHT11 sensor if 3 consecutive measurements cannot be retrieved (uses power relay option) ([#273](https://github.com/kizniche/mycodo/issues/273))
 - Add MH-Z19 CO2 sensor

### Bugfixes

 - Upgrade to InfluxDB 1.3.1 ([#8500](https://github.com/influxdata/influxdb/issues/8500) - fixes InfluxDB going unresponsive)
 - Fix K30 sensor module


## 5.0.49 (2017-07-13)

### Bugfixes

 - Move relay_usage_reports directory to new version during upgrade
 - Fix LCD display of PID setpoints with long float values (round two decimal places)
 - Fix geocoder issue


## 5.0.48 (2017-07-11)

### Features

 - Add power relay to AM2315 sensor configuration ([#273](https://github.com/kizniche/mycodo/issues/273))


## 5.0.47 (2017-07-09)

### Bugfixes

 - Fix upgrade script


## 5.0.46 (2017-07-09)

### Bugfixes

 - Fix upgrade initialization to include setting permissions


## 5.0.45 (2017-07-07)

### Bugfixes

 - Fix minor bug that leaves the .upgrade file in a backup, causing issue with upgrading after a restore


## 5.0.44 (2017-07-06)

### Bugfixes

 - Fix issues with restore functionality (still possibly buggy: use at own risk)


## 5.0.43 (2017-07-06)

### Bugfixes

 - Fix issues with restore functionality (still possibly buggy: use at own risk)


## 5.0.42 (2017-07-06)

### Features

 - Update InfluxDB to 1.3.0
 - Update pip package (geocoder)


## 5.0.41 (2017-07-06)

### Features

 - Add ability to restore backup (Warning: Experimental feature, not thoroughly tested)
 - Add ability to view the backup log on View Logs page
 - Add script to check if daemon uncleanly shut down during upgrade and remove stale PID file ([#198](https://github.com/kizniche/mycodo/issues/198))

### Bugfixes

 - Fix error if country cannot be detected for anonymous statistics


## 5.0.40 (2017-07-03)

### Bugfixes

 - Fix install script error ([#253](https://github.com/kizniche/mycodo/issues/253))
 - Fix issue modulating relays if a conditionals using them are not properly configured ([#266](https://github.com/kizniche/mycodo/issues/266))


## 5.0.39 (2017-06-27)

### Bugfixes

 - Fix upgrade process


## 5.0.38 (2017-06-27)

### Bugfixes

 - Fix install script


## 5.0.37 (2017-06-27)

### Bugfixes

 - Change wiringpi during install


## 5.0.36 (2017-06-27)

### Features

 - Add ability to create a Mycodo backup
 - Add ability to delete a Mycodo backup
 - Remove mycodo-wrapper binary in favor of compiling it from source code during install/upgrade

### Bugfixes

 - Fix issue with influxdb database and user creation during install ([#255](https://github.com/kizniche/mycodo/issues/255))
 
### Work in progress

 - Add ability to restore a Mycodo backup


## 5.0.35 (2017-06-18)

### Bugfixes

 - Fix swap size check (and change to 512 MB) to permit pi_switch module compilation size requirement ([#258](https://github.com/kizniche/mycodo/issues/258))


## 5.0.34 (2017-06-18)

### Features

 - Add TSL2591 luminosity sensor ([#257](https://github.com/kizniche/mycodo/issues/257))
 - Update sensor page to more compact style

### Bugfixes

 - Append setup.sh output to setup.log instead of overwriting ([#255](https://github.com/kizniche/mycodo/issues/255))
 - Fix display of error response when attempting to modify timer when it's active


## 5.0.33 (2017-06-05)

### Features

 - Add new relay type: Execute Commands (executes linux commands to turn the relay on and off)

### Bugfixes

 - Fix query of ADC unit data (not voltage) from influxdb
 
### Miscellaneous

 - Update influxdb to version 1.2.4
 - Update pip packages
 - Update Manual
 - Update translatable texts


## 5.0.32 (2017-06-02)

### Bugfixes

 - Fix display of PID output and setpoint on live graphs ([#252](https://github.com/kizniche/mycodo/issues/252))


## 5.0.31 (2017-05-31)

### Features

 - Add option to not turn wireless relay on or off at startup

### Bugfixes

 - Fix inability to save SHT sensor options ([#251](https://github.com/kizniche/mycodo/issues/251))
 - Fix inability to turn relay on if another relay is unconfigured ([#251](https://github.com/kizniche/mycodo/issues/251))


## 5.0.30 (2017-05-23)

### Bugfixes

 - Fix display of proper relay status if pin is 0


## 5.0.29 (2017-05-23)

### Features

 - Relay and Timer page style improvements

### Bugfixes

 - Add influxdb query generator with input checks


## 5.0.28 (2017-05-23)

### Features

  - Add support for Atlas Scientific pH Sensor ([#238](https://github.com/kizniche/mycodo/issues/238))
  - Add support for calibrating the Atlas Scientific pH sensor
  - Add UART support for Atlas Scientific PT-1000 sensor
  - Update Korean translations
  - Add measurement retries upon CRC fail for AM2315 sensor ([#246](https://github.com/kizniche/mycodo/issues/246))
  - Add page error handler that provides full traceback when the Web UI crashes
  - Display live pH measurements during pH sensor calibration
  - Add ability to clear calibration data from Atlas Scientific pH sensors
  - Add sensor option to calibrate Atlas Scientific pH sensor with the temperature from another sensor before measuring pH
  - Add 433MHz wireless transmitter/receiver support for relay actuation ([#88](https://github.com/kizniche/mycodo/issues/88), [#245](https://github.com/kizniche/mycodo/issues/245))

### Bugfixes

  - Fix saving of proper start time during timer creation ([#248](https://github.com/kizniche/mycodo/issues/248))
  - Fix unicode error when generating relay usage reports


## 5.0.27 (2017-04-12)

### Bugfixes

  - Fix issue with old database entries and new graph page parsing
  - Revert to old relay form submission method (ajax method broken)


## 5.0.26 (2017-04-12)

### Bugfixes

  - Fix critical issue with upgrade script


## 5.0.25 (2017-04-12)

### Bugfixes

  - Fix setting custom graph colors


## 5.0.24 (2017-04-12)

### Features

  - Add toastr and ajax support for submitting forms without refreshing the page (currently only used with relay On/Off/Duration buttons) ([#70](https://github.com/kizniche/mycodo/issues/70))

### Bugfixes

  - Fix issue with changing ownership of SSL certificates during install ([#240](https://github.com/kizniche/mycodo/issues/240))
  - Fix PID Output not appearing when adding new graph (modifying graph works)
  - Remove ineffective upgrade reversion script (reversion was risky)


## 5.0.23 (2017-04-10)

### Features

  - Add PID Output as a graph display option (useful for tuning PID controllers)

### Bugfixes

  - Fix display of unicode characters ([#237](https://github.com/kizniche/mycodo/issues/237))


## 5.0.22 (2017-04-08)

### Features

  - Add sensor conditional: emailing of photo or video (video only supported by picamera library at the moment) ([#226](https://github.com/kizniche/mycodo/issues/226))

### Bugfixes

  - Fix inability to display Sensor page if unable to detect DS18B20 sensors ([#236](https://github.com/kizniche/mycodo/issues/236))
  - Fix inability to disable relay during camera capture
  - Fix SSL generation script and strengthen from 2048 bit to 4096 bit RSA ([#234](https://github.com/kizniche/mycodo/issues/234))

### Miscellaneous

  - New cleaner Timer page style


## 5.0.21 (2017-04-02)

### Bugfixes

  - Fix BMP280 sensor module initialization ([#233](https://github.com/kizniche/mycodo/issues/233))
  - Fix saving and display of PID and Relay values on LCDs


## 5.0.20 (2017-04-02)

### Bugfixes

  - Fix BMP280 sensor module initialization
  - Fix saving and display of PID and Relay values on LCDs
  - Fix inability to select certain measurements for a sensor under the PID options


## 5.0.19 (2017-04-02)

### Bugfixes

  - Fix BMP280 sensor I<sup>2</sup>C address options ([#233](https://github.com/kizniche/mycodo/issues/233))


## 5.0.18 (2017-04-01)

### Features

  - Add BMP280 I2C temperature and pressure sensor ([#233](https://github.com/kizniche/mycodo/issues/233))


## 5.0.17 (2017-03-31)

### Bugfixes

  - Fix issue with graph page crashing when non-existent sensor referenced ([#232](https://github.com/kizniche/mycodo/issues/232))


## 5.0.16 (2017-03-30)

### Features

  - New Mycodo Manual rendered in markdown, html, pdf, and plain text

### Bugfixes

  - Fix BME280 sensor module to include calibration code (fixes "stuck" measurements)
  - Fix issue with graph page crashing when non-existent sensor referenced ([#231](https://github.com/kizniche/mycodo/issues/231))


## 5.0.15 (2017-03-28)

### Bugfixes

  - Fix issue with graph page errors when creating a graph with PIDs or Relays
  - Fix sensor conditional measurement selections ([#230](https://github.com/kizniche/mycodo/issues/230))
  - Fix inability to stream video from a Pi camera ([#228](https://github.com/kizniche/mycodo/issues/228))
  - Fix inability to delete LCD ([#229](https://github.com/kizniche/mycodo/issues/229))
  - Fix measurements export
  - Fix display of BMP and BH1750 sensor measurements in sensor lists (graphs/export)

### Miscellaneous

  - Better exception-handling (clean up logging of influxdb measurement errors)


## 5.0.14 (2017-03-25)

### Features

  - Add BH1750 I2C light sensor ([#224](https://github.com/kizniche/mycodo/issues/224))

### Bugfixes

  - Change default opencv values for new cameras ([#225](https://github.com/kizniche/mycodo/issues/225))
  - Fix relays not recording proper ON duration (which causes other issues) ([#223](https://github.com/kizniche/mycodo/issues/223))
  - Fix new graphs occupying 100% width (12/12 columns)


## 5.0.13 (2017-03-24)

### Bugfixes

  - Fix issue with adding/deleting relays
  - Fix inability to have multiple graphs appear on the same row
  - Fix UnicodeEncodeError when using translations
  - Fix BME280 sensor pressure/altitude


## 5.0.12 (2017-03-23)

### Bugfixes

  - Fix frontend and backend issues with conditionals


## 5.0.11 (2017-03-22)

### Bugfixes

  - Fix alembic database upgrade error (hopefully)


## 5.0.10 (2017-03-22)

### Bugfixes

  - Fix photos being taken uncontrollably when a time-lapse is active


## 5.0.9 (2017-03-22)

### Bugfixes

  - Update geocoder to 1.21.0 to attempt to resolve issue
  - Fix creation of alembic version number in database of new install
  - Add suffixes to distinguish Object from Die temperatures of TMP006 sensor on Live page
  - Fix reference to pybabel in virtualenv


## 5.0.8 (2017-03-22)

### Features

  - Add option to hide tooltips

### Bugfixes

  - Add alembic upgrade check as a part of flask app startup
  - Fix reference to alembic for database upgrades
  - Fix photos being taken uncontrollably when a time-lapse is active
  - Show edge measurements as vertical bars instead of lines on graphs
  - Fix default image width/height when adding cameras
  - Prevent attempting to setup a relay at startup if the GPIO pin is < 1
  - Add coverage where DHT22 sensor could be power cycled to fix an inability to acquire measurements
  - Display the device name next to each custom graph color
  - Fix encoding error when collecting anonymous statistics ([#216](https://github.com/kizniche/mycodo/issues/216))

### Miscellaneous

  - Update Influxdb to version 1.2.2
  - UI style improvements


## 5.0.7 (2017-03-19)

### Bugfixes

  - Fix pybabel reference during install/upgrade ([#212](https://github.com/kizniche/mycodo/issues/212))


## 5.0.6 (2017-03-19)

### Bugfixes

  -  Fix edge detection conditional statements ([#214](https://github.com/kizniche/mycodo/issues/214))
  -  Fix identification and conversion of dewpoint on live page ([#215](https://github.com/kizniche/mycodo/issues/215))


## 5.0.5 (2017-03-18)

### Bugfixes

  - Fix issue with timers not actuating relays ([#213](https://github.com/kizniche/mycodo/issues/213))


## 5.0.4 (2017-03-18)

### Bugfixes

  - Fix issues with saving LCD options ([#211](https://github.com/kizniche/mycodo/issues/211))


## 5.0.0 (2017-03-18)

### Bugfixes

  - Fixes inability of relay conditionals to operate ([#209](https://github.com/kizniche/mycodo/issues/209), [#210](https://github.com/kizniche/mycodo/issues/210))
  - Fix issue with user creation/deletion in web UI
  - Fix influxdb being unreachable directly after package install

### Features

  - Complete Spanish translation
  - Add auto-generation of relay usage/cost reports on a daily, weekly, or monthly schedule
  - Add ability to check daemon health (mycodo_client.py --checkdaemon)
  - Add sensor conditional actions: Activate/Deactivate PID, Email Photo, Email Video
  - Add PID option: maximum allowable sensor measurement age (to allow the PID controller to manipulate relays, the sensor measurement must have occurred in the past x seconds)
  - Add PID option: minimum off duration for lower/raise relay (protects devices that require a minimum off period by preventing power cycling from occurring too quickly)
  - Add new sensor: Free Disk Space (of a set path)
  - Add new sensor: Mycodo Daemon RAM Usage (used for testing)
  - Add ability to use multiple camera configurations (multiple cameras)
  - Add OpenCV camera library to allow use of USB cameras ([#193](https://github.com/kizniche/mycodo/issues/193))
  - Automatically detect DS18B20 sensors in sensor configuration
  - Add ability to create custom user roles
  - Add new user roles: Editor and Monitor ([#46](https://github.com/kizniche/mycodo/issues/46))

### Miscellaneous

  - Mobile display improvements
  - Improve content and accessibility of help documentation
  - Redesign navigation menu (including glyphs from bootstrap and fontawesome)
  - Move to using a Python virtual environment ([#203](https://github.com/kizniche/mycodo/issues/203))
  - Refactor the relay/sensor conditional management system
  - User names are no longer case-sensitive
  - Switch to using Flask-Login
  - Switch to using flask_wtf.FlaskForm (from using deprecated flask_wtf.Form)
  - Update web interface style and layout
  - Update influxdb to 1.2.1
  - Update Flask WTF to 0.14.2
  - Move from using sqlalchemy to flask sqlalchemy
  - Restructure database ([#115](https://github.com/kizniche/mycodo/issues/115), [#122](https://github.com/kizniche/mycodo/issues/122))


## 4.2.0 (2017-03-16)

### Features

  - Add ability to turn a relay on for a specific duration of time
  - Update style of Timer and Relay pages (mobile-compatibility)


## 4.1.16 (2017-02-05)

### Bugfixes

  - Revert back to influxdb 1.1.1 to fix LCD time display ([#7877](https://github.com/influxdata/influxdb/issues/7877) will fix, when released)
  - Fix influxdb not restarting after a new version is installed
  - Fix issue with relay conditionals being triggered upon shutdown
  - Fix asynchronous graph to use local timezone rather than UTC ([#185](https://github.com/kizniche/mycodo/issues/185))

### Miscellaneous

  - Remove archived versions of Mycodo (Mycodo/old) during upgrade (saves space during backup)


## 4.1.15 (2017-01-31)

### Bugfixes

  - Fix LCD KeyError from missing measurement unit for durations_sec


## 4.1.14 (2017-01-30)

### Bugfixes

  - Fix DHT11 sensor module ([#176](https://github.com/kizniche/mycodo/issues/176))

### Miscellaneous

  - Update influxdb to 1.2.0


## 4.1.13 (2017-01-30)

### Bugfixes

  - Fix DHT11 sensor module ([#176](https://github.com/kizniche/mycodo/issues/176))


## 4.1.12 (2017-01-30)

### Bugfixes

  - Fix PID controller crash


## 4.1.11 (2017-01-30)

This is a small update, mainly to fix the install script. It also *should* fix the DHT11 sensor module from stopping at the first bad checksum.

### Bugfixes

  - Fix DHT11 sensor module, removing exception preventing acquisition of future measurements ([#176](https://github.com/kizniche/mycodo/issues/176))
  - Fix setup.sh install script by adding git as a dependency ([#183](https://github.com/kizniche/mycodo/issues/183))
  - Fix initialization script executed during install and upgrade


## 4.1.10 (2017-01-29)

### Bugfixes

  - Fix PID variable initializations
  - Fix KeyError in controller_lcd.py
  - Fix camera termination bug ([#178](https://github.com/kizniche/mycodo/issues/178))
  - Fix inability to pause/hold/resume PID controllers

### Miscellaneous

  - Add help text for conditional statements to relay page ([#181](https://github.com/kizniche/mycodo/issues/181))


## 4.1.9 (2017-01-27)

This update fixes two major bugs: Sometimes admin users not being created properly from the web UI and the daemon not being set to automatically start during install.

This update also fixes an even more severe bug affecting the database upgrade system. If you installed a system before this upgrade, you are probably affected. This release will display a message indicating if your database has an issue. Deleting ~/Mycodo/databases/mycodo.db and restarting the web server (or reboot) will regenerate the database.

If your daemon doesn't automatically start because you installed it with a botched previous version, issue the following commands to add it to systemctl's autostart:

***Important***: Make sure you rename 'user' below to your actual user where you installed Mycodo, and make sure the Mycodo install directory is correct and points to the correct mycodo.service file.

```
sudo service mycodo stop
sudo systemctl disable mycodo.service
sudo rm -rf /etc/systemd/system/mycodo.service
sudo systemctl enable /home/user/Mycodo/install/mycodo.service
sudo service mycodo start
```

### Features

  - Add check for problematic database and notify user how to fix it
  - Add ability to define the colors of lines on general graphs ([#161](https://github.com/kizniche/mycodo/issues/161))

### Bugfixes

  - Update install instructions to correct downloading the latest release tarball
  - Fix for database upgrade bug that has been plaguing Mycodo for the past few releases
  - Fix incorrect displaying of graphs with relay or PID data
  - Fix relay turning off when saving relay settings and GPIO pin doesn't change
  - Fix bug that crashes the daemon if the user database is empty
  - Fix Spanish translation file errors
  - Fix mycodo daemon not automatically starting after install
  - Fix inability to create admin user from the web interface
  - Fix inability to delete methods
  - Fix Atlas PT100 sensor module 'invalid literal for float()' error
  - Fix camera termination bug ([#178](https://github.com/kizniche/mycodo/issues/178))

Miscellaneous

  - Add new theme: Sun


## 4.1.8 (2017-01-21)

### Bugfixes

  - Actually fix the upgrade system (mycodo_wrapper)
  - Fix bug in DHT22 sensor module preventing measurements
  - Fix inability to show latest time-lapse image on the camera page (images are still being captured)

### Miscellaneous

  - Update Spanish translations


## 4.1.7 (2017-01-19)

### Bugfixes

  - Fix upgrade system (mycodo_wrapper). This may have broke the upgrade system (if so, use the manual method in the README)
  - Fix time-lapses not resuming after an upgrade
  - Fix calculation of total 1-month relay usage and cost
  - Fix (and modify) the logging behavior in modules
  - Fix K30 sensor module returning None as a measurement value
  - Fix gpiod being added to crontab during install from setup.sh ([#174](https://github.com/kizniche/mycodo/issues/174))


## 4.1.6 (2017-01-17)

### Features

  - Add ability to export selected measurement data (in CSV format) from a date/time span

### Bugfixes

  - Fix issue with setup.sh when the version of wget<1.16 ([#173](https://github.com/kizniche/mycodo/issues/173))
  - Fix error calculating rely usage when it's currently the billing day of the month

### Miscellaneous

  - Remove Sensor Logs (Tools/Sensor Logs). The addition of the measurement export feature in this release deprecates Sensor Logs. Note that by the very nature of how the Sensor Log controllers were designed, there was a high probability of missing measurements. The new measurement export feature ensures all measurements are exported.
  - Add more translatable text
  - Add password repeat input when creating new admin user


## 4.1.5 (2017-01-14)

### Bugfixes

  - Fix DHT11 sensor module not returning values ([#171](https://github.com/kizniche/mycodo/issues/171))
  - Fix HTU21D sensor module not returning values ([#172](https://github.com/kizniche/mycodo/issues/172))


## 4.1.4 (2017-01-13)

This release introduces a new method for upgrading Mycodo to the latest version. Upgrades will now be performed from github releases instead of commits, which should prevent unintended upgrades to the public, facilitate bug-tracking, and enable easier management of a changelog.

### Performance

  - Add ability to hold, pause and resume PID controllers
  - Add ability to modify PID controller parameters while active, held, or paused
  - New method of processing data on live graphs that is more accurate and reduced bandwidth
  - Install numpy binary from apt instead of compiling with pip

### Features

  - Add ability to set the language of the web user interface ([#167](https://github.com/kizniche/mycodo/issues/167))
  - Add Spanish language translation
  - New upgrade system to perform upgrades from github releases instead of commits
  - Allow symbols to be used in a user password ([#76](https://github.com/kizniche/mycodo/issues/76))
  - Introduce changelog (CHANGELOG.md)

### Bugfixes

  - Fix inability to update long-duration relay times on live graphs
  - Fix dew point being incorrectly inserted into the database
  - Fix inability to start video stream ([#155](https://github.com/kizniche/mycodo/issues/155))
  - Fix SHT1x7x sensor module not returning values ([#159](https://github.com/kizniche/mycodo/issues/159))

### Miscellaneous

  - Add more software tests
  - Update Flask to v0.12
  - Update InfluxDB to v1.1.1
  - Update factory_boy to v2.8.1
  - Update sht_sensor to v16.12.1
  - Move install files to Mycodo/install


## 4.0.26 (2016-11-23)

### Features

  - Add more I2C LCD address options (again)
  - Add Fahrenheit conversion for temperatures on /live page
  - Add github issue template ([#150](https://github.com/kizniche/mycodo/issues/150) [#151](https://github.com/kizniche/Mycodo/pull/151))
  - Add information to the README about performing manual backup/restore
  - Add universal sensor tests

### Bugfixes

  - Fix code warnings and errors
  - Add exceptions, logging, and docstrings


## 4.0.25 (2016-11-13)

### Features

  - New create admin user page if no admin user exists
  - Add support for [Chirp soil moisture sensor](https://wemakethings.net/chirp/)
  - Add more I2C LCD address options
  - Add endpoint tests
  - Add use of [Travis CI](https://travis-ci.org/) and [Codacy](https://www.codacy.com/)

### Bugfixes

  - Fix controller crash when using a 20x4 LCD ([#136](https://github.com/kizniche/mycodo/issues/136))
  - Add short sleep() to login to reduce chance of brute-force success
  - Fix code warnings and errors


## 4.0.24 (2016-10-26)

### Features

  - Setup flask app using new create_app() factory
  - Create application factory and moved view implementation into a general blueprint ([#129](https://github.com/kizniche/mycodo/issues/129) [#132](https://github.com/kizniche/Mycodo/pull/132) [#142](https://github.com/kizniche/Mycodo/pull/142))
  - Add initial fixture tests


## 4.0.23 (2016-10-18)

### Performance

  - Improve time-lapse capture method

### Features

  - Add BME280 sensor
  - Create basic tests for flask app ([#112](https://github.com/kizniche/mycodo/issues/122))
  - Relocated Flask UI into its own package ([#116](https://github.com/kizniche/Mycodo/pull/116))
  - Add DB session fixtures; create model factories
  - Add logging of relay durations that are turned on and off, without a known duration
  - Add ability to define power billing cycle day, AC voltage, cost per kWh, and currency unit for relay usage statistics
  - Add more Themes
  - Add hostname to UI page title

### Bugfixes

  - Fix relay conditionals when relays turn on for durations of time ([#123](https://github.com/kizniche/mycodo/issues/123))
  - Exclude photo/video directories from being backed up during upgrade
  - Removed unused imports
  - Changed print statements to logging statements
  - Fix inability to save sensor settings ([#120](https://github.com/kizniche/mycodo/issues/120) [#134](https://github.com/kizniche/mycodo/issues/134))
