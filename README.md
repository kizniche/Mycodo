# Mycodo 

## Environmental Regulation System

### Latest version: 4.1.13 [![Build Status](https://travis-ci.org/kizniche/Mycodo.svg?branch=master)](https://travis-ci.org/kizniche/Mycodo) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/5b9c21d5680f4f7fb87df1cf32f71e80)](https://www.codacy.com/app/Mycodo/Mycodo?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kizniche/Mycodo&amp;utm_campaign=Badge_Grade)

Mycodo is a remote monitoring and automated regulation system with a focus on modulating environmental conditions. It was built to run on the Raspberry Pi (versions Zero, 1, 2, and 3) and aims to be easy to install and set up.

The core system coordinates a diverse set of responses to sensor measurements, including actions such as camera captures, email notifications, relay activation/deactivation, regulation with PID control, and more. Mycodo has been used for cultivating gourmet mushrooms, cultivating plants, culturing microorganisms, maintaining honey bee apiary homeostasis, incubating snake eggs and young animals, aging cheeses, fermenting foods, maintaining aquatic systems, and more.



## What is PID Control?

[![Mycodo](http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png)](http://kylegabriel.com/projects/)

A [proportional-derivative-integral (PID) controller](https://en.wikipedia.org/wiki/PID_controller) is a control loop feedback mechanism used throughout industry for controlling systems. It efficiently brings a measurable condition, such as the temperature, to a desired state and maintains it there with little overshoot and oscillation. A well-tuned PID controller will raise to the setpoint quickly, have minimal overshoot, and maintain the setpoint with little oscillation.

In the top graph of the above screenshot visualizes the regulation of temperature in a sealed chamber. The red line is the desired temperature setpoint that has been configured (which also happens to have been configured to change over the course of each day). The blue line is the actual recorded temperature. The green vertical bars represent how long a heater is activated for, per every 20-second period. This regulation was achieved with minimal tuning (Actual tuned gains: K<sub>P</sub>=0.08, K<sub>I</sub>=0.005, K<sub>D</sub>=0.001), and already displays a very minimal deviation from the setpoint (±0.5° Celsius). Further tuning would reduce this variability even more.



## Table of Contents

- [Features](#features)
- [TODO](#todo)
- [Install](#install)
- [Install Notes](#install-notes)
- [Supported Devices and Sensors](#supported-devices-and-sensors)
    - [1-Wire](#1-wire)
    - [GPIO](#gpio)
    - [UART](#uart)
    - [I<sub>2</sub>C](#i2c)
    - [Devices](#devices)
- [Notes](#notes)
- [HTTP Server](#http-server-security)
- [Daemon Info](#daemon-info)
- [Upgrading](#upgrading)
- [Backup and Restore](#backup-and-restore)
- [Translations](#translations)
- [Directory Structure](#directory-structure)
- [License](#license)
- [Screenshots](#screenshots)
- [Links](#links)



## Features

* Web interface: Visualize data, configure the system, manipulate relays, and more, from anywhere with an internet connection.
* Many Analog and digital sensors supported: Measuring temperature, humidity, CO<sub>2</sub>, atmospheric pressure, luminosity, infrared heat, soil moisture, and more!
  * Analog to digital converter support for reading any analog sensor or signal.
* Event triggers: When certain conditions are met, activate relays, camera recording, email notification, and more.
* Discrete PID control: Regulate environmental conditions with prediction and precision.
* Method creation for dynamic PID setpoints for changing conditions over time (setpoint tracking).
  * Time/Date: Change the setpoint based on specific times and dates (ideal for long-duration changes).
  * Duration: Change the setpoint at durations form when it was activated (examples: reflow oven, thermal cycler).
  * Daily: Change the setpoint on a daily, repeatable schedule.
  * Daily Sine Wave: Change the setpoint on a daily, repeatable schedule that follows a configurable sinusoidal wave.
  * Daily Bezier Curve: Change the setpoint on a daily, repeatable schedule that follows a configurable Bezier curve.
* 16x2 and 20x4 I<sup>2</sup>C LCD support: Create a physical display of conditions or status of the system.
* I<sup>2</sup>C multiplexer support to allow using multiple devices/sensors with the same I<sup>2</sup>C address.
* Pi Camera support: Stream live video, capture still images, or create time-lapses.
* Automated system upgrade: When there's new release on github, an upgrade can be initiated from the web UI.
* Languages: English and Spanish.



## TODO:

* Support Serial Port Expander
* Support more Atlas Scientific sensors
* Add PID filters (of input or output) and alternate PID functions.
* Add support for wireless communication (z-wave, xbee, or other).
* Support for PWM and servo/stepper motors
* Continue development of Remote Admin Dashboard to monitor other Mycodo servers
* Add graph export options (width, height, scale)
* Create custom log from influxdb query
* Notes, flag points of time on graph (text, file upload, graph saving, etc.).



## Install

These install procedures have been tested to work with a Raspberry Pi following a fresh install of [Raspbian Jessie](https://www.raspberrypi.org/downloads/raspbian/) (Full or Lite version), with an active internet connection.

It appears that with the current version of Raspbian, SSH is not enabled by default. This necessitates the use of a keyboard and monitor to run raspi-config and enable SSH.

Set up the initial settings with raspi-config. **It's very important that you don't skip the file system expansion and reboot! This needs to be done before continuing or there won't be any free disk space.**

```sudo raspi-config```

 + Expand File system (required)**
 + Change User Password
 + Internationalisation Options -> Change Locale (set and select en_US.UTF-8 if US)
 + Internationalisation Options -> Change Timezone
 + Enable Camera
 + Advanced Options -> Enable SSH
 + Advanced Options -> Enable I<sup>2</sup>C (required if using certain sensors)
 + **Reboot (required)**


Mycodo will be installed by executing setup.sh. As a part of the installation, it will install and modify the default apache2 configuration to host the Mycodo web UI. If you require a custom setup, examine and modify this script accordingly. If you do not require a custom setup, just run the install script with the following commands:

```
sudo apt-get install jq
cd ~
curl -s https://api.github.com/repos/kizniche/Mycodo/releases/latest | \
jq -r '.tarball_url' | wget -i - -O mycodo-latest.tar.gz
mkdir Mycodo
tar xzf mycodo-latest.tar.gz -C Mycodo --strip-components=1
rm -f mycodo-latest.tar.gz
cd Mycodo/install
sudo /bin/bash ./setup.sh
```

Make sure the setup.sh script finishes without errors. A log of the setup.sh script output will be created at ~/Mycodo/install/setup.log.

If the install is successful, the web user interface should be accessible with your PI's IP address https://IPaddress/. The first time you visit this page, you will be prompted to create an admin user. After creating an admin user, you should be redirected to the login page to use the credentials just created to log in. Once logged in, make sure the host name and version number at the top left is green, indicating the daemon is running. Red indicates the daemon is inactive or unresponsive. Ensure any java-blocking plugins are disabled for all the web UI features to work.

Alternatively, an admin user may also be created with the following command:

```sudo ~/Mycodo/init_databases.py --addadmin```



## Install Notes

If you want write access to the mycodo files, add your user to the mycodo group, changing 'username' to your user.

```sudo usermod -a -G mycodo username```

In certain circumstances after the initial install, the mycodo service will not be able to start because of a missing or corrupt package. I'm still trying to understand why this happens and how to prevent it. If you cannot start the daemon, try to reinstall the required python modules with the following command:

```sudo pip install -r ~/Mycodo/install/requirements.txt --upgrade --force-reinstall --no-deps```

Then reboot

```sudo shutdown now -r```

If you receive an unresolvable error during the install, please [create an issue](https://github.com/kizniche/Mycodo/issues).



## Supported Devices and Sensors

Certain sensors will require extra steps to be taken in order to set up the interface for communication. This includes I<sup>2</sup>C, one-wire, and UART.

### 1-Wire

The 1-wire interface should be configured with [these instructions](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing).

> [DS18B20](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf), [DS18S20](https://datasheets.maximintegrated.com/en/ds/DS18S20.pdf), [DS1822](https://datasheets.maximintegrated.com/en/ds/DS1822.pdf), [DS28EA00](https://datasheets.maximintegrated.com/en/ds/DS28EA00.pdf), [DS1825](https://datasheets.maximintegrated.com/en/ds/DS1825.pdf)/[MAX31850K](https://datasheets.maximintegrated.com/en/ds/MAX31850-MAX31851.pdf) Temperature

### GPIO

> [DHT11, DHT22, AM2302](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/wiring) Relative humidity and temperature.

> [SHT1x, SHT2x, SHT7x](https://github.com/mk-fg/sht-sensor) Relative humidity and temperature.

### UART

> [K30](http://www.co2meter.com/products/k-30-co2-sensor-module) Carbon dioxide (CO<sub>2</sub>) in ppmv

[This documentation](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zip) provides specific installation procedures for the K30 with the Raspberry Pi version 1 or 2. Once the K30 has been configured with this documentation, it can be tested whether the sensor is able to be read, by executing ~/Mycodo/mycodo/tests/test_uart_K30.py

Because the UART is handled differently by the Raspberry Pi 3, from of the addition of bluetooth, there are a different set of instructions for getting the K30 working on the Raspberry Pi 3. If installing on a Raspberry Pi 3, you only need to perform these steps to get the K30 working:

Run raspi-config

```sudo raspi-config```

Go to Advanced Options->Serial and disable. Then edit /boot/config.txt

```sudo vi /boot/config.txt```

Find the line "enable_uart=0" and change it to "enable_uart=1", then reboot.

### I<sup>2</sup>C

The I<sup>2</sup>C interface should be enabled with `raspi-config`.

> [AM2315](https://github.com/lexruee/tentacle_pi) Relative humidity and temperature.

> [Atlas Scientific PT-1000](http://www.atlas-scientific.com/product_pages/kits/temp_kit.html) Temperature

> [BME280](https://www.bosch-sensortec.com/bst/products/all_products/bme280) Barometric pressure, humidity, and temperature

> [BMP085, BMP180](https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi) Barometric pressure and temperature

> [HTU21D](http://www.te.com/usa-en/product-CAT-HSC0004.html) Relative humidity and temperature

> [TMP006, TMP007](https://www.sparkfun.com/products/11859) Contactless temperature

> [TSL2561](https://www.sparkfun.com/products/12055) Light

> [Chirp](https://wemakethings.net/chirp/) Moisture, light, and temperature

### Edge Detection

The detection of a changing signal, for instance a simple switch completing a circuit, requires the use of edge detection. By detecting a rising edge (LOW to HIGH), a falling edge (HIGH to LOW), or both, actions or events can be triggered. The GPIO chosen to detect the signal should be equipped with an appropriate resistor that either pulls the GPIO up [to 5-volts] or down [to ground]. The option to enable the internal pull-up or pull-down resistors is not available for safety reasons. Use your own resistor to pull the GPIO high or low.

Examples of devices that can be used with edge detection: simple switches and buttons, PIR motion sensors, reed switches, hall effect sensors, float switches, and more.


### Devices

### I<sup>2</sup>C Multiplexers

All devices that connected to the Raspberry Pi by the I<sup>2</sup>C bus need to have a unique address in order to communicate. Some sensors may have the same address (such as the AM2315), which prevents more than one from being connected at the same time. Others may provide the ability to change the address, however the address range may be limited, which limits by how many you can use at the same time. I<sup>2</sup>C multiplexers are extremely clever and useful in these scenarios because they allow multiple sensors with the same I<sup>2</sup>C address to be connected.

> [TCA9548A I<sup>2</sup>C Multiplexer](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/overview) (I<sup>2</sup>C): Has 8 selectable addresses, so 8 multiplexers can be connected to one Raspberry Pi. Each multiplexer has 8 channels, allowing up to 8 devices/sensors with the same address to be connected to each multiplexer. 8 multiplexers x 8 channels = 64 devices/sensors with the same I<sup>2</sup>C address.

> [TCA9545A Grove I<sup>2</sup>C Bus Multiplexer](http://store.switchdoc.com/i2c-4-channel-mux-extender-expander-board-grove-pin-headers-for-arduino-and-raspberry-pi/) (I<sup>2</sup>C): This board works a little differently than the TCA9548A, ablove. This board actually creates 4 new I<sup>2</sup>C busses, each with their own selectable voltage, either 3.3 or 5.0 volts. Instructions to enable the Device Tree Overlay are at [https://github.com/camrex/i2c-mux-pca9545a](https://github.com/camrex/i2c-mux-pca9545a). Nothing else needs to be done in Mycodo after that except to select the correct I<sup>2</sup>C bus when configuring the sensor.

### Analog to Digital Converters

An analog to digital converter (ADC) allows the use of any analog sensor that outputs a variable voltage. A [voltage divider](https://learn.sparkfun.com/tutorials/voltage-dividers) may be necessary to attain your desired range.

> [ADS1x15 Analog to Digital Converters](https://www.adafruit.com/product/1085) &plusmn;4.096 (I<sup>2</sup>C)

> [MCP342x Analog to Digital Converters](http://www.dfrobot.com/wiki/index.php/MCP3424_18-Bit_ADC-4_Channel_with_Programmable_Gain_Amplifier_(SKU:DFR0316)) &plusmn;2.048 (I<sup>2</sup>C)



## Notes

A minimal set of anonymous usage statistics are collected to help improve development. No identifying information is saved from the information that is collected and it is only used to improve Mycodo. No other sources will have access to this information. The data collected is mainly how much specific features are used, how often errors occur, and other similar statistics. The data that's collected can be viewed from the 'View collected statistics' link in the Settings/General panel of the UI or in the file Mycodo/databases/statistics.csv. You may opt out from transmitting this information from the General settings in the Admin panel.

Mycodo/mycodo/scripts/mycodo_wrapper is a binary executable used to update the system from the web interface. It has the setuid bit to permit it to be executed as root ('sudo bash ~/Mycodo/mycodo/scripts/upgrade_mycodo_release.sh initialize' sets the correct permissions and setuid). Since shell scripts cannot be setuid (ony binary files), the mycodo_wrapper binary permits these operations to be executed as root by a non-root user (in this case, members of the group 'mycodo'). You can audit the source code of Mycodo/mycodo/scripts/mycodo_wrapper.c and if you want to ensure the binary is indeed compiled from that source, you may compile it yourself with the following command. Otherwise, the compiled binary is already included and no further action is needed.

```sudo gcc ~/Mycodo/mycodo/scripts/mycodo_wrapper.c -o ~/Mycodo/mycodo/scripts/mycodo_wrapper```


### HTTP Server Security

An SSL certificate will be generated and stored at ~/Mycodo/mycodo/mycodo_flask/ssl_certs/ during the install process. If you want to use your own SSL certificates, replace them with your own. [letsencrypt.org](https://letsencrypt.org) provides free verified SSL certificates if you have your own domain.

If using the auto-generated certificate from the install, be aware that it will not be verified when visiting the 'https://' version (opposed to 'http://')of the web UI. You may receive a warning message about the security of your site, unless you add the certificate to your browser's trusted list.


### Daemon info

The status of the daemon's service can be checked

```sudo service mycodo service```

The daemon can also be started manually if the systemd method above isn't used or an error needs to be debugged

```sudo ~/Mycodo/mycodo/mycodo_daemon.py```

Also, use '-d' to log all debug messages to /var/log/mycodo/mycodo.log

```sudo ~/Mycodo/mycodo/mycodo_daemon.py -d```

To terminate the daemon, you can use two methods. If the daemon was started with ```sudo service mycodo start```, please use ```sudo service mycodo stop``` to stop it. If the daemon was started from either of the two commands above, then the following command may be used to terminate the daemon:

```python ~/Mycodo/mycodo/mycodo_client.py -t```


### Upgrading

If you already have Mycodo installed (>=4.0.0), you can perform an upgrade to the latest [release](https://github.com/kizniche/Mycodo/releases) on github by either using the Admin/Upgrade menu in the web UI (recommended) or by issuing the following command at the terminal. A log of the upgrade process is created at /var/log/mycodo/mycodoupgrade.log

```sudo /bin/bash ~/Mycodo/mycodo/scripts/upgrade_mycodo_release.sh upgrade```

Upgrading the mycodo database is performed automatically during the upgrade process, however it can also be performed manually with the following commands (Note: This does not create the database, only upgrade them. You must already have a database created in order to upgrade):

```bash
cd ~/Mycodo/databases
alembic upgrade head
```

Refer to the [alembic documentation](http://alembic.readthedocs.org/en/latest/tutorial.html) for other functions.



### Backup and Restore

Currently only the Mycodo settings are backed up when the system is upgraded from the Admin/Upgrade menu of the web UI.

If you would like to create a full backup that includes all the sensor data, which can be used to set up Mycodo on a new system as it was on the old, you can follow these steps:

Backup the influx databases:

```bash
influxd backup <path-to-metastore-backup>
influxd backup -database mycodo_db <path-to-database-backup>
```
 
Backup the Mycodo databases:

```bash
cd ~/Mycodo/databases
tar zcf ~/Mycodo-databases.tar.gz users.db mycodo.db
```

Then, on the new system, assign the same IP as the old system (if using the remote admin).

Clone the latest Mycodo from github (ensure [prerequisites](#install-notes) are taken care of first):

```bash
cd ~
clone git clone https://github.com/kizniche/Mycodo
```

Extract the Mycodo databases back to Mycodo/databases:

```bash
tar zxvf ~/Mycodo-databases.tar.gz -C ~/Mycodo/databases
```

To ensure your databases are up-to-date and compatible with the latest version of Mycodo, run:

```bash
cd ~/Mycodo/databases
alembic upgrade head
```

Execute the Mycodo setup.sh script:

```bash
cd ~/Mycodo/install
sudo /bin/bash setup.sh
```

Restore the influx databases:

```bash
service influxdb stop
influxd restore -metadir /var/lib/influxdb/meta <path-to-metastore-backup>
influxd restore -datadir /var/lib/influxdb/data <path-to-database-backup>
sudo chown -R influxdb:influxdb /var/lib/influxdb
service influxdb start
```

The order of these events are important, because databases will be created and services started while the setup.sh script is running, so certain commands need to be done before this happens.

You could also copy the influx databases and just copy the entire Mycodo directory (archive to preserve permissions) to a new system, but I was writing from the perspective of backing up the most minimal set of data, so if a system became corrupt somewhere, the backups could be restored to a new system.



### Translations

Translation support has been added but there is currently a lack of translation languages. If you know another language and would like to create translations, follow the steps below.

To create your own translation, use the following commands.

```cd ~/Mycodo/mycodo```

Create a messages.pot file from searching all files that contain translatable text.

```pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .```

Create the translation for the new language (in this case it is 'es' for Spanish).

```pybabel init -i messages.pot -d mycodo_flask/translations -l es```

There will now be the file 'messages.po' created in ~/Mycodo/mycodo/mycodo_flask/translations/es/LC_MESSAGES/

Edit messages.po (I used [poedit](https://poedit.net/)) to edit and save the translation for each translatable word or phrase.

Finally, compile the new translation.

```pybabel compile -d mycodo_flask/translations```

If you would like to rescan for translatable text and update your language's messages.po file (or add translations to an already-created messages.po) without losing your previous translation work, use the following commands instead of the above commands. Then edit with poedit (or similar app) and compile for it to take effect.

```
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
pybabel update -i messages.pot -d mycodo_flask/translations
pybabel compile -d mycodo_flask/translations
```

The important file is ~/Mycodo/mycodo/mycodo_flask/translations/##/LC_MESSAGES/messages.po (with '##' representing the language code, e.g. 'es' for spanish, 'fr' for French) that should either be sent to me or added to a pull request. This is how the new translations can be incorporated into Mycodo.

Refer to [The Flask Mega-Tutorial, Part XIV: I18n and L10n](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n) for more details of this process.



### Directory Structure

This is the file structure of Mycodo, so it may assist anyone to understand or modify the system. I'll try to keep this current.

```
Mycodo/
├── CHANGELOG.md - Mycodo version changelog
├── databases - SQLite databases (for configuration)
│   ├── alembic - Alembic SQL database migration tool
│   │   └── versions - Scripts to upgrade/downgrade databases
│   │       ├── 04303bc223c4_create_dynamic_pid_setpoint_table.py
│   │       ├── px5pvbcdpw46_rename_table.py
│   │       └── ...
│   ├── mycodo.db - Mycodo settings
│   ├── notes.db
│   ├── statistics.csv - Anonymous statistics data
│   └── users.db - User settings
├── init_databases.py - Script to create SQLite databases and users
├── install
│   ├── crontab.sh - Ensures proper line is in crontab
│   ├── mycodo.service - Systemd script
│   ├── mycodo_flask_apache.conf - Apache2 configuration file
│   ├── requirements.txt - Python module requirements
│   └── setup.sh - Mycodo install script
├── mycodo
│   ├── config.py - Global configuration file
│   ├── controller_lcd.py - LCD controller class
│   ├── controller_log.py - Log controller class
│   ├── controller_pid.py - PID controller class
│   ├── controller_relay.py - Relay controller class
│   ├── controller_sensor.py - Sensor controller class
│   ├── controller_timer.py - Timer controller class
│   ├── daemonutils.py - Various functions to assist mycodo_daemon.py
│   ├── databases - SQL database manipulation framework (SQLAlchemy)
│   │   └── ...
│   ├── devices - Python modules for devices (such as I2C multiplexer)
│   │   ├── ads1x15.py
│   │   ├── camera_pi.py
│   │   └── ...
│   ├── flaskforms.py - Flask form classes
│   ├── flaskutils.py - Various functions to assist the flask UI
│   ├── mycodo_flask - HTTP server files (Flask)
│   │   ├── admin_routes.py - Admin page routes
│   │   ├── authentication_routes.py - Authentication routes
│   │   ├── general_routes.py - General routes
│   │   ├── method_routes.py - Method routes
│   │   ├── page_routes.py - General page routes
│   │   ├── settings_routes.py - Settings page routes
│   │   ├── ssl_certs - Location of HTTP SSL certificates
│   │   ├── static - Static files reside (images, css, js, etc.)
│   │   ├── templates - Flask HTML templates
│   │   │   ├── 404.html
│   │   │   ├── flash_messages.html - Error message handler
│   │   │   ├── layout.html - Template for pages/, settings/, /tools
│   │   │   ├── layout-remote.html - Template for /remote
│   │   │   ├── layout-settings.html - Template for /settings
│   │   │   ├── login.html - Login page
│   │   │   ├── manual.html - Mycodo usage manual
│   │   │   ├── admin - Flask admin pages
│   │   │   ├── pages - Flask general pages
│   │   │   │   ├── graph.html - Graph display age
│   │   │   │   ├── live.html - Live data display page
│   │   │   │   ├── sensor.html - Sensor configuration page
│   │   │   │   └── ...
│   │   │   ├── remote - Future remote administration panel
│   │   │   │   └── setup.html - Add or check the status of remote systems
│   │   │   ├── settings - Flask settings pages
│   │   │   │   ├── alerts.html - Alerts settings page
│   │   │   │   ├── users.html - Users settings page
│   │   │   │   └── ...
│   │   │   └── tools - Various tools for Mycodo
│   │   │       ├── info.html - Information about your system
│   │   │       ├── logview.html - Display log files
│   │   │       ├── usage.html - Calculate relay usage/power consumtion
│   │   │       └── ...
│   │   └── translations - Language translations
│   ├── mycodo_client.py - Communicates with the running daemon
│   ├── mycodo_daemon.py - Mycodo daemon (core of the system)
│   ├── start_flask_ui.py - Flask startup script
│   ├── scripts - Miscellaneous helper and test scripts and functions
│   │   ├── mycodo_wrapper.c - Source to binary that's setuid, for upgrades 
│   │   ├── restore_mycodo.sh - Script to restore a backed-up Mycodo version
│   │   ├── upgrade_mycodo_release.sh - Updates Mycodo to the latest release
│   │   ├── update_post.sh - Post update commands (from the latest release)
│   │   └── ...
│   ├── sensors - Python modules for sensors
│   │   ├── am2315.py
│   │   ├── bmp.py
│   │   ├── dht11.py
│   │   └── ...
│   └── tests - Software and Hardware Tests 
│       ├── manual_tests - Scripts to test various sensors or devices
│       │   ├── Test_I2C_LCD.py
│       │   ├── Test_I2C_MCP342x.py
│       │   ├── Test_I2C_Multiplexer.py
│       │   └──...
│       └── software_tests - Automated Tests for Software
├── mycodo_flask.wsgi - Start script for Apache2 mod_wsgi
├── old - Archived milestone versions of Mycodo
└──
```


### License

Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](http://www.gnu.org/licenses/gpl-3.0.en.html) for more details.

A full copy of the GNU General Public License can be found at <a href="http://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank">http://www.gnu.org/licenses/gpl-3.0.en.html</a>

This software includes third party open source software components: Discrete PID Controller. Each of these software components have their own license. Please see Mycodo/mycodo/controller_PID.py for license information.


### Screenshots (may be outdated)

See the status of all sensors on one page

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Status-2016-04-10-10-53-58.png">

---

Create custom live graphs

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Graph-2016-04-14-18-29-24.png">

---

Add sensors

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Sensors-2016-04-10-10-52-36.png">

---

Configure and manipulate relays

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Relays-2016-04-10-10-52-57.png">

---

Create PID controllers

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-PID-2016-04-10-10-53-11.png">

---

Output to LCDs

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-LCD-2016-04-10-10-53-38.png">

---

Change settings

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Alerts-Settings-2016-04-10-11-50-29-e1460303466599.png">



## Links

Thanks for using and supporting Mycodo, however it may not be the latest version or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

https://github.com/kizniche/Mycodo

http://KyleGabriel.com
