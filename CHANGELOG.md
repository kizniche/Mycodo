## 5.0.0 (Unreleased)

### Features

  - Add auto-generation of relay usage/cost reports on a daily, weekly, or monthly schedule
  - Add ability to check daemon health (mycodo_client.py --checkdaemon)
  - Add sensor conditional actions: Activate/Deactivate PID, Email Photo, Email Video
  - Add PID option: maximum allowable sensor measurement age (to allow the PID controller from manipulate relays, the sensor measurement must have occurred in the past x seconds)
  - Add PID option: minimum off duration for lower/raise relay (protects devices that require a minimum off period by preventing power cycling from occurring too quickly)
  - Add new sensor: Free Disk Space (of a set path)
  - Add ability to use multiple camera configurations (multiple cameras)
  - Add OpenCV camera library to allow use of USB cameras ([#193](https://github.com/kizniche/mycodo/issues/193))
  - Automatically detect DS18B20 sensors in sensor configuration
  - Add ability to create custom user roles
  - Add new user roles: Editor and Monitor ([#46](https://github.com/kizniche/mycodo/issues/46))

### Miscellaneous

  - Refactor the relay/sensor conditional management system
  - User names are no longer case-sensitive
  - Switch to using Flask-Login
  - Switch to using flask_wtf.FlaskForm (from using deprecated flask_wtf.Form)
  - Update web interface style and layout
  - Update Flask WTF to 0.14.2
  - Move from using sqlalchemy to flask sqlalchemy
  - Restructure database ([#115](https://github.com/kizniche/mycodo/issues/115), [#122](https://github.com/kizniche/mycodo/issues/122))

## 4.1.17 (Unreleased)

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
