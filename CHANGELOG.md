## 4.1.0 (Unreleased)

This release introduces a new method for upgrading Mycodo to the latest version. Upgrades will now be performed from github releases instead of commits.

Performance:

  - Reduced bandwidth usage and processing of new data on live graphs
  - Update to InfluxDB 1.1.0

Features:

  - New upgrade system to perform upgrades from github releases
  - Introduce changelog (CHANGELOG.md)

Bugfixes:

  - Fix inability to update long-duration relay times on live graphs
  - Fix dew point being incorrectly inserted into the database
  - Fix inability to start video stream ([#155](https://github.com/kizniche/mycodo/issues/155))
  - Fix SHT1x7x sensor module not returning values ([#159](https://github.com/kizniche/mycodo/issues/159))

## 4.0.26 (2016-11-23)

Features:

  - Add more I2C LCD address options (again)
  - Add Fahrenheit conversion for temperatures on /live page
  - Add github issue template ([#150](https://github.com/kizniche/mycodo/issues/150) [#151](https://github.com/kizniche/Mycodo/pull/151))
  - Add information to the README about performing manual backup/restore
  - Add universal sensor tests

Bugfixes:

  - Fix code warnings and errors
  - Add exceptions, logging, and docstrings

## 4.0.25 (2016-11-13)

Features:

  - New create admin user page if no admin user exists
  - Add Chirp soil moisture sensor (https://wemakethings.net/chirp/)
  - Add more I2C LCD address options
  - Add endpoint tests
  - Add use of Travis CI and Codacy

Bugfixes:

  - Fix controller crash when using a 20x4 LCD (fixes [#136](https://github.com/kizniche/mycodo/issues/136))
  - Add short sleep() to login to reduce chance of brute-force success
  - Fix code warnings and errors

## 4.0.24 (2016-10-26)

Features:

  - Setup flask app using new create_app() factory
  - Create application factory and moved view implementation into a general blueprint ([#129](https://github.com/kizniche/mycodo/issues/129) [#132](https://github.com/kizniche/Mycodo/pull/132) [#142](https://github.com/kizniche/Mycodo/pull/142))
  - Add initial fixture tests

## 4.0.23 (2016-10-18)

Performance:

  - Improve time-lapse capture method

Features:

  - Add BME280 sensor
  - Create basic tests for flask app (fixes [#112](https://github.com/kizniche/mycodo/issues/122))
  - Relocated Flask UI into its own package [#116](https://github.com/kizniche/Mycodo/pull/116)
  - Add DB session fixtures; create model factories
  - Add logging of relay durations that are turned on and off, without a known duration
  - Add ability to define power billing cycle day, AC voltage, cost per kWh, and currency unit for relay usage statistics
  - Add more Themes
  - Add hostname to UI page title

Bugfixes:

  - Fix relay conditionals when relays turn on for durations of time (fixes [#123](https://github.com/kizniche/mycodo/issues/123))
  - Exclude photo/video directories from being backed up during upgrade
  - Removed unused imports
  - Changed print statements to logging statements
  - Fix inability to save sensor settings (fixes [#120](https://github.com/kizniche/mycodo/issues/120) [#134](https://github.com/kizniche/mycodo/issues/134))
