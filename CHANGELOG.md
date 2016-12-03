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
  - Fix inability to start video stream (#155)
  - Fix SHT1x7x sensor module not returning values (#159)

## 4.0.26 (2016-11-23)

Features:

  - Add more I2C LCD address options (again)
  - Add Fahrenheit conversion for temperatures on /live page
  - Add github issue template (#150)
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

  - Fix controller crash when using a 20x4 LCD (fixes #136)
  - Add short sleep() to login to reduce chance of brute-force success
  - Fix code warnings and errors

## 4.0.24 (2016-10-26)

Features:

  - Setup flask app using new create_app() factory
  - Create application factory and moved view implementation into a general blueprint (fixes #129)
  - Update to use new flask application factory. Added support fixtures
  - Add initial fixture tests

## 4.0.23 (2016-10-18)

Performance:

  - Improve time-lapse capture method

Features:

  - Add BME280 sensor
  - Create basic tests for flask app (fixes #112)
  - Relocated Flask UI into its own package
  - Add DB session fixtures; create model factories
  - Add logging of relay durations that are turned on and off, without a known duration
  - Add ability to define power billing cycle day, AC voltage, cost per kWh, and currency unit for relay usage statistics
  - Add more Themes
  - Add hostname to UI page title

Bugfixes:

  - Fix relay conditionals when relays turn on for durations of time (fixes #123)
  - Exclude photo/video directories from being backed up during upgrade
  - Removed unused imports
  - Changed print statements to logging statements
  - Fix inability to save sensor settings (fixes #120 #134)
