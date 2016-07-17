# Mycodo

## An Environmental Monitoring and Regulation System

### Latest version: 4.0.5 ([Install Instructions](#installation))

Mycodo is a remote monitoring and automation system with a focus on regulating environmental conditions. The system focuses on enabling a diverse set of responses to sensor measurements. Responses can be many things (and is expanding all the time), a camera capture, an email notification, a relay activation/deactivation, or regulation with PID control. Mycodo has been used for cultivating gourmet mushrooms, maintaining homeostasis in a honey bee apiary, incubating eggs, aging cheeses, and.

The system is built to run on the Raspberry Pi and aims to be easy to install and set up.

[![Mycodo](http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png)](http://kylegabriel.com/projects/)


## Table of Contents

- [Features](#features)
- [TODO](#todo)
- [Install](#install)
- [Install Notes](#install-notes)
- [Supported Devices and Sensors](#supported-devices-and-sensors)
    - [Temperature](#temperature)
    - [Humidity](#humidity)
    - [CO<sub>2</sub>](#co2)
    - [Pressure](#pressure)
    - [Luminosity](#luminosity)
    - [Devices](#devices)
- [Notes](#notes)
- [HTTP Server](#http-server-security)
- [Daemon Info](#daemon-info)
- [Upgrading](#upgrading)
- [Restoring Backups](#restoring-backups)
- [License](#license)
- [Screenshots](#screenshots)
- [Links](#links)


## Features

* Web interface for visualizing data, configuring the system, and manipulating relays.
* Automated sensor reading and writing to a round-robin database for central access to data.
* Analog to digital converter support for reading any analog sensor.
* Support for several digital sensors for measuring temperature, humidity, CO<sub>2</sub>, atmospheric pressure, luminosity, and infrared heat).
* Event triggers (relay, camera, email, etc.) when certain sensor measurements occur or conditions are met.
* Regulate environmental conditions with discrete PID control.
* Dynamic PID setpoints for changing environmental conditions throughout the day.
* 16x2 and 20x4 I<sup>2</sup>C LCD support.
* I<sup>2</sup>C multiplexer support to allow using multiple devices/sensors with the same address.
* Pi Camera support.
* Automated system upgrade.


## TODO:

* Add support for wireless communication (z-wave, xbee, or other).
* Add ability to build and run rate-change methods (reflow oven, thermal cycler for PCR, etc.).
* Support for PWM and servo/stepper motors
* Dashboard to monitor other Mycodo servers
* Add graph export options (width, height, scale)
* Add stepper motor support
* Create custom log from influxdb query
* Notes, flag points of time on graph (text, file upload, graph saving, etc.).


## Install

These install procedures have been tested to work with a Raspberry Pi following a fresh intall of [Raspbian Jessie Lite](https://www.raspberrypi.org/downloads/raspbian/), with an active internet connection. Note: Only the Lite version has been confirmed to work.

Set up the initial settings with raspi-config. **Don't skip the file system expansion and reboot! This needs to be done before continuing to install anything or there won't be any free disk space.**

```sudo raspi-config```

 + Change the default user (pi) password
 + Set the locale to en_US.UTF-8
 + Set the time zone (required for setting the proper time)
 + Enable I<sup>2</sup>C (required)
 + Enable Pi Camera support (optional)
 + Advanced A2: change the hostname (optional)
 + **Expand the file system (required)**
 + **Reboot**


Mycodo will be installed with the following install script (setup.sh). As a part of the instllation, it will install and modify the default apache2 configuration to host the Mycodo web UI. If you require a custom setup, examine and modify this script accordingly. If you do not require a custom setup, just run the install script with the following commands.

```
sudo apt-get update && sudo apt-get install -y git
cd
git clone https://github.com/kizniche/Mycodo
cd Mycodo
sudo ./setup.sh
```

Create an administrator user for the web UI:

```sudo ./init_databases.py -A```

Make sure the setup.sh and init_databases.py scripts run without error. A log of the setup.sh script output will be created at ~/Mycodo/setup.log.

Follow the on-screen prompts to create an administrator user for the web interface and then reboot.

```sudo shudown now -r```

That's it. After the reboot, you should be able to log into the Mycodo web UI at https://localhost/ (note the 's' in https) with the user you just created. Make sure the Mycodo logo and version number at the top left is the color green, indicating the daemon is running.


## Install Notes

If you want write access to the mycodo files, add your user to the mycodo group, changing 'username' to your user.

```sudo usermod -a -G mycodo username```

In certain circumstances after the initial install, the mycodo service will not be able to start because of a missing or corrupt package. I'm still trying to understand why this happens and how to prevent it. If you cannot start the daemon, try to resinstall the required modules with the following command:

```sudo pip install -r ~/Mycodo/requirements.txt --upgrade --force-reinstall --no-deps```

Then reboot

```sudo shutdown now -r```

If you receive an unresolvable error during the install, please [create an issue](https://github.com/kizniche/Mycodo/issues).


## PID Controller

A [proportional-derivative-integral (PID) controller](https://en.wikipedia.org/wiki/PID_controller) is a control loop feedback mechanism used throughout industry for controlling systems. It efficiently brings a measurable condition, such as the temperature, to a desired state and maintains it there with little overshoot and oscillation. A well-tuned PID controller will raise to the setpoint quickly, have minimal overshoot, and maintain the setpoint with little oscillation.


## Supported Devices and Sensors

Certain sensors will require extra steps to be taken in order to set up the interface for communication. This includes I<sup>2</sup>C, one-wire, and UART.

### Temperature

> [DS18B20](https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf) (1-wire): Once the one-wire interface has been configured with [these instructions](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing), it may be used with Mycodo.

> [TMP006, TMP007](https://www.sparkfun.com/products/11859) (I<sup>2</sup>C): Can measure the temperature of an object without making contact with it, by using a thermopile to detect and absorb the infrared energy an object is emitting. This sensor also measures the temperature of the die (physical sensor).

### Humidity

> [DHT11, DHT22, AM2302](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/wiring) (GPIO): Measures relative humidity and temperature.

> [AM2315](https://github.com/lexruee/tentacle_pi) (I<sup>2</sup>C): Measures relative humidity and temperature.

> [SHT10, SHT11, SHT15, SHT71, SHT75](https://github.com/mk-fg/sht-sensor) (GPIO): Measures relative humidity and temperature.

### Carbon Dioxide (CO<sub>2</sub>)

> [K30](http://www.co2meter.com/products/k-30-co2-sensor-module) (UART): [This documentation](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zip) provides specific installation procedures for the K30 with the Raspberry Pi version 1 or 2, as well as example code. Once the K30 has been configured with this documentation, it can be tested whether the sensor is able to be read, by executing mycodo/tests/Test-Sensor-CO2-K30.py

Because the UART is handled differently by the Raspberry Pi 3, from of the addition of bluetooth, there are a different set of instructions for getting the K30 working on the Raspberry Pi 3. If installing on a Raspberry Pi 3, you only need to perform these steps to get the K30 working:

Run raspi-config, go to Advanced Options->Serial and disable.

```sudo raspi-config```

Then edit /boot/config.txt

```sudo vi /boot/config.txt```

Find the line "enable_uart=0" and change it to "enable_uart=1", then reboot.

### Pressure

> [BMP085/BMP180](https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi) (I<sup>2</sup>C)

### Luminosity

> [TSL2561](https://www.sparkfun.com/products/12055) (I<sup>2</sup>C): A light sensor with a flat response across most of the visible spectrum. It measures both infrared and visible light to better approximate the response of the human eye. Because it's an integrating sensor (it soaks up light for a predetermined amount of time), it is capable of measuring both small and large amounts of light by changing the integration time. Conducts specific light ranges from 0.1 - 40k+ Lux and contains two integrating analog-to-digital converters (ADC) that integrate currents from two photodiodes, simultaneously.

### Edge Detection

The detection of a changing signal, for instance, 5-volts (HIGH) to 0-volts (LOW), requires the use of edge detection. By detecting a rising edge (LOW to HIGH), a falling edge (HIGH to LOW), or both, we can trigger actions or events. The GPIO chosen to detect the signal should be equipped with an appropriate resistor that either pulls the GPIO up (connected to 5-volts) or down (connected to ground). The option to enable the internal pull-up or pull-down resistors is not available for safety reasons. Use your own resistor to pull the GPIO high or low.

Examples of devices that can be used with edge detection: simple switches and buttons, PIR motion sensors, reed switches, hall effect sensors, float switches, and more.


### Devices

## I<sup>2</sup>C Multiplexers

All devices that connected to the Raspberry Pi by the I<sup>2</sup>C bus need to have a unique address in order to communicate. Some sensors may have the same address (such as the AM2315), which prevents both from being connected at the same time. Others may provide the ability to change the address, however the address range may be limited, so you will be limited by how many sensors you can use at ine time. I<sup>2</sup>C multiplexers are extremely clever and useful in these scenarios because they allow multiple sensors with the same I<sup>2</sup>C address to be connected.

> [TCA9548A I2C Multiplexer](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/overview) (I<sup>2</sup>C): Has 8 selectable address, so 8 multiplexers can be connected to one Raspberry Pi. Each multiplexer has 8 channels, allowing up to 8 devices/sensors with the same address to be connected to each. 8 multiplexers x 8 channels = 64 devices/sensors with the same address.

## Analog to Digital Converters

An analog to digital converter (ADC) allows the use of any analog sensor that outputs a variable voltage. The detectable voltage range of this ADC is &plusmn;2.048 volts. A [voltage divider](https://learn.sparkfun.com/tutorials/voltage-dividers) may be necessary to attain this range.

> [ADS1x15 Analog to Digital Converters](https://www.adafruit.com/product/1085) (I<sup>2</sup>C)

> [MCP243x Analog to Digital Converters](http://www.dfrobot.com/wiki/index.php/MCP3424_18-Bit_ADC-4_Channel_with_Programmable_Gain_Amplifier_(SKU:DFR0316)) (I<sup>2</sup>C)



## Notes

A minimal set of anonymous usage statistics are collected to help improve development. No identifying information is saved from the information that is collected and it is only used to improve Mycodo. No other sources will have access to this information. The data collected is mainly how much specific features are used, how often errors occur, and other similar statistics. The data that's collected can be viewed from the 'View collected statistics' link in the Settings/General panel of the UI or in the file Mycodo/databases/statistics.csv. You may opt out from transmitting this information from the General settings in the Admin panel.

Mycodo/mycodo/scripts/mycodo_wrapper is a binary executable used to update the system from the web interface. It has the setuid bit to permit it to be executed as root ('sudo update_mycodo.sh initialize' sets the correct permissions and setuid). Since shell scripts cannot be setuid (ony binary files), the mycodo_wrapper binay permits these operations to be executed as root by a non-root user (in this case, members of the group 'mycodo'). You can audit the source code of Mycodo/mycodo/scripts/mycodo_wrapper.c and if you want to ensure the binary is indeed compiled from that source, you may compile it yourself with the following command. Otherwise, the compiled binary is already included and no further action is needed.

```sudo gcc ~/Mycodo/mycodo/scripts/mycodo_wrapper.c -o ~/Mycodo/mycodo/scripts/mycodo_wrapper```


### HTTP Server Security

SSL certificates will be generated and stored at ~/Mycodo/mycodo/frontend/ssl_certs/ during the install process. If you want to use your own SSL certificates, replace them as they are named in this directory. [letsencrypt.org](https://letsencrypt.org) provides free verified SSL certificates.

If using the auto-generated certificate, be aware that they will not be verified when visiting the https:// version of the WEB UI. You will receive warning messages about the security of your site unless you add the certificate to your browser's trusted list). 


### Daemon info

The status of the daemon's service can be checked

```sudo service mycodo service```

The daemon can also be started manually if the systemd method above isn't used or an error needs to be debugged

```sudo ~/Mycodo/mycodo/mycodo_daemon.py```

Also, use '-d' to log all debug messages to /var/log/mycodo/mycodo.log

```sudo ~/Mycodo/mycodo/mycodo_daemon.py -d```


### Upgrading

If you already have Mycodo installed (>=4.0.0), you can perform an upgrade to the latest version on github by either using the Admin/Update menu in the web UI (recommended) or by issuing the following command at the terminal. Note: You must be a member of the group 'mycodo', else you will have to execute the following command as root. A log of the update process can be found at /var/log/mycodo/mycodoupdate.log

```~/Mycodo/mycodo/scripts/mycodo_wrapper upgrade```

Upgrading the mycodo database is performed automatically during the upgrade process, however it can also be performed manually with the following commands (Note: This does not create the database, only upgrade them. You must already have a database created in order to upgrade):

```cd ~/Mycodo/databases```

```alembic upgrade head```

Refer to the [alembic documentation](http://alembic.readthedocs.org/en/latest/tutorial.html) for other functions.



### Restoring Backups

A backup is made when the system is upgraded. If you need to restore a backup, do the following, changing the appropriate directory names:

```
sudo mv ~/Mycodo ~/Mycodo_old
sudo cp -a /var/Mycodo-backups/Mycodo-TIME-COMMIT ~/Mycodo
sudo service mycodo restart
sudo /etc/init.d/apache2 restart
```


### License

Mycodo is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mycodo is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](http://www.gnu.org/licenses/gpl-3.0.en.html) for more details.

A full copy of the GNU General Public License can be found at <a href="http://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank">http://www.gnu.org/licenses/gpl-3.0.en.html</a>

This software includes third party open source software components: Discrete PID Controller. Each of these software components have their own license. Please see ./3.5/cgi-bin/mycodoPID.py for license information.


### Screenshots (may be outdated)

Console output of the daemon running in debug mode (verbose output).

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/03/Mycodo-Console.png">

---

Status page displays all active sensors with a collapsible menu of activated PIDs and associated relays.

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Status-2016-04-10-10-53-58.png">

---

Custom graphs can be created with specific measurements and relays displayed (also duration, height, width).

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Graph-2016-04-14-18-29-24.png">

---

The sensor controller page lists activated and deactivated sensor controllers and their conditionals.

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Sensors-2016-04-10-10-52-36.png">

---

The relay page lists available relays and their conditionals.

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Relays-2016-04-10-10-52-57.png">

---

The PID page lists activated and deactivated PID controllers.

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-PID-2016-04-10-10-53-11.png">

---

Timers can be set to occur at a specific time of day or on a timed schedule.

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Timers-2016-04-14-18-33-24.png">

---

Log controllers enable polling of the influxdb at specific periods to create a log file.

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Logs-2016-04-15-10-45-09.png">

---

The LCD page lists activated and deactivated LCD controllers.

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-LCD-2016-04-10-10-53-38.png">

---

Settings pages to modify miscellaneous settings SQL databases

<img src="http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/04/Mycodo-Alerts-Settings-2016-04-10-11-50-29-e1460303466599.png">

## Links

Thanks for using and supporting Mycodo, however it may not be the latest version or it may have been altered if not obtained through an official distribution site. You should be able to find the latest version on github or my web site.

https://github.com/kizniche/Mycodo

http://KyleGabriel.com
