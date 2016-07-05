# Mycodo

## An Environmental Monitoring and Regulation System

### Latest version: 4.0.0

Mycodo is a remote monitoring and automation system with a focus on environmental regulation from sensor stimuli. Responses can be as simple as a trigger (camera capture, email notification, relay activation) or as complex as a PID controller to regulate conditions in an environment. Mycodo has been used for cultivating gourmet mushrooms, maintaining homeostatsis in a honey bee apiary, incubating eggs, aging cheeses, and more.

The system is built to run on the Raspberry Pi and aims to be easy to install and set up.

[![Mycodo](http://kylegabriel.com/projects/wp-content/uploads/sites/3/2016/05/Mycodo-3.6.0-tango-Graph-2016-05-21-11-15-26.png)](http://kylegabriel.com/projects/)


## Table of Contents

- [Features](#features)
- [TODO](#todo)
- [Supported Devices and Sensors](#supported-devices-and-sensors)
    - [Temperature](#temperature)
    - [Humidity](#humidity)
    - [CO<sub>2</sub>](#co2)
    - [Pressure](#pressure)
    - [Luminosity](#luminosity)
    - [Devices](#devices)
- [Notes](#notes)
- [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Enable I2C](#enable-i2c)
    - [Influxdb](#influxdb)
    - [Databases](#databases)
    - [HTTP Server](#http-server)
    - [Final Steps](#final-steps)
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
* Support for several digital sensors for measuring temperature, humidity, CO<sub>2</sub>, atmospheric pressure, luminocity, and infrared heat).
* Event triggers (relay, camera, email, etc.) when certain sensor measurements occur or conditions are met.
* Regulate environmental conditions with discrete PID control.
* Dynamic PID setpoints for changing environmental conditions throughout the day.
* 16x2 and 20x4 I<sup>2</sup>C LCD support.
* I<sup>2</sup>C multiplexer support to allow using multiple devices/sensors with the same address.
* Pi Camera support (still and video stream, timelapse coming soon).
* Automated system upgrade.


## TODO:

* Dashboard to monitor other Mycodo servers
* Add graph export options (width, height, scale)
* Add stepper motor support
* Create custom log from influxdb query
* Creat program/method (for reflow oven, gas chromatography, etc.)
* Wireless device support (z-wave)
* Notes, flag points of time on graph (text, file upload, graph saving, etc.).


## Supported Devices and Sensors

Certain sensors will require extra steps to be taken in order to set up the interface for communication. This includes I<sup>2</sup>C, one-wire, and UART.

### Temperature

> [DS18B20](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing) (1-wire)

The DS18B20 is a simple 1-wire sensor. Once the one-wire interface has been configured with the above instructions, it may be used with Mycodo.

> [TMP 006/007](https://www.sparkfun.com/products/11859) (I<sup>2</sup>C)

The TMP006 (and 007) can measure the temperature of an object without making contact with it, by using a thermopile to detect and absorb the infrared energy an object is emitting. This sensor also measures the temperature of the die (physical sensor).

### Humidity

> [DHT11, DHT22, AM2302](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/wiring) (GPIO)

> [AM2315](https://github.com/lexruee/tentacle_pi) (I<sup>2</sup>C)

> [SHT10, SHT11, SHT15, SHT71, SHT75](https://github.com/mk-fg/sht-sensor) (GPIO)

NOTE: The Raspberry Pi uses 3.3-volts for powering the SHT sensor, however the default driver (sht-sensor) does not handle measurement calculations from 3.3-volts, only 3.5-volts. This can be easy corrected by setting the correct coefficient in driver (a future revision will fix this).

### Carbon Dioxide (CO<sub>2</sub>)

> [K30](http://www.co2meters.com/Documentation/AppNotes/AN137-Raspberry-Pi.zip) (UART)

This documentation provides specific installation procedures for the K30 with the Raspberry Pi as well as example code. Once the K30 has been configured with this documentation, it can be tested whether the sensor is able to be read, by executing mycodo/tests/Test-Sensor-CO2-K30.py

UART is handled differently with the Raspberry Pi 3, because of bluetooth. Therefore, follow the instructions in the above link for Raspberry Pis 1 and 2, and the following instructions for the Raspberry pi 3:

Run raspi-config, go to Advanced Options->Serial and disable.

```sudo raspi-config```

edit /boot/config.txt and find the line "enable_uart=0" and change it to "enable_uart=1", then reboot.

### Pressure

> [BMP085/BMP180](https://learn.adafruit.com/using-the-bmp085-with-raspberry-pi) (I<sup>2</sup>C)

### Luminosity

> [TSL2561](https://www.sparkfun.com/products/12055) (I<sup>2</sup>C)

The TSL2561 SparkFun Luminosity Sensor Breakout is a sophisticated light sensor which has a flat response across most of the visible spectrum. Unlike simpler sensors, the TSL2561 measures both infrared and visible light to better approximate the response of the human eye. And because the TSL2561 is an integrating sensor (it soaks up light for a predetermined amount of time), it is capable of measuring both small and large amounts of light by changing the integration time.

The TSL2561 is capable of direct I2C communication and is able to conduct specific light ranges from 0.1 - 40k+ Lux easily. Additionally, the TSL12561 contains two integrating analog-to-digital converters (ADC) that integrate currents from two photodiodes, simultaneously.

### Edge Detection

The detection of a changing digital signal (for instance, HIGH to LOW) requires the use of edge detection. The rising edge (LOW to HIGH), the falling edge (HIGH to LOW), or both can be used to trigger events. The GPIO chosen to detect the signal should be equiped with an appropriate resistor that either pulls the GPIO up (connected to power) or down (connected to ground). The option to enable the internal pull-up or pull-down resistors is not available for safety reasons. Use your own resistor to pull the GPIO high or low.

Examples of devices that can be used with edge detection: simple switches and buttons, PIR motion sensors, reed switches, hall effect sensors, float switches, and more.

### Devices

> [TCA9548A I2C Multiplexer](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/overview) (I<sup>2</sup>C)

The TCA9548A I<sup>2</sup>C allows multiple sensors that have the same I<sup>2</sup>C address to be used with mycodo (such as the AM2315). The multiplexer has a selectable address, from 0x70 through 0x77, allowing up to 8 multiplexers to be used at once. With 8 channels per multiplexer, this allows up to 64 devices with the same address to be used.

> [MCP243x Analog to Digital Converter](http://www.dfrobot.com/wiki/index.php/MCP3424_18-Bit_ADC-4_Channel_with_Programmable_Gain_Amplifier_(SKU:DFR0316)) (I<sup>2</sup>C)

An analog to digital converter (ADC) allows the use of any analog sensor that outputs a variable voltage. The detectable voltage range of this ADC is &plusmn;2.048 volts. A [voltage divider](https://learn.sparkfun.com/tutorials/voltage-dividers) may be necessary to attain this range.


## Notes

A minimal set of anonymous usage statistics are collected to help improve development. No identifying information is saved from the information that is collected and it is only used to improve Mycodo. No other sources will have access to this information. The data collected is mainly how much specific features are used, how often errors occur, and other similar statistics. The data that's collected can be viewed from the 'View collected statistics' link in the Settings/General panel of the UI or in the file Mycodo/databases/statistics.csv. You may opt out from transmitting this information from the General settings in the Admin panel.

Mycodo/mycodo/scripts/mycodo_wrapper is a binary executable used to update the system from the web interface. It has the setuid bit to permit it to be executed as root ('sudo update_mycodo.sh initialize' sets the correct permissions and setuid). Since shell scripts cannot be setuid (ony binary files), the mycodo_wrapper binay permits these operations to be executed as root by a non-root user (in this case, members of the group 'mycodo'). You can audit the source code of Mycodo/mycodo/scripts/mycodo_wrapper.c and if you want to ensure the binary is indeed compiled from that source, you may compile it yourself with the following command. Otherwise, the compiled binary is already included and no further action is needed.

```sudo gcc ~/Mycodo/mycodo/scripts/mycodo_wrapper.c -o ~/Mycodo/mycodo/scripts/mycodo_wrapper```


## Installation

### Prerequisites

These install procedures have been tested to work with a Raspberry Pi following a fresh intall of [Raspbian Jessie](https://www.raspberrypi.org/downloads/raspbian/).

Set up the initial settings with raspi-config. **Don't skip the file system expansion and reboot! This needs to be done before continuing to install anything or there won't be any free disk space.**

```sudo raspi-config```

 + Change the default user (pi) password
 + Set the locale to en_US.UTF-8
 + Set the timezone (required for setting the proper time)
 + Enable I<sup>2</sup>C (required)
 + Enable Pi Camera support (optional)
 + Advanced A2: change the hostname (optional)
 + **Expand the file system (required)**
 + **Reboot**


```
sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt-get autoremove -y
sudo apt-get install -y git libffi-dev libi2c-dev python-dev python-setuptools python-smbus sqlite3 vim
sudo easy_install pip
```

```
wget abyz.co.uk/rpi/pigpio/pigpio.zip
unzip pigpio.zip
cd PIGPIO
make -j4
sudo make install
```

If you plan to use the DHT11, DHT22, or AM2302, you must add pigpiod to cron to start at boot. Edit the cron file with:

```sudo crontab -e```

Then add this line to the bottom of the file, then save and reboot:

```@reboot /usr/local/bin/pigpiod &```

```
cd
git clone git://git.drogon.net/wiringPi
cd wiringPi
./build
```

```
cd
git clone https://github.com/kizniche/Mycodo
cd Mycodo
sudo pip install -r requirements.txt --upgrade
sudo useradd -M mycodo
sudo adduser mycodo gpio
```


### Enable I2C

Enable I<sup>2</sup>C support through raspi-config (and other options if not already done)

Edit /etc/modules and add 'i2c-bcm2708' to the last line of the file

```sudo vim /etc/modules```

Edit /boot/config.txt

```sudo vim /boot/config.txt```

and add the following two lines to the end of the file

```
dtparam=i2c1=on
dtparam=i2c_arm=on
```

Reboot

```sudo shutdown now -r```


### Influxdb

```
wget https://dl.influxdata.com/influxdb/releases/influxdb_0.13.0_armhf.deb
sudo dpkg -i influxdb_0.13.0_armhf.deb
sudo service influxdb start
```

Set up the InfluxDB database and user from the influxdb console.

```
influx
CREATE DATABASE "mycodo_db"
CREATE USER "mycodo" WITH PASSWORD 'mmdu77sj3nIoiajjs'
exit
```


### Databases

Create all the required databases

```~/Mycodo/init_databases.py -i all```

Add an Administrator to the User database

```~/Mycodo/init_databases.py -A```


### HTTP Server

If you want write access to the mycodo files, add your user to the mycodo group, changing 'username' to your user.

```sudo usermod -a -G mycodo username```

The following steps will enable Flask application to run on Apache2 using mod_wsgi.

```
sudo apt-get install -y apache2 libapache2-mod-wsgi
sudo a2enmod wsgi ssl
sudo ln -s ~/Mycodo /var/www/mycodo
sudo cp ~/Mycodo/mycodo_flask_apache.conf /etc/apache2/sites-available/
sudo ln -sf /etc/apache2/sites-available/mycodo_flask_apache.conf /etc/apache2/sites-enabled/000-default.conf
mkdir ~/Mycodo/mycodo/frontend/ssl_certs
```

[letsencrypt.org](https://letsencrypt.org) provides free verified SSL certificates. However, if you don't want to bother, or don't have a domain, use the following commands to gener