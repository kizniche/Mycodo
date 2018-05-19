## 6.1.1 (Unreleased)

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
